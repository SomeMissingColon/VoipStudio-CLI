#!/usr/bin/env python3
"""
Database layer for VStudio CLI CRM
Provides unified interface for CSV compatibility and MongoDB operations
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None

from mongodb_schema import CRMDatabase, CONTACTS_COLLECTION, INTERACTIONS_COLLECTION, TASKS_COLLECTION


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    use_mongodb: bool = False
    mongodb_uri: str = "mongodb://localhost:27017/"
    database_name: str = "vstudio_crm"
    csv_backup_enabled: bool = True
    csv_export_path: str = "data_export.csv"
    auto_migrate: bool = True


class CRMDataManager:
    """Unified data manager supporting both CSV and MongoDB backends."""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.mongodb = None
        self.csv_path = None
        self.csv_headers = []
        
        # In-memory data for CSV mode
        self.contacts_data = []
        
        # Initialize based on configuration
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the appropriate database backend."""
        if self.config.use_mongodb and MONGODB_AVAILABLE:
            try:
                self.mongodb = CRMDatabase(
                    connection_string=self.config.mongodb_uri,
                    db_name=self.config.database_name
                )
                
                if self.mongodb.connect():
                    self.logger.info("Connected to MongoDB successfully")
                    # Ensure indexes are created
                    self.mongodb.create_indexes()
                    self.mongodb.setup_default_priority_rules()
                else:
                    self.logger.error("Failed to connect to MongoDB, falling back to CSV")
                    self.mongodb = None
                    self.config.use_mongodb = False
                    
            except Exception as e:
                self.logger.error(f"MongoDB initialization failed: {e}")
                self.mongodb = None
                self.config.use_mongodb = False
        
        if not self.config.use_mongodb:
            self.logger.info("Using CSV backend")
    
    def load_data_from_csv(self, csv_path: Union[str, Path]) -> bool:
        """Load data from CSV file."""
        self.csv_path = Path(csv_path)
        
        if not self.csv_path.exists():
            self.logger.error(f"CSV file not found: {csv_path}")
            return False
        
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.csv_headers = list(reader.fieldnames) if reader.fieldnames else []
                self.contacts_data = list(reader)
            
            self.logger.info(f"Loaded {len(self.contacts_data)} records from CSV")
            
            # If MongoDB is enabled and auto-migrate is true, migrate the data
            if self.config.use_mongodb and self.config.auto_migrate and self.mongodb:
                self._migrate_csv_to_mongodb()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return False
    
    def _migrate_csv_to_mongodb(self):
        """Migrate CSV data to MongoDB."""
        try:
            self.logger.info("Migrating CSV data to MongoDB...")
            migration_result = self.mongodb.migrate_from_csv(self.contacts_data)
            
            self.logger.info(f"Migration completed: {migration_result}")
            
            # Create backup of original CSV
            if self.config.csv_backup_enabled:
                backup_path = self.csv_path.parent / f"{self.csv_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                import shutil
                shutil.copy2(self.csv_path, backup_path)
                self.logger.info(f"CSV backup created: {backup_path}")
                
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
    
    def get_contacts(self, 
                    status_filter: Optional[str] = None,
                    limit: Optional[int] = None,
                    skip: Optional[int] = None,
                    sort_by: Optional[str] = "priority_score",
                    sort_direction: int = -1) -> List[Dict]:
        """Get contacts with optional filtering and sorting."""
        
        if self.config.use_mongodb and self.mongodb:
            return self._get_contacts_mongodb(status_filter, limit, skip, sort_by, sort_direction)
        else:
            return self._get_contacts_csv(status_filter, limit, skip, sort_by, sort_direction)
    
    def _get_contacts_mongodb(self, status_filter, limit, skip, sort_by, sort_direction) -> List[Dict]:
        """Get contacts from MongoDB."""
        try:
            collection = self.mongodb.db[CONTACTS_COLLECTION]
            
            # Build query
            query = {}
            if status_filter:
                query["status"] = status_filter
            
            # Build cursor
            cursor = collection.find(query)
            
            # Add sorting
            if sort_by:
                cursor = cursor.sort(sort_by, sort_direction)
            
            # Add pagination
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            # Convert ObjectIds to strings for JSON serialization
            contacts = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                contacts.append(doc)
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Failed to get contacts from MongoDB: {e}")
            return []
    
    def _get_contacts_csv(self, status_filter, limit, skip, sort_by, sort_direction) -> List[Dict]:
        """Get contacts from CSV data."""
        filtered_data = self.contacts_data
        
        # Apply status filter
        if status_filter:
            filtered_data = [record for record in filtered_data if record.get("status") == status_filter]
        
        # Apply sorting (simplified)
        if sort_by and sort_by in self.csv_headers:
            try:
                filtered_data.sort(
                    key=lambda x: float(x.get(sort_by, 0) or 0),
                    reverse=(sort_direction == -1)
                )
            except (ValueError, TypeError):
                # Fallback to string sorting
                filtered_data.sort(
                    key=lambda x: str(x.get(sort_by, "")),
                    reverse=(sort_direction == -1)
                )
        
        # Apply pagination
        if skip:
            filtered_data = filtered_data[skip:]
        if limit:
            filtered_data = filtered_data[:limit]
        
        return filtered_data
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Dict]:
        """Get a single contact by ID."""
        if self.config.use_mongodb and self.mongodb:
            try:
                from bson import ObjectId
                collection = self.mongodb.db[CONTACTS_COLLECTION]
                doc = collection.find_one({"_id": ObjectId(contact_id)})
                if doc:
                    doc["_id"] = str(doc["_id"])
                return doc
            except Exception as e:
                self.logger.error(f"Failed to get contact from MongoDB: {e}")
                return None
        else:
            # In CSV mode, use external_row_id or phone_number
            for record in self.contacts_data:
                if record.get("external_row_id") == contact_id or record.get("phone_number") == contact_id:
                    return record
            return None
    
    def update_contact(self, contact_id: str, updates: Dict) -> bool:
        """Update a contact record."""
        if self.config.use_mongodb and self.mongodb:
            return self._update_contact_mongodb(contact_id, updates)
        else:
            return self._update_contact_csv(contact_id, updates)
    
    def _update_contact_mongodb(self, contact_id: str, updates: Dict) -> bool:
        """Update contact in MongoDB."""
        try:
            from bson import ObjectId
            collection = self.mongodb.db[CONTACTS_COLLECTION]
            
            # Add update timestamp
            updates["metadata.updated_at"] = datetime.utcnow()
            
            result = collection.update_one(
                {"_id": ObjectId(contact_id)},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update contact in MongoDB: {e}")
            return False
    
    def _update_contact_csv(self, contact_id: str, updates: Dict) -> bool:
        """Update contact in CSV data."""
        try:
            for i, record in enumerate(self.contacts_data):
                if (record.get("external_row_id") == contact_id or 
                    record.get("phone_number") == contact_id):
                    
                    # Apply updates
                    for key, value in updates.items():
                        record[key] = value
                    
                    # Add update timestamp
                    record["last_updated"] = datetime.now().isoformat()
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update contact in CSV: {e}")
            return False
    
    def create_interaction(self, contact_id: str, interaction_data: Dict) -> Optional[str]:
        """Create an interaction record."""
        if self.config.use_mongodb and self.mongodb:
            try:
                from bson import ObjectId
                collection = self.mongodb.db[INTERACTIONS_COLLECTION]
                
                interaction_doc = {
                    "contact_id": ObjectId(contact_id),
                    "type": interaction_data.get("type", "note"),
                    "timestamp": interaction_data.get("timestamp", datetime.utcnow()),
                    "duration": interaction_data.get("duration", 0),
                    "direction": interaction_data.get("direction", "outbound"),
                    "body": interaction_data.get("body", ""),
                    "external_id": interaction_data.get("external_id"),
                    "metadata": interaction_data.get("metadata", {})
                }
                
                result = collection.insert_one(interaction_doc)
                return str(result.inserted_id)
                
            except Exception as e:
                self.logger.error(f"Failed to create interaction: {e}")
                return None
        else:
            # For CSV mode, add to notes field
            contact = self.get_contact_by_id(contact_id)
            if contact:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_note = f"[{timestamp}] {interaction_data.get('body', '')}"
                
                existing_notes = contact.get('notes', '')
                if existing_notes:
                    contact['notes'] = f"{existing_notes}; {new_note}"
                else:
                    contact['notes'] = new_note
                
                return "csv_note"
            
            return None
    
    def create_task(self, contact_id: str, task_data: Dict) -> Optional[str]:
        """Create a task record."""
        if self.config.use_mongodb and self.mongodb:
            try:
                from bson import ObjectId
                collection = self.mongodb.db[TASKS_COLLECTION]
                
                task_doc = {
                    "contact_id": ObjectId(contact_id),
                    "type": task_data.get("type", "callback"),
                    "due_at": task_data.get("due_at"),
                    "start_time": task_data.get("start_time"),
                    "end_time": task_data.get("end_time"),
                    "state": task_data.get("state", "pending"),
                    "priority": task_data.get("priority", "medium"),
                    "title": task_data.get("title", ""),
                    "description": task_data.get("description", ""),
                    "external_refs": task_data.get("external_refs", {}),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = collection.insert_one(task_doc)
                return str(result.inserted_id)
                
            except Exception as e:
                self.logger.error(f"Failed to create task: {e}")
                return None
        else:
            # For CSV mode, update callback_on or meeting_at fields
            contact = self.get_contact_by_id(contact_id)
            if contact:
                if task_data.get("type") == "callback":
                    contact["callback_on"] = task_data.get("due_at", "").replace(" ", "T") if task_data.get("due_at") else ""
                elif task_data.get("type") == "meeting":
                    contact["meeting_at"] = task_data.get("start_time", "").replace(" ", "T") if task_data.get("start_time") else ""
                
                return "csv_task"
            
            return None
    
    def get_priority_view_data(self, view_type: str = "today") -> List[Dict]:
        """Get data for priority views (today, due, overdue, hot, new)."""
        if self.config.use_mongodb and self.mongodb:
            return self._get_priority_view_mongodb(view_type)
        else:
            return self._get_priority_view_csv(view_type)
    
    def _get_priority_view_mongodb(self, view_type: str) -> List[Dict]:
        """Get priority view data from MongoDB."""
        try:
            contacts_coll = self.mongodb.db[CONTACTS_COLLECTION]
            tasks_coll = self.mongodb.db[TASKS_COLLECTION]
            
            today = datetime.utcnow().date()
            
            if view_type == "today":
                # Find contacts with tasks due today
                pipeline = [
                    {
                        "$lookup": {
                            "from": TASKS_COLLECTION,
                            "localField": "_id",
                            "foreignField": "contact_id",
                            "as": "tasks"
                        }
                    },
                    {
                        "$match": {
                            "tasks.due_at": {
                                "$gte": datetime.combine(today, datetime.min.time()),
                                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
                            }
                        }
                    }
                ]
                
                contacts = list(contacts_coll.aggregate(pipeline))
                
            elif view_type == "overdue":
                pipeline = [
                    {
                        "$lookup": {
                            "from": TASKS_COLLECTION,
                            "localField": "_id",
                            "foreignField": "contact_id",
                            "as": "tasks"
                        }
                    },
                    {
                        "$match": {
                            "tasks.due_at": {
                                "$lt": datetime.combine(today, datetime.min.time())
                            },
                            "tasks.state": "pending"
                        }
                    }
                ]
                
                contacts = list(contacts_coll.aggregate(pipeline))
                
            elif view_type == "new":
                contacts = list(contacts_coll.find({"status": "new"}).sort("metadata.created_at", -1))
                
            else:  # Default to all active contacts
                contacts = list(contacts_coll.find({"status": {"$ne": "archived"}}).sort("priority_score", -1))
            
            # Convert ObjectIds to strings
            for contact in contacts:
                contact["_id"] = str(contact["_id"])
                if "tasks" in contact:
                    for task in contact["tasks"]:
                        task["_id"] = str(task["_id"])
                        task["contact_id"] = str(task["contact_id"])
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Failed to get priority view from MongoDB: {e}")
            return []
    
    def _get_priority_view_csv(self, view_type: str) -> List[Dict]:
        """Get priority view data from CSV."""
        today = datetime.now().date()
        
        if view_type == "today":
            # Find contacts with callbacks or meetings today
            filtered = []
            for record in self.contacts_data:
                callback_date = record.get("callback_on")
                meeting_date = record.get("meeting_at")
                
                if callback_date:
                    try:
                        callback_parsed = datetime.fromisoformat(callback_date.replace("T", " ")).date()
                        if callback_parsed == today:
                            filtered.append(record)
                            continue
                    except:
                        pass
                
                if meeting_date:
                    try:
                        meeting_parsed = datetime.fromisoformat(meeting_date.replace("T", " ")).date()
                        if meeting_parsed == today:
                            filtered.append(record)
                    except:
                        pass
            
            return filtered
            
        elif view_type == "overdue":
            # Find contacts with overdue callbacks or meetings
            filtered = []
            for record in self.contacts_data:
                callback_date = record.get("callback_on")
                meeting_date = record.get("meeting_at")
                
                if callback_date:
                    try:
                        callback_parsed = datetime.fromisoformat(callback_date.replace("T", " ")).date()
                        if callback_parsed < today:
                            filtered.append(record)
                            continue
                    except:
                        pass
                
                if meeting_date:
                    try:
                        meeting_parsed = datetime.fromisoformat(meeting_date.replace("T", " ")).date()
                        if meeting_parsed < today:
                            filtered.append(record)
                    except:
                        pass
            
            return filtered
            
        elif view_type == "new":
            return [record for record in self.contacts_data if record.get("status") == "new"]
            
        else:  # All active
            return [record for record in self.contacts_data if record.get("status") not in ["archived", "deleted", "do_not_call"]]
    
    def export_to_csv(self, export_path: Optional[str] = None) -> bool:
        """Export current data to CSV format."""
        export_file = Path(export_path or self.config.csv_export_path)
        
        try:
            contacts = self.get_contacts()
            if not contacts:
                self.logger.warning("No contacts to export")
                return False
            
            # Determine headers
            if self.config.use_mongodb and contacts:
                # For MongoDB, we need to map back to CSV format
                headers = [
                    "external_row_id", "phone_number", "name", "email", "company", 
                    "title", "city", "address", "source", "status", "notes", "last_call_at",
                    "callback_on", "meeting_at", "gcal_callback_event_id", 
                    "gcal_meeting_event_id"
                ]
            else:
                headers = self.csv_headers
            
            with open(export_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for contact in contacts:
                    # Map MongoDB format back to CSV format
                    if self.config.use_mongodb:
                        csv_row = {
                            "external_row_id": contact.get("external_row_id", ""),
                            "phone_number": contact.get("phone_number", ""),
                            "name": contact.get("name", ""),
                            "email": contact.get("email", ""),
                            "company": contact.get("company", ""),
                            "title": contact.get("title", ""),
                            "city": contact.get("city", ""),
                            "address": contact.get("address", ""),
                            "source": contact.get("source", ""),
                            "status": contact.get("status", ""),
                            "notes": "",  # Would need to query interactions
                            "last_call_at": "",
                            "callback_on": "",
                            "meeting_at": "",
                            "gcal_callback_event_id": "",
                            "gcal_meeting_event_id": ""
                        }
                    else:
                        csv_row = contact
                    
                    writer.writerow(csv_row)
            
            self.logger.info(f"Exported {len(contacts)} contacts to {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            return False
    
    def save_data(self) -> bool:
        """Save data (for CSV mode, writes back to file)."""
        if not self.config.use_mongodb and self.csv_path:
            try:
                # Create backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.csv_path.parent / f"{self.csv_path.stem}_backup_{timestamp}.csv"
                
                if self.csv_path.exists():
                    import shutil
                    shutil.copy2(self.csv_path, backup_path)
                
                # Write to temporary file then replace
                temp_path = self.csv_path.with_suffix('.tmp')
                
                with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                    writer.writeheader()
                    writer.writerows(self.contacts_data)
                
                # Atomic replace
                temp_path.replace(self.csv_path)
                self.logger.info(f"CSV data saved successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to save CSV data: {e}")
                return False
        
        return True  # MongoDB saves automatically
    
    def close(self):
        """Close database connections."""
        if self.mongodb:
            self.mongodb.disconnect()


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment and config files."""
    config = DatabaseConfig()
    
    # Check environment variables
    if os.getenv("USE_MONGODB", "").lower() == "true":
        config.use_mongodb = True
    
    if os.getenv("MONGODB_URI"):
        config.mongodb_uri = os.getenv("MONGODB_URI")
    
    if os.getenv("DATABASE_NAME"):
        config.database_name = os.getenv("DATABASE_NAME")
    
    # Check for config file
    config_file = Path("database_config.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
            
            config.use_mongodb = file_config.get("use_mongodb", config.use_mongodb)
            config.mongodb_uri = file_config.get("mongodb_uri", config.mongodb_uri)
            config.database_name = file_config.get("database_name", config.database_name)
            config.csv_backup_enabled = file_config.get("csv_backup_enabled", config.csv_backup_enabled)
            config.auto_migrate = file_config.get("auto_migrate", config.auto_migrate)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to load database config: {e}")
    
    return config


if __name__ == "__main__":
    # Example usage and testing
    config = load_database_config()
    
    # For testing, use CSV mode
    config.use_mongodb = False
    
    db_manager = CRMDataManager(config)
    
    # Test loading sample data
    sample_csv = Path("sample_contacts.csv")
    if sample_csv.exists():
        if db_manager.load_data_from_csv(sample_csv):
            print(f"Loaded data successfully")
            
            # Test getting contacts
            contacts = db_manager.get_contacts(limit=5)
            print(f"Retrieved {len(contacts)} contacts")
            
            # Test priority view
            today_contacts = db_manager.get_priority_view_data("today")
            print(f"Today's contacts: {len(today_contacts)}")
    
    db_manager.close()