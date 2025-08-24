#!/usr/bin/env python3
"""
MongoDB Schema Design for VStudio CLI CRM
Based on the requirements from REQUIREMENTS_FOR_THE_FUTURE.MD

This defines the MongoDB collections and document structures needed to transform
the CSV-based VoIP dialer into a minimalistic CRM system.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
import uuid

# Collection names
CONTACTS_COLLECTION = "contacts"
INTERACTIONS_COLLECTION = "interactions"
OUTCOMES_COLLECTION = "outcomes"
TASKS_COLLECTION = "tasks"
CALENDAR_MAP_COLLECTION = "calendar_map"
PRIORITY_RULES_COLLECTION = "priority_rules"
USER_PREFS_COLLECTION = "user_preferences"
AUDIT_COLLECTION = "audit_log"

class MongoDBSchema:
    """MongoDB schema manager for VStudio CLI CRM."""
    
    def __init__(self, db_name: str = "vstudio_crm"):
        self.db_name = db_name
        self.client = None
        self.db = None
        
    def get_contact_schema(self) -> Dict:
        """Contact document schema."""
        return {
            "_id": "ObjectId",  # MongoDB auto-generated
            "external_row_id": "str",  # For CSV compatibility
            "phone_number": "str",  # E.164 format
            "name": "str",
            "email": "str",
            "company": "str",
            "title": "str",
            "city": "str",
            "address": "str",  # Physical address
            "source": "str",
            "tags": ["str"],  # Array of tags for categorization
            "metadata": {
                "created_at": "datetime",
                "updated_at": "datetime",
                "created_by": "str",  # user identifier
                "last_contact_at": "datetime",
                "contact_attempts": "int",
                "data_quality_score": "float"  # 0-1 based on completeness
            },
            "status": "str",  # active, archived, do_not_call
            "priority_score": "float",  # Calculated priority
            "custom_fields": {}  # Flexible storage for additional data
        }
    
    def get_interaction_schema(self) -> Dict:
        """Interaction document schema."""
        return {
            "_id": "ObjectId",
            "contact_id": "ObjectId",  # Reference to contact
            "type": "str",  # call, text, note, email
            "timestamp": "datetime",
            "duration": "int",  # seconds (for calls)
            "direction": "str",  # outbound, inbound
            "body": "str",  # message content or notes
            "external_id": "str",  # VoIP system call/SMS ID
            "metadata": {
                "from_number": "str",
                "to_number": "str",
                "voip_call_id": "str",
                "sms_status": "str",
                "call_status": "str",
                "recording_url": "str"
            }
        }
    
    def get_outcome_schema(self) -> Dict:
        """Outcome document schema."""
        return {
            "_id": "ObjectId",
            "interaction_id": "ObjectId",  # Reference to interaction
            "contact_id": "ObjectId",  # Reference to contact (for easy queries)
            "category": "str",  # bad_number, no_answer, callback, meeting_booked, do_not_call
            "notes": "str",
            "created_at": "datetime",
            "created_by": "str",
            "confidence": "float",  # AI-assisted outcome confidence (0-1)
            "auto_generated": "bool"  # Whether outcome was auto-detected
        }
    
    def get_task_schema(self) -> Dict:
        """Task document schema (callbacks, meetings, follow-ups)."""
        return {
            "_id": "ObjectId",
            "contact_id": "ObjectId",  # Reference to contact
            "type": "str",  # callback, meeting, follow_up, reminder
            "due_at": "datetime",  # When task is due
            "start_time": "datetime",  # For meetings
            "end_time": "datetime",  # For meetings
            "state": "str",  # pending, completed, cancelled, overdue
            "priority": "str",  # high, medium, low
            "title": "str",
            "description": "str",
            "external_refs": {
                "calendar_event_id": "str",
                "calendar_provider": "str"  # google, outlook, etc
            },
            "created_at": "datetime",
            "updated_at": "datetime",
            "completed_at": "datetime"
        }
    
    def get_calendar_map_schema(self) -> Dict:
        """Calendar mapping document schema."""
        return {
            "_id": "ObjectId",
            "contact_id": "ObjectId",
            "task_id": "ObjectId",
            "provider": "str",  # google, outlook
            "external_event_id": "str",
            "event_type": "str",  # callback, meeting
            "sync_status": "str",  # synced, pending, failed
            "last_sync_at": "datetime"
        }
    
    def get_priority_rule_schema(self) -> Dict:
        """Priority scoring rules schema."""
        return {
            "_id": "ObjectId",
            "rule_id": "str",  # unique rule identifier
            "name": "str",
            "description": "str",
            "weight": "float",  # Rule weight in scoring
            "enabled": "bool",
            "rule_type": "str",  # time_based, interaction_based, data_quality
            "parameters": {},  # Rule-specific parameters
            "last_updated": "datetime",
            "created_by": "str"
        }
    
    def get_user_preferences_schema(self) -> Dict:
        """User preferences document schema."""
        return {
            "_id": "ObjectId",
            "user_id": "str",  # User identifier
            "display_options": {
                "records_per_page": "int",
                "default_view": "str",  # today, due, overdue, hot, new
                "show_archived": "bool",
                "theme": "str"
            },
            "default_durations": {
                "callback_minutes": "int",
                "meeting_minutes": "int"
            },
            "reminder_preferences": {
                "callback_reminders": ["int"],  # minutes before
                "meeting_reminders": ["int"]
            },
            "priority_weights": {
                "urgency_weight": "float",
                "recency_weight": "float", 
                "quality_weight": "float"
            },
            "integrations": {
                "calendar_provider": "str",
                "voip_provider": "str",
                "timezone": "str"
            },
            "last_updated": "datetime"
        }
    
    def get_audit_schema(self) -> Dict:
        """Audit log document schema."""
        return {
            "_id": "ObjectId",
            "entity_type": "str",  # contact, interaction, task, etc.
            "entity_id": "ObjectId",  # ID of the entity
            "action": "str",  # create, update, delete, archive
            "timestamp": "datetime",
            "user_id": "str",
            "changes": {},  # Before/after values
            "metadata": {
                "ip_address": "str",
                "user_agent": "str",
                "session_id": "str"
            }
        }

class CRMDatabase:
    """MongoDB CRM database manager."""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "vstudio_crm"):
        self.connection_string = connection_string
        self.db_name = db_name
        self.client = None
        self.db = None
        
    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    def create_indexes(self):
        """Create database indexes for optimal performance."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        # Contacts indexes
        contacts = self.db[CONTACTS_COLLECTION]
        contacts.create_index("phone_number", unique=True)
        contacts.create_index("external_row_id", unique=True, sparse=True)
        contacts.create_index("email", sparse=True)
        contacts.create_index([("name", ASCENDING), ("company", ASCENDING)])
        contacts.create_index("status")
        contacts.create_index([("priority_score", DESCENDING)])
        contacts.create_index("metadata.last_contact_at")
        contacts.create_index("tags")
        
        # Interactions indexes
        interactions = self.db[INTERACTIONS_COLLECTION]
        interactions.create_index("contact_id")
        interactions.create_index([("contact_id", ASCENDING), ("timestamp", DESCENDING)])
        interactions.create_index("type")
        interactions.create_index("timestamp")
        interactions.create_index("external_id", sparse=True)
        
        # Outcomes indexes
        outcomes = self.db[OUTCOMES_COLLECTION]
        outcomes.create_index("interaction_id")
        outcomes.create_index("contact_id")
        outcomes.create_index("category")
        outcomes.create_index("created_at")
        
        # Tasks indexes
        tasks = self.db[TASKS_COLLECTION]
        tasks.create_index("contact_id")
        tasks.create_index("due_at")
        tasks.create_index([("state", ASCENDING), ("due_at", ASCENDING)])
        tasks.create_index("type")
        tasks.create_index("priority")
        
        # Calendar mapping indexes
        calendar_map = self.db[CALENDAR_MAP_COLLECTION]
        calendar_map.create_index([("contact_id", ASCENDING), ("provider", ASCENDING)])
        calendar_map.create_index("external_event_id", unique=True, sparse=True)
        calendar_map.create_index("sync_status")
        
        # Priority rules indexes
        priority_rules = self.db[PRIORITY_RULES_COLLECTION]
        priority_rules.create_index("rule_id", unique=True)
        priority_rules.create_index("enabled")
        
        # User preferences indexes
        user_prefs = self.db[USER_PREFS_COLLECTION]
        user_prefs.create_index("user_id", unique=True)
        
        # Audit log indexes
        audit = self.db[AUDIT_COLLECTION]
        audit.create_index([("entity_type", ASCENDING), ("entity_id", ASCENDING)])
        audit.create_index("timestamp")
        audit.create_index("user_id")
        
        print("Database indexes created successfully")
    
    def migrate_from_csv(self, csv_data: List[Dict]) -> Dict[str, int]:
        """Migrate existing CSV data to MongoDB."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        contacts_coll = self.db[CONTACTS_COLLECTION]
        interactions_coll = self.db[INTERACTIONS_COLLECTION]
        outcomes_coll = self.db[OUTCOMES_COLLECTION]
        tasks_coll = self.db[TASKS_COLLECTION]
        
        migrated_counts = {
            "contacts": 0,
            "interactions": 0,
            "tasks": 0,
            "skipped": 0
        }
        
        for csv_row in csv_data:
            try:
                # Create contact document
                contact_doc = {
                    "external_row_id": csv_row.get("external_row_id"),
                    "phone_number": csv_row.get("phone_number", "").strip(),
                    "name": csv_row.get("name", "").strip(),
                    "email": csv_row.get("email", "").strip(),
                    "company": csv_row.get("company", "").strip(),
                    "title": csv_row.get("title", "").strip(),
                    "city": csv_row.get("city", "").strip(),
                    "address": csv_row.get("address", "").strip(),
                    "source": csv_row.get("source", "").strip(),
                    "tags": [],
                    "metadata": {
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "created_by": "csv_migration",
                        "contact_attempts": 0,
                        "data_quality_score": self._calculate_data_quality(csv_row)
                    },
                    "status": csv_row.get("status", "new"),
                    "priority_score": 0.0,
                    "custom_fields": {}
                }
                
                # Skip if phone number is empty
                if not contact_doc["phone_number"]:
                    migrated_counts["skipped"] += 1
                    continue
                
                # Insert or update contact
                result = contacts_coll.replace_one(
                    {"phone_number": contact_doc["phone_number"]},
                    contact_doc,
                    upsert=True
                )
                
                contact_id = result.upserted_id or contacts_coll.find_one(
                    {"phone_number": contact_doc["phone_number"]}
                )["_id"]
                
                migrated_counts["contacts"] += 1
                
                # Create interaction records from CSV notes/history
                if csv_row.get("notes"):
                    self._migrate_notes_to_interactions(
                        contact_id, csv_row["notes"], interactions_coll
                    )
                    migrated_counts["interactions"] += 1
                
                # Create tasks from callback/meeting data
                task_count = self._migrate_tasks_from_csv(
                    contact_id, csv_row, tasks_coll
                )
                migrated_counts["tasks"] += task_count
                
            except Exception as e:
                print(f"Error migrating row {csv_row}: {e}")
                migrated_counts["skipped"] += 1
                continue
        
        return migrated_counts
    
    def _calculate_data_quality(self, csv_row: Dict) -> float:
        """Calculate data quality score based on field completeness."""
        fields = ["name", "email", "company", "title", "city", "phone_number"]
        filled_fields = sum(1 for field in fields if csv_row.get(field, "").strip())
        return filled_fields / len(fields)
    
    def _migrate_notes_to_interactions(self, contact_id, notes: str, interactions_coll: Collection):
        """Convert CSV notes to interaction documents."""
        if not notes:
            return
        
        # Parse timestamped notes (format: [YYYY-MM-DD HH:MM] note text)
        note_parts = [part.strip() for part in notes.split(';') if part.strip()]
        
        for note in note_parts:
            if note.startswith('[') and ']' in note:
                try:
                    end_bracket = note.index(']')
                    timestamp_str = note[1:end_bracket]
                    content = note[end_bracket + 1:].strip()
                    
                    # Try to parse timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        timestamp = datetime.utcnow()
                    
                    interaction_doc = {
                        "contact_id": contact_id,
                        "type": "note",
                        "timestamp": timestamp,
                        "duration": 0,
                        "direction": "outbound",
                        "body": content,
                        "external_id": None,
                        "metadata": {
                            "migrated_from_csv": True
                        }
                    }
                    
                    interactions_coll.insert_one(interaction_doc)
                    
                except (ValueError, IndexError):
                    # Fallback: create note without parsed timestamp
                    interaction_doc = {
                        "contact_id": contact_id,
                        "type": "note",
                        "timestamp": datetime.utcnow(),
                        "duration": 0,
                        "direction": "outbound",
                        "body": note,
                        "external_id": None,
                        "metadata": {
                            "migrated_from_csv": True
                        }
                    }
                    interactions_coll.insert_one(interaction_doc)
    
    def _migrate_tasks_from_csv(self, contact_id, csv_row: Dict, tasks_coll: Collection) -> int:
        """Create task documents from CSV callback/meeting data."""
        task_count = 0
        
        # Callback task
        if csv_row.get("callback_on"):
            try:
                due_date = datetime.fromisoformat(csv_row["callback_on"])
                task_doc = {
                    "contact_id": contact_id,
                    "type": "callback",
                    "due_at": due_date,
                    "state": "pending",
                    "priority": "medium",
                    "title": "Callback scheduled",
                    "description": "Migrated from CSV",
                    "external_refs": {
                        "calendar_event_id": csv_row.get("gcal_callback_event_id", ""),
                        "calendar_provider": "google" if csv_row.get("gcal_callback_event_id") else ""
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                tasks_coll.insert_one(task_doc)
                task_count += 1
            except (ValueError, TypeError):
                pass
        
        # Meeting task
        if csv_row.get("meeting_at"):
            try:
                meeting_time = datetime.fromisoformat(csv_row["meeting_at"])
                task_doc = {
                    "contact_id": contact_id,
                    "type": "meeting",
                    "due_at": meeting_time,
                    "start_time": meeting_time,
                    "end_time": meeting_time + timedelta(hours=1),
                    "state": "pending",
                    "priority": "high",
                    "title": "Meeting scheduled",
                    "description": "Migrated from CSV",
                    "external_refs": {
                        "calendar_event_id": csv_row.get("gcal_meeting_event_id", ""),
                        "calendar_provider": "google" if csv_row.get("gcal_meeting_event_id") else ""
                    },
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                tasks_coll.insert_one(task_doc)
                task_count += 1
            except (ValueError, TypeError):
                pass
        
        return task_count
    
    def setup_default_priority_rules(self):
        """Set up default priority scoring rules."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        
        priority_rules = self.db[PRIORITY_RULES_COLLECTION]
        
        default_rules = [
            {
                "rule_id": "due_date_urgency",
                "name": "Due Date Urgency",
                "description": "Higher priority for overdue and soon-due tasks",
                "weight": 0.4,
                "enabled": True,
                "rule_type": "time_based",
                "parameters": {
                    "overdue_multiplier": 2.0,
                    "today_multiplier": 1.5,
                    "this_week_multiplier": 1.2
                },
                "last_updated": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "rule_id": "interaction_recency",
                "name": "Recent Interaction",
                "description": "Higher priority for recently contacted leads",
                "weight": 0.3,
                "enabled": True,
                "rule_type": "interaction_based",
                "parameters": {
                    "decay_days": 7,
                    "max_boost": 1.0
                },
                "last_updated": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "rule_id": "data_quality",
                "name": "Data Completeness",
                "description": "Prioritize contacts with complete information",
                "weight": 0.2,
                "enabled": True,
                "rule_type": "data_quality",
                "parameters": {
                    "min_score_threshold": 0.5
                },
                "last_updated": datetime.utcnow(),
                "created_by": "system"
            },
            {
                "rule_id": "manual_pins",
                "name": "Manual Pins",
                "description": "User-pinned contacts get highest priority",
                "weight": 0.1,
                "enabled": True,
                "rule_type": "manual",
                "parameters": {
                    "pin_boost": 3.0
                },
                "last_updated": datetime.utcnow(),
                "created_by": "system"
            }
        ]
        
        for rule in default_rules:
            priority_rules.replace_one(
                {"rule_id": rule["rule_id"]},
                rule,
                upsert=True
            )
        
        print("Default priority rules created")

if __name__ == "__main__":
    # Example usage
    schema = MongoDBSchema()
    print("Contact Schema:", schema.get_contact_schema())
    
    # Test database connection
    db = CRMDatabase()
    if db.connect():
        print("Connected to MongoDB successfully")
        db.create_indexes()
        db.setup_default_priority_rules()
        db.disconnect()
    else:
        print("Failed to connect to MongoDB")