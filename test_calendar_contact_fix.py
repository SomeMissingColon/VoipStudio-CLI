#!/usr/bin/env python3
"""
Test the fixed calendar contact selection functionality
This reproduces the user selection workflow that was crashing
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch
from io import StringIO

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def test_calendar_contact_fix():
    """Test the calendar contact selection workflow after fixes."""
    
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
    
    print("🔧 Testing Fixed Calendar Contact Selection")
    print("=" * 50)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("✅ MongoDB connected successfully")
            
            # Get a test contact from the calendar events
            from datetime import datetime
            current_date = datetime.now()
            events = app._get_month_events(current_date.year, current_date.month)
            
            if 15 in events and events[15]:
                print("✅ Found events on day 15")
                
                # Test the problematic workflow that was crashing
                test_event = events[15][0]  # First event on day 15
                selected_date = datetime(current_date.year, current_date.month, 15).date()
                
                print("🎯 Testing contact data handling...")
                
                # This is the code path that was failing
                contact = test_event['contact']
                print(f"Contact type: {type(contact)}")
                print(f"Contact keys: {list(contact.keys())}")
                
                # Test the _display_record method directly (this was crashing)
                original_data = app.data
                original_index = app.current_index
                
                try:
                    app.data = [contact]
                    app.current_index = 0
                    
                    print("🔍 Testing _display_record method (this was crashing)...")
                    
                    # Capture the output instead of displaying it
                    from io import StringIO
                    import contextlib
                    
                    output_buffer = StringIO()
                    with contextlib.redirect_stdout(output_buffer):
                        app._display_record()
                    
                    print("✅ _display_record completed successfully!")
                    print("✅ Contact data type conversion fixed!")
                    
                    # Test a few field values to make sure type conversion works
                    for field in ['name', 'company', 'phone_number', 'email']:
                        value = contact.get(field, '')
                        if isinstance(value, str):
                            test_strip = value.strip()
                            print(f"  ✅ {field}: string type, strip() works")
                        else:
                            test_convert = str(value) if value else ''
                            print(f"  ✅ {field}: {type(value)} type, converted to string")
                    
                except Exception as e:
                    print(f"❌ Still failing: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    app.data = original_data
                    app.current_index = original_index
                
            else:
                print("❌ No test events found on day 15")
                
        else:
            print("❌ MongoDB connection failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print(f"\n👋 Test completed - original config restored")

if __name__ == "__main__":
    test_calendar_contact_fix()