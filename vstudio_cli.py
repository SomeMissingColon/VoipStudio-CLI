#!/usr/bin/env python3
"""
VStudio CLI - A keyboard-first CLI/TUI for VoIPstudio call management.

A simple Python script that walks callers through CSV lists, places and monitors 
calls via VoIPstudio's REST API, captures outcomes, schedules callbacks/meetings 
to Google Calendar, and persists everything back to CSV with backups.
"""

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import signal
from dotenv import load_dotenv

# Third-party imports (to be installed)
try:
    import requests
    import keyring
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
    import dateparser
    import phonenumbers
    from phonenumbers import NumberParseException
    
    # Google Calendar imports
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install requests keyring rich dateparser phonenumbers google-auth google-auth-oauthlib google-api-python-client python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration constants
API_BASE_URL = "https://l7api.com/v1.2/voipstudio"
KEYRING_SERVICE = "vstudio-cli"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
BACKUP_DIR = "backups"
ARCHIVE_FILE = "archive.csv"

# Google Calendar configuration
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CREDENTIALS_FILE = "credentials.json"
GOOGLE_TOKEN_FILE = "token.json"

# Status constants
STATUS_NEW = "new"
STATUS_BAD_NUMBER = "bad_number"
STATUS_NO_ANSWER = "no_answer"
STATUS_CALLBACK = "callback"
STATUS_MEETING_BOOKED = "meeting_booked"
STATUS_DO_NOT_CALL = "do_not_call"
STATUS_DELETED = "deleted"

TERMINAL_STATUSES = {STATUS_DELETED, STATUS_DO_NOT_CALL, STATUS_BAD_NUMBER}


