#!/usr/bin/env python3
"""
Debug the update contact functionality
"""

import sys
import os
import json
from pathlib import Path

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI, STATUS_CLOSE_WON

def debug_update():
    """Debug contact updates."""
    
    # Override database config to use test database
    test_config = {
        "use_mongodb": True,
        "mongodb_uri": "mongodb://localhost:27017/",
        "database_name": "vstudio_crm_test",
        "csv_backup_enabled": True,
        "auto_migrate": False
    }
    
    # Write temporary config for test mode
    original_config_path = Path("database_config.json")
    backup_config_path = Path("database_config.json.backup")
    temp_config_path = Path("database_config.json")
    
    # Backup original config if it exists
    if original_config_path.exists():
        import shutil
        shutil.copy2(original_config_path, backup_config_path)
    
    # Write test config
    with open(temp_config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print("🔍 Debug Contact Updates")
    print("=" * 30)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("✅ MongoDB connected")
            
            # Get a test contact
            contacts = app.db_manager.get_contacts(limit=1)
            if contacts:
                contact = contacts[0]
                contact_id = contact.get('external_row_id')
                original_status = contact.get('status', 'unknown')
                
                print(f"📋 Test Contact:")
                print(f"  ID: {contact_id}")
                print(f"  Name: {contact.get('name', 'Unknown')}")
                print(f"  Current Status: {original_status}")
                
                # Try to update directly with MongoDB
                if hasattr(app.db_manager, 'mongodb') and app.db_manager.mongodb:
                    collection = app.db_manager.mongodb.db['contacts']
                    
                    # Check if contact exists
                    existing = collection.find_one({'external_row_id': contact_id})
                    if existing:
                        print(f"✅ Contact exists in MongoDB")
                        
                        # Try the update
                        result = collection.update_one(
                            {'external_row_id': contact_id},
                            {'$set': {'status': STATUS_CLOSE_WON}}
                        )
                        
                        print(f"📊 Update Result:")
                        print(f"  Matched: {result.matched_count}")
                        print(f"  Modified: {result.modified_count}")
                        
                        if result.modified_count > 0:
                            print(f"✅ Direct MongoDB update successful!")
                            
                            # Verify the change
                            updated = collection.find_one({'external_row_id': contact_id})
                            new_status = updated.get('status')
                            print(f"✅ Verified new status: {new_status}")
                            
                            # Test using the app method
                            restore_result = app.db_manager.update_contact(contact_id, {'status': original_status})
                            print(f"🔄 App method restore result: {restore_result}")
                            
                        else:
                            print(f"❌ No documents were modified")
                    else:
                        print(f"❌ Contact not found in MongoDB")
                        print(f"Available contact IDs:")
                        for c in collection.find({}, {'external_row_id': 1}).limit(5):
                            print(f"  - {c.get('external_row_id')}")
                            
            else:
                print("❌ No contacts found")
                
        else:
            print("❌ MongoDB connection failed")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print(f"\n👋 Debug completed")

if __name__ == "__main__":
    debug_update()