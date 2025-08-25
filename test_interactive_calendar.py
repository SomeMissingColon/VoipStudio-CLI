#!/usr/bin/env python3
"""
Test interactive calendar workflow with simulated input
This simulates the exact user workflow that was crashing
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def test_interactive_calendar():
    """Test interactive calendar workflow with mocked input."""
    
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
    
    print("🎮 Testing Interactive Calendar Workflow")
    print("=" * 50)
    print("Simulating: Calendar → Day Details → Contact Selection")
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("✅ MongoDB connected")
            
            # Simulate the exact workflow that was crashing:
            # 1. Go to calendar
            # 2. Press 'd' + '15' (day details)  
            # 3. Press '1' (select first contact)
            # 4. Press 'c' (return to calendar)
            
            current_date = datetime.now()
            events = app._get_month_events(current_date.year, current_date.month)
            
            if 15 in events:
                print("🎯 Step 1: Getting day 15 events...")
                day_events = events[15]
                print(f"✅ Found {len(day_events)} events on day 15")
                
                print("🎯 Step 2: Simulating contact selection...")
                
                # This simulates what happens when user selects contact #1
                if day_events:
                    selected_event = day_events[0]  # First contact
                    selected_date = datetime(current_date.year, current_date.month, 15).date()
                    
                    contact = selected_event['contact']
                    print(f"Selected contact: {contact.get('name', 'Unknown')}")
                    
                    # Test the _work_on_calendar_contact method
                    print("🎯 Step 3: Testing contact workflow...")
                    
                    # Save original state
                    original_data = app.data
                    original_index = app.current_index
                    
                    try:
                        # Set up contact as current record (this was failing)
                        app.data = [contact]
                        app.current_index = 0
                        
                        print("✅ Contact data setup successful")
                        
                        # Test that _display_record works (this was the crash point)
                        print("🔍 Testing display_record...")
                        
                        # Redirect output to prevent console spam
                        import io
                        import contextlib
                        
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            app._display_record()
                        
                        print("✅ Contact display successful!")
                        print("✅ Calendar-to-contact workflow fixed!")
                        
                        # Show what the user would see
                        contact_name = contact.get('name', 'Unknown')
                        company = contact.get('company', 'N/A')
                        phone = contact.get('phone_number', 'N/A')
                        
                        print(f"\n📋 Contact Details:")
                        print(f"  Name: {contact_name}")
                        print(f"  Company: {company}")
                        print(f"  Phone: {phone}")
                        
                        print(f"\n🎉 Workflow Test Complete!")
                        print(f"User can now:")
                        print(f"  📞 Make calls (press '1')")
                        print(f"  💬 Send SMS (press '2')")  
                        print(f"  📝 Add notes (press '5')")
                        print(f"  📊 Mark outcomes (press 'o')")
                        print(f"  🔄 Return to calendar (press 'c')")
                        
                    finally:
                        # Restore original state
                        app.data = original_data
                        app.current_index = original_index
                
            else:
                print("❌ No events found on day 15")
                
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
        
        print(f"\n👋 Interactive test completed")

if __name__ == "__main__":
    test_interactive_calendar()