class OperationQueue:
    """Queue manager for offline/failed operations."""
    
    def __init__(self, queue_file: str = "operation_queue.json"):
        self.queue_file = Path(queue_file)
        self.operations = []
        self.logger = logging.getLogger(__name__)
        self._load_queue()
    
    def _load_queue(self):
        """Load queued operations from disk."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    self.operations = json.load(f)
                self.logger.info(f"Loaded {len(self.operations)} queued operations")
            except Exception as e:
                self.logger.error(f"Failed to load operation queue: {e}")
                self.operations = []
    
    def _save_queue(self):
        """Save queued operations to disk."""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(self.operations, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save operation queue: {e}")
    
    def add_calendar_operation(self, operation_type: str, record_id: str, **kwargs):
        """Add a calendar operation to the queue."""
        operation = {
            'type': 'calendar',
            'operation': operation_type,  # 'create_callback', 'create_meeting', 'cancel'
            'record_id': record_id,
            'timestamp': datetime.now().isoformat(),
            'attempts': 0,
            'max_attempts': 3,
            'data': kwargs
        }
        self.operations.append(operation)
        self._save_queue()
        self.logger.info(f"Queued calendar operation: {operation_type} for {record_id}")
    
    def process_queue(self, calendar_client, data_records: List[Dict]) -> int:
        """Process all queued operations. Returns number of successful operations."""
        if not self.operations:
            return 0
        
        successful_ops = 0
        failed_ops = []
        
        # Create lookup for records by external_row_id
        record_lookup = {record.get('external_row_id'): record for record in data_records}
        
        for operation in self.operations:
            try:
                operation['attempts'] += 1
                success = False
                
                if operation['type'] == 'calendar' and calendar_client:
                    success = self._process_calendar_operation(operation, calendar_client, record_lookup)
                
                if success:
                    successful_ops += 1
                    self.logger.info(f"Successfully processed queued operation: {operation['operation']}")
                else:
                    if operation['attempts'] >= operation['max_attempts']:
                        self.logger.error(f"Operation failed after {operation['attempts']} attempts: {operation}")
                    else:
                        failed_ops.append(operation)
                        
            except Exception as e:
                self.logger.error(f"Error processing queued operation: {e}")
                if operation['attempts'] < operation['max_attempts']:
                    failed_ops.append(operation)
        
        # Update queue with failed operations only
        self.operations = failed_ops
        self._save_queue()
        
        return successful_ops
    
    def _process_calendar_operation(self, operation: Dict, calendar_client, record_lookup: Dict) -> bool:
        """Process a single calendar operation."""
        record_id = operation['record_id']
        record = record_lookup.get(record_id)
        
        if not record:
            self.logger.warning(f"Record not found for queued operation: {record_id}")
            return True  # Remove from queue - record no longer exists
        
        op_type = operation['operation']
        data = operation['data']
        
        try:
            if op_type == 'create_callback':
                callback_date = datetime.fromisoformat(data['callback_date'])
                event_id = calendar_client.create_callback_event(record, callback_date, data.get('notes', ''))
                if event_id:
                    record['gcal_callback_event_id'] = event_id
                    return True
                    
            elif op_type == 'create_meeting':
                meeting_datetime = datetime.fromisoformat(data['meeting_datetime'])
                event_id = calendar_client.create_meeting_event(record, meeting_datetime, data.get('notes', ''))
                if event_id:
                    record['gcal_meeting_event_id'] = event_id
                    return True
                    
            elif op_type == 'cancel':
                event_id = data.get('event_id')
                if event_id and calendar_client.cancel_event(event_id):
                    # Clear the event ID from record
                    if data.get('event_type') == 'callback':
                        record['gcal_callback_event_id'] = ""
                    elif data.get('event_type') == 'meeting':
                        record['gcal_meeting_event_id'] = ""
                    return True
                    
        except Exception as e:
            self.logger.error(f"Calendar operation failed: {e}")
            
        return False
    
    def get_queue_status(self) -> Dict:
        """Get current queue status."""
        return {
            'total_operations': len(self.operations),
            'by_type': {},
            'failed_operations': [op for op in self.operations if op['attempts'] >= op['max_attempts']]
        }
    
    def clear_failed_operations(self):
        """Clear all permanently failed operations."""
        self.operations = [op for op in self.operations if op['attempts'] < op['max_attempts']]
        self._save_queue()


class GoogleCalendarClient:
    """Google Calendar API client for creating and managing events."""
    
    def __init__(self, credentials_file: str = GOOGLE_CREDENTIALS_FILE, token_file: str = GOOGLE_TOKEN_FILE):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = logging.getLogger(__name__)
        self.calendar_id = 'primary'  # Use primary calendar by default
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API using OAuth2."""
        creds = None
        
        # Load existing token
        if Path(self.token_file).exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, GOOGLE_SCOPES)
            except Exception as e:
                self.logger.warning(f"Failed to load existing token: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                if not Path(self.credentials_file).exists():
                    self.logger.error(f"Google credentials file not found: {self.credentials_file}")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, GOOGLE_SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    self.logger.error(f"OAuth flow failed: {e}")
                    return False
            
            # Save credentials for future use
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                self.logger.warning(f"Failed to save token: {e}")
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            self.logger.error(f"Failed to build Calendar service: {e}")
            return False
    
    def create_callback_event(self, contact: Dict, callback_date: datetime, notes: str = "") -> Optional[str]:
        """Create a callback event in Google Calendar."""
        if not self.service:
            return None
        
        # Default callback time (10 AM)
        event_datetime = callback_date.replace(hour=10, minute=0, second=0, microsecond=0)
        end_datetime = event_datetime + timedelta(minutes=30)  # 30-minute duration
        
        # Build event description
        description_parts = [
            f"Callback for: {contact.get('name', 'Unknown')}",
            f"Company: {contact.get('company', 'N/A')}",
            f"Phone: {contact.get('phone_number', 'N/A')}",
            f"Email: {contact.get('email', 'N/A')}",
        ]
        
        if notes:
            description_parts.append(f"Notes: {notes}")
        
        description_parts.append(f"CSV ID: {contact.get('external_row_id', 'N/A')}")
        
        event = {
            'summary': f"Callback: {contact.get('name', contact.get('phone_number', 'Unknown'))}",
            'description': '\n'.join(description_parts),
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': 'America/New_York',  # TODO: Make configurable
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                    {'method': 'popup', 'minutes': 5},
                ],
            },
        }
        
        # Add attendee if email exists
        email = contact.get('email', '').strip()
        if email and '@' in email:
            event['attendees'] = [{'email': email}]
        
        try:
            result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return result.get('id')
        except HttpError as e:
            self.logger.error(f"Failed to create callback event: {e}")
            return None
    
    def create_meeting_event(self, contact: Dict, meeting_datetime: datetime, notes: str = "") -> Optional[str]:
        """Create a meeting event in Google Calendar."""
        if not self.service:
            return None
        
        end_datetime = meeting_datetime + timedelta(hours=1)  # 1-hour duration
        
        # Build event description
        description_parts = [
            f"Meeting with: {contact.get('name', 'Unknown')}",
            f"Company: {contact.get('company', 'N/A')}",
            f"Phone: {contact.get('phone_number', 'N/A')}",
            f"Email: {contact.get('email', 'N/A')}",
        ]
        
        if notes:
            description_parts.append(f"Notes: {notes}")
        
        description_parts.append(f"CSV ID: {contact.get('external_row_id', 'N/A')}")
        
        event = {
            'summary': f"Meeting: {contact.get('name', contact.get('phone_number', 'Unknown'))}",
            'description': '\n'.join(description_parts),
            'start': {
                'dateTime': meeting_datetime.isoformat(),
                'timeZone': 'America/New_York',  # TODO: Make configurable
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/New_York',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        # Add attendee if email exists
        email = contact.get('email', '').strip()
        if email and '@' in email:
            event['attendees'] = [{'email': email}]
        
        try:
            result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return result.get('id')
        except HttpError as e:
            self.logger.error(f"Failed to create meeting event: {e}")
            return None
    
    def cancel_event(self, event_id: str) -> bool:
        """Cancel (delete) a calendar event."""
        if not self.service or not event_id:
            return False
        
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            return True
        except HttpError as e:
            self.logger.error(f"Failed to cancel event {event_id}: {e}")
            return False
    
    def update_event(self, event_id: str, **kwargs) -> bool:
        """Update an existing calendar event."""
        if not self.service or not event_id:
            return False
        
        try:
            # Get existing event
            event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            
            # Update fields
            for key, value in kwargs.items():
                event[key] = value
            
            # Update event
            self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=event).execute()
            return True
        except HttpError as e:
            self.logger.error(f"Failed to update event {event_id}: {e}")
            return False

class VoIPStudioAPI:
    """VoIPstudio REST API client."""
    
    def __init__(self, api_token: str, base_url: str = API_BASE_URL):
        self.api_token = api_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-Auth-Token": api_token,
            "Content-Type": "application/json",
            "User-Agent": "vstudio-cli/1.0"
        })
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an authenticated API request with error handling."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            self.logger.debug(f"{method} {url} -> {response.status_code}")
            return response
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout: {method} {url}")
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error: {method} {url}")
            raise
        except Exception as e:
            self.logger.error(f"Request error: {method} {url} - {e}")
            raise
    
    def validate_auth(self) -> bool:
        """Test API authentication."""
        try:
            response = self._make_request("GET", "/ping")
            return response.status_code == 200
        except Exception:
            return False
    
    @classmethod
    def login_with_credentials(cls, email: str, password: str) -> Optional[str]:
        """Login with email/password to get user token."""
        try:
            login_url = "https://l7api.com/v1.2/voipstudio/login"
            response = requests.post(
                login_url,
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('user_token')
            else:
                return None
        except Exception:
            return None
    
    def create_call(self, to_number: str, from_user: str = None, caller_id: str = None) -> Optional[Dict]:
        """Initiate an outbound call."""
        payload = {"to": to_number}
        if from_user:
            payload["from"] = from_user
        if caller_id:
            payload["caller_id"] = caller_id
        
        self.logger.debug(f"Creating call with payload: {payload}")
        response = self._make_request("POST", "/calls", json=payload)
        self.logger.debug(f"Create call response: {response.status_code} - {response.text if response else 'No response'}")
        
        if response.status_code == 201:
            result = response.json()
            self.logger.debug(f"Call created successfully: {result}")
            return result
        else:
            self.logger.error(f"Failed to create call: {response.status_code} - {response.text}")
            return None
    
    def get_call(self, call_id: str) -> Optional[Dict]:
        """Get call details by ID."""
        response = self._make_request("GET", f"/calls/{call_id}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None  # Call not found (probably ended)
        else:
            self.logger.error(f"Failed to get call {call_id}: {response.status_code}")
            return None
    
    def get_active_calls(self) -> List[Dict]:
        """Get all active calls."""
        response = self._make_request("GET", "/calls")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', []) if isinstance(data, dict) else data
        else:
            self.logger.error(f"Failed to get active calls: {response.status_code}")
            return []
    
    def terminate_call(self, call_id: str) -> bool:
        """Terminate an active call."""
        response = self._make_request("DELETE", f"/calls/{call_id}")
        
        if response.status_code == 204:
            return True
        else:
            self.logger.error(f"Failed to terminate call {call_id}: {response.status_code}")
            return False
    
    def update_call(self, call_id: str, **kwargs) -> Optional[Dict]:
        """Update call (transfer, etc.)."""
        response = self._make_request("PATCH", f"/calls/{call_id}", json=kwargs)
        
        if response.status_code in [200, 301]:
            return response.json()
        else:
            self.logger.error(f"Failed to update call {call_id}: {response.status_code}")
            return None
    
    def send_sms(self, to_number: str, message: str, from_number: str = None) -> Optional[Dict]:
        """Send an SMS message."""
        payload = {
            "to": to_number,
            "message": message
        }
        if from_number:
            payload["from"] = from_number
        
        self.logger.debug(f"Sending SMS with payload: {payload}")
        response = self._make_request("POST", "/sms", json=payload)
        self.logger.debug(f"SMS response: {response.status_code} - {response.text if response else 'No response'}")
        
        if response.status_code == 201:
            result = response.json()
            self.logger.debug(f"SMS sent successfully: {result}")
            return result
        else:
            self.logger.error(f"Failed to send SMS: {response.status_code} - {response.text}")
            return None
    
    def get_sms_list(self) -> List[Dict]:
        """Get list of SMS messages."""
        response = self._make_request("GET", "/sms")
        
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get SMS list: {response.status_code} - {response.text}")
            return []
    
    def get_ddis(self) -> List[Dict]:
        """Get list of DDI (Direct Dial-In) numbers for the account."""
        response = self._make_request("GET", "/ddis")
        
        if response.status_code == 200:
            result = response.json()
            self.logger.debug(f"DDIs retrieved: {result}")
            return result.get('data', []) if isinstance(result, dict) else result
        else:
            self.logger.error(f"Failed to get DDIs: {response.status_code} - {response.text}")
            return []
    
    def get_sms_capable_numbers(self) -> List[str]:
        """Get list of phone numbers capable of sending SMS."""
        ddis = self.get_ddis()
        sms_numbers = []
        
        for ddi in ddis:
            # Check if this DDI supports SMS
            if isinstance(ddi, dict):
                number = ddi.get('e164') or ddi.get('number')
                sms_enabled = ddi.get('sms', {}).get('enabled', False) if isinstance(ddi.get('sms'), dict) else ddi.get('sms_enabled', True)
                
                if number and sms_enabled:
                    # Remove + if present for API consistency
                    clean_number = number.lstrip('+') if number.startswith('+') else number
                    sms_numbers.append(clean_number)
        
        self.logger.debug(f"SMS capable numbers: {sms_numbers}")
        return sms_numbers


class VStudioCLI:
    """Main application class for VStudio CLI."""
    
    def __init__(self, debug=False):
        self.console = Console()
        self.csv_path = None
        self.data = []
        self.current_index = 0
        self.running = True
        self.api_client = None
        self.calendar_client = None
        self.current_call_id = None
        self.operation_queue = OperationQueue()
        self.debug = debug
        
        # Setup logging
        log_level = logging.DEBUG if debug else logging.INFO
        
        # Create file handler for logs.txt
        file_handler = logging.FileHandler('logs.txt', mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # Setup root logger
        logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
        self.logger = logging.getLogger(__name__)
        
        if debug:
            self.logger.info("Debug mode enabled - all debug info will be logged to logs.txt")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled."""
        # Always log to file
        self.logger.debug(f"DEBUG: {message}")
        
        # Print to console only if debug mode is enabled
        if self.debug:
            self.console.print(f"[cyan][DEBUG] {message}[/cyan]")
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown on signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.current_call_id and self.api_client:
            self.api_client.terminate_call(self.current_call_id)
    
    def run(self, csv_path: Optional[str] = None):
        """Main entry point for the application."""
        try:
            self._initialize(csv_path)
            self._main_loop()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.console.print(f"[red]Error: {e}[/red]")
        finally:
            self._cleanup()
    
    def _initialize(self, csv_path: Optional[str] = None):
        """Initialize the application."""
        if self.debug:
            self.console.print("[cyan]🐛 Debug mode enabled[/cyan]")
        
        # Get CSV path
        if not csv_path:
            csv_path = Prompt.ask("Enter CSV file path")
        
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Load and validate CSV
        self._load_csv()
        
        # Setup authentication
        self._setup_auth()
        
        # Setup Google Calendar (optional)
        self._setup_calendar()
        
        # Process any queued operations
        self._process_queued_operations()
        
        # Create necessary directories
        Path(BACKUP_DIR).mkdir(exist_ok=True)
    
    def _load_csv(self):
        """Load and validate the CSV file."""
        self.logger.info(f"Loading CSV: {self.csv_path}")
        
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.headers = list(reader.fieldnames) if reader.fieldnames else []
                self.data = list(reader)
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {e}")
        
        if not self.headers:
            raise ValueError("CSV file appears to be empty or has no headers")
        
        # Validate required columns
        if 'phone_number' not in self.headers:
            raise ValueError("CSV must contain a 'phone_number' column")
        
        # Add managed columns if missing
        managed_columns = [
            'status', 'last_call_at', 'callback_on', 'meeting_at', 'notes',
            'gcal_callback_event_id', 'gcal_meeting_event_id', 'gcal_calendar_id',
            'external_row_id', 'last_sms_at', 'sms_history'
        ]
        
        for col in managed_columns:
            if col not in self.headers:
                self.headers.append(col)
                for row in self.data:
                    row[col] = ""
        
        # Validate and normalize data
        valid_rows = []
        issues = []
        
        for i, row in enumerate(self.data):
            # Generate external_row_id for new rows
            if not row.get('external_row_id'):
                content_hash = hash(f"{row.get('phone_number', '')}{row.get('name', '')}{row.get('company', '')}")
                row['external_row_id'] = f"{self.csv_path.stem}_{i}_{abs(content_hash)}"
            
            # Set default status
            if not row.get('status'):
                row['status'] = STATUS_NEW
            
            # Validate phone_number number
            phone_number = row.get('phone_number', '').strip()
            if not phone_number:
                issues.append(f"Row {i+1}: Missing phone_number number")
                continue
            
            # Try to normalize phone number
            normalized = self._normalize_phone_number(phone_number)
            if normalized:
                row['phone_number'] = normalized
            else:
                issues.append(f"Row {i+1}: Invalid phone number format: {phone_number}")
                # Keep the row but mark for manual review
                row['status'] = 'invalid_phone'
            
            valid_rows.append(row)
        
        self.data = valid_rows
        
        # Report issues but don't fail completely
        if issues:
            self.console.print(f"[yellow]Found {len(issues)} data issues:[/yellow]")
            for issue in issues[:10]:  # Show first 10 issues
                self.console.print(f"  - {issue}")
            if len(issues) > 10:
                self.console.print(f"  ... and {len(issues) - 10} more")
        
        self.console.print(f"[green]Loaded {len(self.data)} records[/green]")
    
    def _setup_auth(self):
        """Setup VoIPstudio API authentication."""
        # Try to get stored token
        api_token = None
        try:
            api_token = keyring.get_password(KEYRING_SERVICE, "api_token")
        except Exception:
            pass
        
        if not api_token:
            # Offer login options
            auth_method = Prompt.ask(
                "Authentication method",
                choices=["token", "login"],
                default="login"
            )
            
            if auth_method == "login":
                email = Prompt.ask("Email")
                password = Prompt.ask("Password", password=True)
                
                self.console.print("[yellow]Logging in...[/yellow]")
                api_token = VoIPStudioAPI.login_with_credentials(email, password)
                
                if not api_token:
                    self.console.print("[red]Login failed. Please check credentials.[/red]")
                    raise ValueError("Login failed")
                
                self.console.print("[green]✓ Login successful[/green]")
                
                if Confirm.ask("Save token securely?"):
                    try:
                        keyring.set_password(KEYRING_SERVICE, "api_token", api_token)
                    except Exception as e:
                        self.logger.warning(f"Failed to save token: {e}")
            else:
                api_token = Prompt.ask("Enter VoIPstudio API token", password=True)
                if Confirm.ask("Save token securely?"):
                    try:
                        keyring.set_password(KEYRING_SERVICE, "api_token", api_token)
                    except Exception as e:
                        self.logger.warning(f"Failed to save token: {e}")
        
        # Create API client
        self._debug_print(f"Creating API client with token: {api_token[:10] if api_token else 'None'}...")
        self.api_client = VoIPStudioAPI(api_token)
        
        # Validate token
        self._debug_print("Validating API authentication")
        if not self.api_client.validate_auth():
            # Clear stored token if validation fails
            try:
                keyring.delete_password(KEYRING_SERVICE, "api_token")
            except Exception:
                pass
            self._debug_print("API authentication failed")
            raise ValueError("Invalid API token")
        else:
            self._debug_print("API authentication successful")
    
    def _setup_calendar(self):
        """Setup Google Calendar integration (optional)."""
        # Check if user wants calendar integration
        if not Path(GOOGLE_CREDENTIALS_FILE).exists():
            self.console.print(f"[yellow]Google Calendar credentials not found ({GOOGLE_CREDENTIALS_FILE})[/yellow]")
            self.console.print("[dim]Calendar integration will be disabled. To enable:[/dim]")
            self.console.print("[dim]1. Create a Google Cloud Project[/dim]")
            self.console.print("[dim]2. Enable Calendar API[/dim]")
            self.console.print("[dim]3. Create OAuth 2.0 credentials[/dim]")
            self.console.print(f"[dim]4. Download credentials as {GOOGLE_CREDENTIALS_FILE}[/dim]")
            return
        
        try:
            self.calendar_client = GoogleCalendarClient()
            if self.calendar_client.authenticate():
                self.console.print("[green]✓ Google Calendar connected[/green]")
            else:
                self.console.print("[yellow]⚠ Google Calendar authentication failed[/yellow]")
                self.calendar_client = None
        except Exception as e:
            self.logger.error(f"Calendar setup failed: {e}")
            self.console.print(f"[yellow]⚠ Google Calendar setup failed: {e}[/yellow]")
            self.calendar_client = None
    
    def _process_queued_operations(self):
        """Process any queued operations from previous sessions."""
        if not self.operation_queue.operations:
            return
        
        self.console.print(f"[yellow]Processing {len(self.operation_queue.operations)} queued operations...[/yellow]")
        
        try:
            successful_ops = self.operation_queue.process_queue(self.calendar_client, self.data)
            
            if successful_ops > 0:
                self.console.print(f"[green]✓ Successfully processed {successful_ops} queued operations[/green]")
                # Save CSV if any records were updated
                self._save_csv()
            
            remaining_ops = len(self.operation_queue.operations)
            if remaining_ops > 0:
                self.console.print(f"[yellow]⚠ {remaining_ops} operations remain queued[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Failed to process queued operations: {e}")
            self.console.print(f"[red]Failed to process queued operations: {e}[/red]")
    
    def _main_loop(self):
        """Main application loop."""
        while self.running and self.data:
            # Skip terminal statuses
            while (self.current_index < len(self.data) and 
                   self.data[self.current_index].get('status') in TERMINAL_STATUSES):
                self.current_index += 1
            
            if self.current_index >= len(self.data):
                self.console.print("[yellow]No more records to process[/yellow]")
                break
            
            self._display_record()
            action = self._get_user_input()
            self._handle_action(action)
    
    def _display_record(self):
        """Display the current record in a readable format."""
        if not self.data or self.current_index >= len(self.data):
            self.console.print("[yellow]No more records to display[/yellow]")
            return
        
        record = self.data[self.current_index]
        
        # Clear screen and show header
        self.console.clear()
        
        # Header with navigation info and status
        total_active = len([r for r in self.data if r.get('status') not in TERMINAL_STATUSES])
        current_active = len([r for r in self.data[:self.current_index] 
                             if r.get('status') not in TERMINAL_STATUSES]) + 1
        
        status = record.get('status', STATUS_NEW)
        status_color = self._get_status_color(status)
        
        header_parts = [
            f"Record {current_active}/{total_active}",
            f"[{status_color}]{status.replace('_', ' ').title()}[/{status_color}]"
        ]
        
        # Add timing information
        if record.get('last_call_at'):
            try:
                last_call = datetime.fromisoformat(record['last_call_at'].replace('Z', '+00:00'))
                header_parts.append(f"Last Call: {last_call.strftime('%Y-%m-%d %H:%M')}")
            except:
                header_parts.append(f"Last Call: {record['last_call_at']}")
        
        if record.get('callback_on'):
            header_parts.append(f"[yellow]Callback: {record['callback_on']}[/yellow]")
        
        if record.get('meeting_at'):
            try:
                meeting = datetime.fromisoformat(record['meeting_at'].replace('Z', '+00:00'))
                header_parts.append(f"[green]Meeting: {meeting.strftime('%Y-%m-%d %H:%M')}[/green]")
            except:
                header_parts.append(f"Meeting: {record['meeting_at']}")
        
        header_text = " | ".join(header_parts)
        self.console.print(Panel(header_text, style="bold blue"))
        
        # Record details table
        table = Table(show_header=False, box=None, padding=(0, 2), show_lines=False)
        table.add_column("Field", style="bold cyan", min_width=12)
        table.add_column("Value", style="white")
        
        # Show key fields with better formatting
        key_fields = [
            ('Name', 'name'),
            ('Company', 'company'), 
            ('phone_number', 'phone_number'),
            ('Email', 'email'),
            ('Title', 'title'),
            ('City', 'city'),
            ('Source', 'source')
        ]
        
        for display_name, field_name in key_fields:
            value = record.get(field_name, '').strip()
            if value:
                # Special formatting for phone_number
                if field_name == 'phone_number':
                    table.add_row(display_name, f"[bold green]{value}[/bold green]")
                elif field_name == 'email':
                    table.add_row(display_name, f"[blue]{value}[/blue]")
                else:
                    table.add_row(display_name, value)
        
        # Show notes with proper wrapping
        notes = record.get('notes', '').strip()
        if notes:
            # Parse timestamped notes
            formatted_notes = self._format_notes(notes)
            table.add_row("Notes", formatted_notes)
        
        self.console.print(table)
        
        # Show any additional fields not covered above
        other_fields = []
        standard_fields = {'name', 'company', 'phone_number', 'email', 'title', 'city', 'source', 
                          'notes', 'status', 'last_call_at', 'callback_on', 'meeting_at',
                          'gcal_callback_event_id', 'gcal_meeting_event_id', 'gcal_calendar_id',
                          'external_row_id'}
        
        for field, value in record.items():
            if field not in standard_fields and value and value.strip():
                other_fields.append(f"{field}: {value}")
        
        if other_fields:
            self.console.print(f"\n[dim]Additional: {' | '.join(other_fields[:3])}[/dim]")
            if len(other_fields) > 3:
                self.console.print(f"[dim]... and {len(other_fields) - 3} more fields[/dim]")
        
        # Footer with hotkeys
        footer = self._get_hotkey_footer()
        self.console.print(Panel(footer, style="dim", title="[bold]Commands[/bold]"))
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status display."""
        status_colors = {
            STATUS_NEW: "white",
            STATUS_NO_ANSWER: "yellow", 
            STATUS_CALLBACK: "blue",
            STATUS_MEETING_BOOKED: "green",
            STATUS_BAD_NUMBER: "red",
            STATUS_DO_NOT_CALL: "red",
            STATUS_DELETED: "dim red",
            'invalid_phone': "magenta"
        }
        return status_colors.get(status, "white")
    
    def _format_notes(self, notes: str) -> str:
        """Format timestamped notes for display."""
        if not notes:
            return ""
        
        # Split by semicolon (our separator) and format each note
        note_parts = [part.strip() for part in notes.split(';')]
        formatted_parts = []
        
        for part in note_parts:
            if part.startswith('[') and ']' in part:
                # Timestamped note
                try:
                    end_bracket = part.index(']')
                    timestamp = part[1:end_bracket]
                    content = part[end_bracket + 1:].strip()
                    formatted_parts.append(f"[dim]{timestamp}[/dim] {content}")
                except:
                    formatted_parts.append(part)
            else:
                formatted_parts.append(part)
        
        # Join with newlines for better readability
        result = '\n'.join(formatted_parts)
        
        # Truncate if too long
        if len(result) > 200:
            result = result[:197] + "..."
        
        return result
    
    def _get_hotkey_footer(self) -> str:
        """Get the hotkey footer text."""
        return """[bold cyan]1[/bold cyan] Call  [bold cyan]2[/bold cyan] Text  [bold cyan]3[/bold cyan] Next  [bold cyan]4[/bold cyan] Delete  [bold cyan]5[/bold cyan] Add Note
[bold cyan]↑/k[/bold cyan] Prev  [bold cyan]↓/j[/bold cyan] Next  [bold cyan]/[/bold cyan] Search  [bold cyan]o[/bold cyan] Outcome  [bold cyan]q[/bold cyan] Quit"""
    
    def _get_user_input(self) -> str:
        """Get user input for action selection."""
        try:
            # Use Rich's input with prompt styling
            user_input = self.console.input("\n[bold cyan]Action[/bold cyan] → ").strip().lower()
            return user_input
        except (EOFError, KeyboardInterrupt):
            return 'q'
    
    def _handle_action(self, action: str):
        """Handle user action."""
        if action == 'q':
            self.running = False
        elif action == '1':
            self._make_call()
        elif action == '2':
            self._send_text()
        elif action == '3' or action == 'j' or action == '':
            self._next_record()
        elif action == '4':
            self._delete_record()
        elif action == '5':
            self._add_note()
        elif action == 'k':
            self._prev_record()
        elif action == '/':
            self._search()
        elif action == 'o':
            self._handle_call_outcome('manual')
        else:
            self.console.print("[yellow]Unknown command[/yellow]")
    
    def _make_call(self):
        """Initiate a call to the current record."""
        self._debug_print("Starting _make_call method")
        
        if self.current_index >= len(self.data):
            self._debug_print("No data or invalid current_index")
            return
        
        record = self.data[self.current_index]
        phone_number = record.get('phone_number')
        self._debug_print(f"Current record: {record}")
        self._debug_print(f"Phone number from record: {phone_number}")
        
        if not phone_number:
            self.console.print("[red]No phone_number number found[/red]")
            return
        
        # Format phone number for VoIP Studio API (E.164 without plus)
        api_number = self._format_phone_for_voipstudio(phone_number)
        normalized_display = self._normalize_phone_number(phone_number)  # For display with +
        self._debug_print(f"Original number: {phone_number}")
        self._debug_print(f"API format number: {api_number}")
        self._debug_print(f"Display format number: {normalized_display}")
        
        if not api_number:
            self.console.print(f"[red]Invalid phone number format: {phone_number}[/red]")
            return
        
        self.console.print(f"[yellow]Calling {normalized_display or api_number}...[/yellow]")
        self._debug_print(f"API client status: {self.api_client is not None}")
        
        try:
            # Make API call to initiate call
            self._debug_print("Sending API request to create call")
            call_data = self.api_client.create_call(api_number)
            self._debug_print(f"API response: {call_data}")
            
            if call_data:
                # Extract call ID from nested data structure
                if 'data' in call_data and 'id' in call_data['data']:
                    self.current_call_id = str(call_data['data']['id'])
                else:
                    self.current_call_id = call_data.get('id')
                self._debug_print(f"Call ID set to: {self.current_call_id}")
                self.console.print(f"[green]Call initiated (ID: {self.current_call_id})[/green]")
                self._monitor_call()
            else:
                self.console.print("[red]Failed to initiate call[/red]")
                self._debug_print("API returned None or empty response")
                
        except Exception as e:
            self.console.print(f"[red]Error making call: {e}[/red]")
            self.logger.error(f"Call error: {e}")
            self._debug_print(f"Exception details: {type(e).__name__}: {e}")
            import traceback
            self._debug_print(f"Traceback: {traceback.format_exc()}")
    
    def _normalize_phone_number(self, phone: str, default_region: str = "US") -> Optional[str]:
        """Normalize phone number to E.164 format using phonenumbers library."""
        if not phone:
            return None
        
        try:
            # Parse the phone number
            parsed = phonenumbers.parse(phone, default_region)
            
            # Validate the number
            if phonenumbers.is_valid_number(parsed):
                # Format as E.164
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                self.logger.warning(f"Invalid phone number: {phone}")
                return None
                
        except NumberParseException as e:
            self.logger.error(f"Failed to parse phone number '{phone}': {e}")
            return None
    
    def _format_phone_for_voipstudio(self, phone: str) -> Optional[str]:
        """Format phone number for VoIP Studio API (E.164 without plus sign)."""
        normalized = self._normalize_phone_number(phone)
        if normalized and normalized.startswith('+'):
            return normalized[1:]  # Remove the plus sign
        return normalized
    
    def _monitor_call(self):
        """Monitor the active call and handle outcomes."""
        self._debug_print("Starting call monitoring")
        if not self.current_call_id:
            self._debug_print("No current call ID, exiting monitor")
            return
        
        import time
        from rich.live import Live
        from rich.table import Table
        from rich.text import Text
        
        start_time = time.time()
        poll_count = 0
        last_status = None
        max_poll_attempts = 30  # Maximum polling attempts before forcing outcome menu
        
        def create_call_display():
            """Create the call monitoring display."""
            table = Table(show_header=False, box=None, padding=(1, 2))
            table.add_column("", style="bold cyan", min_width=15)
            table.add_column("", style="white")
            
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            
            table.add_row("Call ID", str(self.current_call_id))
            table.add_row("Status", f"[{self._get_status_color(last_status or 'dialing')}]{last_status or 'dialing'}[/]")
            table.add_row("Duration", f"{minutes:02d}:{seconds:02d}")
            table.add_row("", "[dim]Press Ctrl+C to end call or Space to show outcome menu[/dim]")
            
            return Panel(table, title="[bold yellow]📞 Call Monitor[/bold yellow]", style="yellow")
        
        call_ended = False
        final_status = None
        
        try:
            with Live(create_call_display(), refresh_per_second=1) as live:
                while self.current_call_id and self.running and not call_ended:
                    try:
                        self._debug_print(f"Polling call status for ID: {self.current_call_id} (attempt {poll_count})")
                        call_data = self.api_client.get_call(self.current_call_id)
                        self._debug_print(f"Call data received: {call_data}")
                        
                        if call_data:
                            # Extract status from call data
                            status = self._extract_call_status(call_data)
                            self._debug_print(f"Extracted status: {status}")
                            
                            if status != last_status:
                                last_status = status
                                self._debug_print(f"Status changed to: {status}")
                                live.update(create_call_display())
                            
                            # Check if call ended
                            if self._is_call_ended(status, call_data):
                                self._debug_print(f"Call ended with status: {status}")
                                call_ended = True
                                final_status = status
                                live.update(create_call_display())
                                time.sleep(2)  # Show final status briefly
                                break
                                
                        elif poll_count > 10:  # Call not found after many attempts
                            self._debug_print("Call not found after many attempts, assuming completed")
                            last_status = "completed"
                            call_ended = True
                            final_status = "completed"
                            live.update(create_call_display())
                            time.sleep(1)
                            break
                        
                        # Force outcome menu after max attempts
                        if poll_count >= max_poll_attempts:
                            self._debug_print("Max poll attempts reached, forcing outcome menu")
                            call_ended = True
                            final_status = last_status or "unknown"
                            break
                        
                        poll_count += 1
                        live.update(create_call_display())
                        time.sleep(2)  # Poll every 2 seconds
                        
                    except Exception as e:
                        self.logger.error(f"Call monitoring error: {e}")
                        self._debug_print(f"Exception in call monitoring: {e}")
                        last_status = "error"
                        live.update(create_call_display())
                        time.sleep(3)  # Wait on error but don't wait too long
                        
        except KeyboardInterrupt:
            # User wants to end call manually
            self.console.print("\n[yellow]Terminating call...[/yellow]")
            if self.api_client.terminate_call(self.current_call_id):
                self.console.print("[yellow]Call terminated by user[/yellow]")
            else:
                self.console.print("[red]Failed to terminate call[/red]")
            call_ended = True
            final_status = 'terminated'
        
        # Always show outcome menu after call monitoring ends
        self.current_call_id = None
        self._debug_print(f"Call monitoring ended, showing outcome menu with status: {final_status}")
        self._handle_call_outcome(final_status)
    
    def _extract_call_status(self, call_data: Dict) -> str:
        """Extract call status from API response."""
        # This depends on the actual VoIPstudio API response format
        # Common fields to check: status, state, call_state, etc.
        for field in ['status', 'state', 'call_state', 'call_status']:
            if field in call_data:
                return str(call_data[field]).lower()
        
        # Fallback based on other indicators
        if call_data.get('end_time') or call_data.get('ended_at'):
            return 'completed'
        elif call_data.get('start_time') or call_data.get('started_at'):
            return 'connected'
        else:
            return 'dialing'
    
    def _is_call_ended(self, status: str, call_data: Dict) -> bool:
        """Determine if call has ended based on status and data."""
        ended_statuses = [
            'completed', 'failed', 'no-answer', 'busy', 'cancelled',
            'terminated', 'hangup', 'ended', 'finished'
        ]
        
        if status in ended_statuses:
            return True
        
        # Check for end time indicators
        if call_data.get('end_time') or call_data.get('ended_at'):
            return True
        
        return False
    
    def _handle_call_outcome(self, call_status: str = None):
        """Handle post-call outcome selection."""
        self.console.print("\n")  # Add some space
        
        # Create outcome selection panel
        outcome_table = Table(show_header=False, box=None, padding=(0, 2))
        outcome_table.add_column("Key", style="bold cyan", min_width=3)
        outcome_table.add_column("Outcome", style="white")
        outcome_table.add_column("Description", style="dim")
        
        outcome_table.add_row("1", "Bad number", "Archives record, cancels events")
        outcome_table.add_row("2", "No answer", "Keeps record active, adds note")
        outcome_table.add_row("3", "Call back", "Schedules callback, creates calendar event")
        outcome_table.add_row("4", "Meeting booked", "Schedules meeting, creates calendar event")
        outcome_table.add_row("5", "Do not call", "Archives record, cancels events")
        outcome_table.add_row("", "[dim]Enter[/dim]", "[dim]Default: No answer[/dim]")
        
        self.console.print(Panel(outcome_table, title="[bold yellow]Call Outcome[/bold yellow]"))
        
        # Get user choice with better prompt
        choice = Prompt.ask(
            "Select outcome",
            choices=["1", "2", "3", "4", "5", ""],
            default="2",
            show_choices=False
        )
        
        # Handle the selected outcome
        outcome_handlers = {
            '1': self._outcome_bad_number,
            '2': self._outcome_no_answer,
            '3': self._outcome_callback,
            '4': self._outcome_meeting,
            '5': self._outcome_do_not_call,
            '': self._outcome_no_answer  # Default
        }
        
        handler = outcome_handlers.get(choice, self._outcome_no_answer)
        handler()
        
        # Show confirmation of action taken
        self.console.print(f"[green]✓ Outcome recorded: {self._get_outcome_description(choice)}[/green]")
    
    def _get_outcome_description(self, choice: str) -> str:
        """Get human-readable description of outcome."""
        descriptions = {
            '1': "Bad number",
            '2': "No answer", 
            '3': "Call back scheduled",
            '4': "Meeting booked",
            '5': "Do not call",
            '': "No answer"
        }
        return descriptions.get(choice, "Unknown")
    
    def _outcome_bad_number(self):
        """Handle bad number outcome."""
        record = self.data[self.current_index]
        
        # Cancel any existing calendar events
        self._cancel_calendar_events(record)
        
        record['status'] = STATUS_BAD_NUMBER
        record['last_call_at'] = datetime.now().isoformat()
        self._archive_record()
        self._save_csv()
        self._next_record()
    
    def _outcome_no_answer(self):
        """Handle no answer outcome."""
        record = self.data[self.current_index]
        record['status'] = STATUS_NO_ANSWER
        record['last_call_at'] = datetime.now().isoformat()
        
        # Add note in the format: YYYY-MM-DD ~ no answer
        today = datetime.now().strftime("%Y-%m-%d")
        note_text = f"{today} ~ no answer"
        self._add_timestamped_note(note_text)
        self._save_csv()
    
    def _outcome_callback(self):
        """Handle callback outcome."""
        record = self.data[self.current_index]
        
        # Get number of days for callback
        days_input = Prompt.ask(
            "Callback in how many days?",
            default="1",
            show_default=True
        )
        
        try:
            days = int(days_input)
            if days < 0:
                self.console.print("[red]Number of days must be positive[/red]")
                return
        except ValueError:
            self.console.print("[red]Please enter a valid number of days[/red]")
            return
        
        # Calculate callback date (today + N days)
        today = datetime.now().date()
        callback_date = today + timedelta(days=days)
        
        # Show calculated date for confirmation
        formatted_date = callback_date.strftime('%A, %B %d, %Y')
        if not Confirm.ask(f"Schedule callback for {formatted_date}?"):
            return
        
        record['status'] = STATUS_CALLBACK
        record['callback_on'] = callback_date.isoformat()
        record['last_call_at'] = datetime.now().isoformat()
        
        # Create Google Calendar event
        event_id = None
        if self.calendar_client:
            try:
                # Convert date to datetime for calendar event
                callback_datetime = datetime.combine(callback_date, datetime.min.time().replace(hour=10))
                notes = record.get('notes', '')
                event_id = self.calendar_client.create_callback_event(record, callback_datetime, notes)
                if event_id:
                    record['gcal_callback_event_id'] = event_id
                    self.console.print("[green]✓ Calendar event created[/green]")
                else:
                    # Queue the operation for retry
                    self.operation_queue.add_calendar_operation(
                        'create_callback',
                        record.get('external_row_id'),
                        callback_date=callback_datetime.isoformat(),
                        notes=notes
                    )
                    self.console.print("[yellow]⚠ Calendar event queued for retry[/yellow]")
            except Exception as e:
                self.logger.error(f"Calendar event creation failed: {e}")
                # Queue the operation for retry
                self.operation_queue.add_calendar_operation(
                    'create_callback',
                    record.get('external_row_id'),
                    callback_date=callback_datetime.isoformat(),
                    notes=record.get('notes', '')
                )
                self.console.print(f"[yellow]⚠ Calendar event queued due to error: {e}[/yellow]")
        
        # Add note about callback scheduling
        note_text = f"callback scheduled for {callback_date.isoformat()}"
        self._add_timestamped_note(note_text)
        self._save_csv()
        
        self.console.print(f"[blue]📅 Callback scheduled for {formatted_date}[/blue]")
    
    def _outcome_meeting(self):
        """Handle meeting booked outcome."""
        record = self.data[self.current_index]
        
        # Get meeting datetime with examples
        datetime_input = Prompt.ask(
            "Meeting date/time",
            default="tomorrow 2pm",
            show_default=True
        )
        
        meeting_datetime = dateparser.parse(datetime_input, settings={'PREFER_DATES_FROM': 'future'})
        
        if not meeting_datetime:
            self.console.print("[red]Invalid date/time format. Try: 'tomorrow 2pm', 'next Friday 10am', '2024-01-15 14:00'[/red]")
            return
        
        # Show parsed datetime for confirmation
        formatted_datetime = meeting_datetime.strftime('%A, %B %d, %Y at %I:%M %p')
        if not Confirm.ask(f"Schedule meeting for {formatted_datetime}?"):
            return
        
        record['status'] = STATUS_MEETING_BOOKED
        record['meeting_at'] = meeting_datetime.isoformat()
        record['last_call_at'] = datetime.now().isoformat()
        
        # Create Google Calendar event
        event_id = None
        if self.calendar_client:
            try:
                notes = record.get('notes', '')
                event_id = self.calendar_client.create_meeting_event(record, meeting_datetime, notes)
                if event_id:
                    record['gcal_meeting_event_id'] = event_id
                    self.console.print("[green]✓ Calendar event created[/green]")
                else:
                    # Queue the operation for retry
                    self.operation_queue.add_calendar_operation(
                        'create_meeting',
                        record.get('external_row_id'),
                        meeting_datetime=meeting_datetime.isoformat(),
                        notes=notes
                    )
                    self.console.print("[yellow]⚠ Calendar event queued for retry[/yellow]")
            except Exception as e:
                self.logger.error(f"Calendar event creation failed: {e}")
                # Queue the operation for retry
                self.operation_queue.add_calendar_operation(
                    'create_meeting',
                    record.get('external_row_id'),
                    meeting_datetime=meeting_datetime.isoformat(),
                    notes=record.get('notes', '')
                )
                self.console.print(f"[yellow]⚠ Calendar event queued due to error: {e}[/yellow]")
        
        # Add note in the format: meeting booked on YYYY-MM-DD HH:mm
        note_datetime = meeting_datetime.strftime("%Y-%m-%d %H:%M")
        note_text = f"meeting booked on {note_datetime}"
        self._add_timestamped_note(note_text)
        self._save_csv()
        
        self.console.print(f"[green]📅 Meeting scheduled for {formatted_datetime}[/green]")
    
    def _outcome_do_not_call(self):
        """Handle do not call outcome."""
        record = self.data[self.current_index]
        
        # Cancel any existing calendar events
        self._cancel_calendar_events(record)
        
        record['status'] = STATUS_DO_NOT_CALL
        record['last_call_at'] = datetime.now().isoformat()
        self._archive_record()
        self._save_csv()
        self._next_record()
    
    def _cancel_calendar_events(self, record: Dict):
        """Cancel any existing calendar events for a record."""
        if not self.calendar_client:
            return
        
        # Cancel callback event
        callback_event_id = record.get('gcal_callback_event_id')
        if callback_event_id:
            try:
                if self.calendar_client.cancel_event(callback_event_id):
                    self.console.print("[dim]✓ Callback event cancelled[/dim]")
                    record['gcal_callback_event_id'] = ""
                else:
                    self.console.print("[dim]⚠ Failed to cancel callback event[/dim]")
            except Exception as e:
                self.logger.error(f"Failed to cancel callback event: {e}")
        
        # Cancel meeting event
        meeting_event_id = record.get('gcal_meeting_event_id')
        if meeting_event_id:
            try:
                if self.calendar_client.cancel_event(meeting_event_id):
                    self.console.print("[dim]✓ Meeting event cancelled[/dim]")
                    record['gcal_meeting_event_id'] = ""
                else:
                    self.console.print("[dim]⚠ Failed to cancel meeting event[/dim]")
            except Exception as e:
                self.logger.error(f"Failed to cancel meeting event: {e}")
    
    def _send_text(self):
        """Send SMS to the current record."""
        self._debug_print("Starting _send_text method")
        
        if self.current_index >= len(self.data):
            self._debug_print("No data or invalid current_index")
            return
        
        record = self.data[self.current_index]
        phone_number = record.get('phone_number')
        self._debug_print(f"Current record: {record}")
        self._debug_print(f"Phone number from record: {phone_number}")
        
        if not phone_number:
            self.console.print("[red]No phone number found[/red]")
            return
        
        # Format phone number for VoIP Studio API (E.164 without plus)
        api_number = self._format_phone_for_voipstudio(phone_number)
        normalized_display = self._normalize_phone_number(phone_number)  # For display with +
        self._debug_print(f"Original number: {phone_number}")
        self._debug_print(f"API format number: {api_number}")
        self._debug_print(f"Display format number: {normalized_display}")
        
        if not api_number:
            self.console.print(f"[red]Invalid phone number format: {phone_number}[/red]")
            return
        
        # Get message from user
        message = Prompt.ask("Enter SMS message")
        self._debug_print(f"Raw message input: {repr(message)} (type: {type(message)})")
        
        # Handle case where message might be a list or other type
        if isinstance(message, list):
            message = ' '.join(str(item) for item in message)
        elif not isinstance(message, str):
            message = str(message)
        
        if not message.strip():
            self.console.print("[yellow]No message entered[/yellow]")
            return
        
        self.console.print(f"[yellow]Sending SMS to {normalized_display or api_number}...[/yellow]")
        self._debug_print(f"SMS message: {message}")
        self._debug_print(f"API client status: {self.api_client is not None}")
        
        try:
            # Get available SMS-capable numbers
            self._debug_print("Getting SMS-capable numbers for 'from' field")
            from_numbers = self.api_client.get_sms_capable_numbers()
            self._debug_print(f"Available from numbers: {from_numbers}")
            
            if not from_numbers:
                self.console.print("[red]No SMS-capable phone numbers found on your account[/red]")
                self._debug_print("No SMS-capable numbers available")
                return
            
            # Use the first available number as default, or let user choose if multiple
            if len(from_numbers) == 1:
                from_number = from_numbers[0]
                self._debug_print(f"Using only available from number: {from_number}")
            else:
                # Show available numbers with + for user-friendly display
                display_numbers = [f"+{num}" if not num.startswith('+') else num for num in from_numbers]
                self.console.print(f"[cyan]Available numbers: {', '.join(display_numbers)}[/cyan]")
                
                # Use first as default for now (could add user selection later)
                from_number = from_numbers[0]
                self._debug_print(f"Using first available from number: {from_number} (out of {len(from_numbers)} available)")
            
            # Send SMS via API
            self._debug_print("Sending API request to send SMS")
            sms_result = self.api_client.send_sms(api_number, message, from_number)
            self._debug_print(f"SMS API response: {sms_result}")
            
            if sms_result:
                self.console.print(f"[green]✓ SMS sent successfully[/green]")
                
                # Update record with SMS activity
                now = datetime.now()
                record['last_sms_at'] = now.isoformat()
                
                # Store SMS history as a semicolon-separated string like notes
                sms_entry = f"[{now.strftime('%Y-%m-%d %H:%M')}] SMS sent: {message[:50]}{'...' if len(message) > 50 else ''}"
                existing_history = record.get('sms_history', '')
                if existing_history:
                    record['sms_history'] = f"{existing_history}; {sms_entry}"
                else:
                    record['sms_history'] = sms_entry
                
                self._save_csv()
                
            else:
                self.console.print("[red]Failed to send SMS[/red]")
                self._debug_print("SMS API returned None or empty response")
                
        except Exception as e:
            self.console.print(f"[red]Error sending SMS: {e}[/red]")
            self.logger.error(f"SMS error: {e}")
            self._debug_print(f"Exception details: {type(e).__name__}: {e}")
            import traceback
            self._debug_print(f"Traceback: {traceback.format_exc()}")
    
    def _next_record(self):
        """Move to next record."""
        self.current_index += 1
    
    def _prev_record(self):
        """Move to previous record."""
        if self.current_index > 0:
            self.current_index -= 1
    
    def _delete_record(self):
        """Delete (archive) current record."""
        if Confirm.ask("Delete this record?"):
            record = self.data[self.current_index]
            record['status'] = STATUS_DELETED
            self._archive_record()
            self._save_csv()
            self._next_record()
    
    def _add_note(self):
        """Add a timestamped note to current record."""
        note = Prompt.ask("Enter note")
        if note:
            self._add_timestamped_note(note)
            self._save_csv()
    
    def _add_timestamped_note(self, note: str):
        """Add a timestamped note to the current record."""
        record = self.data[self.current_index]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"
        
        existing_notes = record.get('notes', '')
        if existing_notes:
            record['notes'] = f"{existing_notes}; {new_note}"
        else:
            record['notes'] = new_note
    
    def _search(self):
        """Search through records with enhanced functionality."""
        query = Prompt.ask("Search (name, company, phone, email, status, notes)")
        if not query:
            return
        
        query_lower = query.lower()
        matches = []
        
        # Find all matching records
        for i, record in enumerate(self.data):
            # Skip archived records unless specifically searching for them
            if record.get('status') in TERMINAL_STATUSES and 'archive' not in query_lower:
                continue
            
            # Search in key fields
            search_fields = ['phone_number', 'name', 'company', 'email', 'status', 'notes', 'title', 'city', 'source']
            match_found = False
            matched_fields = []
            
            for field in search_fields:
                field_value = str(record.get(field, '')).lower()
                if query_lower in field_value:
                    match_found = True
                    matched_fields.append(field)
            
            if match_found:
                matches.append((i, record, matched_fields))
        
        if not matches:
            self.console.print("[yellow]No matches found[/yellow]")
            return
        
        if len(matches) == 1:
            # Single match - jump directly
            self.current_index = matches[0][0]
            matched_fields = ', '.join(matches[0][2])
            self.console.print(f"[green]Found match in: {matched_fields}[/green]")
        else:
            # Multiple matches - show selection
            self._show_search_results(matches, query)
    
    def _show_search_results(self, matches: List, query: str):
        """Display search results for user selection."""
        self.console.print(f"\n[bold]Found {len(matches)} matches for '{query}':[/bold]\n")
        
        # Create results table
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("#", style="cyan", width=3)
        table.add_column("Name", style="white", min_width=15)
        table.add_column("Company", style="dim", min_width=15)
        table.add_column("Phone", style="green", min_width=12)
        table.add_column("Status", style="yellow", min_width=10)
        table.add_column("Fields", style="dim", min_width=10)
        
        for idx, (record_idx, record, matched_fields) in enumerate(matches[:20], 1):  # Show max 20 results
            status_color = self._get_status_color(record.get('status', ''))
            table.add_row(
                str(idx),
                record.get('name', '')[:20],
                record.get('company', '')[:20],
                record.get('phone_number', '')[:15],
                f"[{status_color}]{record.get('status', '')}[/{status_color}]",
                ', '.join(matched_fields)
            )
        
        if len(matches) > 20:
            table.add_row("...", f"{len(matches) - 20} more results", "", "", "", "")
        
        self.console.print(table)
        
        # Get user selection
        try:
            choice = Prompt.ask(
                f"Select result (1-{min(len(matches), 20)}) or Enter to cancel",
                default="",
                show_default=False
            )
            
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < min(len(matches), 20):
                    self.current_index = matches[idx][0]
                    self.console.print(f"[green]Jumped to match {choice}[/green]")
                else:
                    self.console.print("[red]Invalid selection[/red]")
            
        except (ValueError, KeyboardInterrupt):
            self.console.print("[yellow]Search cancelled[/yellow]")
    
    def _archive_record(self):
        """Archive the current record."""
        record = self.data[self.current_index].copy()
        record['archived_at'] = datetime.now().isoformat()
        
        # Append to archive file
        archive_path = Path(ARCHIVE_FILE)
        file_exists = archive_path.exists()
        
        with open(archive_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers + ['archived_at'])
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)
    
    def _save_csv(self):
        """Save the CSV with backup."""
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(BACKUP_DIR) / f"{self.csv_path.stem}_{timestamp}.csv"
        
        if self.csv_path.exists():
            import shutil
            shutil.copy2(self.csv_path, backup_path)
        
        # Write to temporary file then replace
        temp_path = self.csv_path.with_suffix('.tmp')
        
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(self.data)
        
        # Atomic replace
        temp_path.replace(self.csv_path)
        self.logger.info(f"CSV saved with backup: {backup_path}")
    
    def _terminate_current_call(self):
        """Terminate the current active call."""
        if self.current_call_id and self.api_client:
            if self.api_client.terminate_call(self.current_call_id):
                self.console.print("[yellow]Call terminated[/yellow]")
            else:
                self.console.print("[red]Failed to terminate call[/red]")
            self.current_call_id = None
    
    def _cleanup(self):
        """Cleanup on exit."""
        if self.current_call_id and self.api_client:
            self.api_client.terminate_call(self.current_call_id)
        self.console.print("[green]Goodbye![/green]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="VStudio CLI - VoIP Call Management")
    parser.add_argument("csv_file", nargs="?", help="Path to CSV file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode with detailed call information")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    app = VStudioCLI(debug=args.debug)
    app.run(args.csv_file)


if __name__ == "__main__":
    main()