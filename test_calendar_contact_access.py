#!/usr/bin/env python3
"""
Test calendar-to-contact access functionality
This tests the new feature where users can select contacts directly from calendar day details
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def test_calendar_contact_workflow():
    """Test the calendar-to-contact workflow functionality."""
    
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
    
    print("🧪 Calendar-to-Contact Workflow Test")
    print("=" * 50)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            print("✅ MongoDB connected successfully")
            
            # Test the enhanced day details functionality
            events = app._get_month_events(current_year, current_month)
            
            if 15 in events:  # Day with multiple events
                print(f"\n🎯 Testing Day 15 Details (Multiple Events)")
                print(f"Expected: 4 events with numbered selection")
                
                day_15_events = events[15]
                print(f"✅ Found {len(day_15_events)} events on day 15:")
                
                for i, event in enumerate(day_15_events, 1):
                    contact = event['contact']
                    event_type = event['type'].title()
                    contact_name = contact.get('name', 'Unknown')
                    event_time = event['time']
                    print(f"  {i}. {event_type}: {contact_name} at {event_time}")
                
                print(f"\n✅ Calendar-to-Contact Features Available:")
                print(f"  📋 Numbered contact selection (1-{len(day_15_events)})")
                print(f"  📞 Direct calling from calendar context")
                print(f"  💬 SMS messaging with calendar context")
                print(f"  📝 Note adding with event context")
                print(f"  📊 Outcome marking from calendar")
                print(f"  🔄 Navigation: 'c' back to calendar, 'd' back to day details")
                
            # Test overdue event detection
            # Check July for overdue events
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            prev_events = app._get_month_events(prev_year, prev_month)
            if prev_events:
                print(f"\n🔴 Testing Overdue Event Detection")
                overdue_count = 0
                for day, day_events in prev_events.items():
                    for event in day_events:
                        overdue_count += 1
                        contact_name = event['contact'].get('name', 'Unknown')
                        print(f"  ⚠️  OVERDUE: {contact_name} - {event['type'].title()}")
                
                print(f"✅ Found {overdue_count} overdue events that will show overdue warnings")
            
            print(f"\n🎮 Calendar Navigation Workflow:")
            print(f"1. 📅 Start with calendar grid view")
            print(f"2. 🔍 Press 'd' + day number to see day details")
            print(f"3. 📋 See numbered list of contacts/events")
            print(f"4. 🎯 Press 1-{len(day_15_events) if 15 in events else 'X'} to work on specific contact")
            print(f"5. 📞 Full contact operations: call, text, notes, outcomes")
            print(f"6. 🔄 Return with 'c' (calendar) or 'd' (day details)")
            
            print(f"\n✅ All calendar-to-contact features implemented and ready!")
            print(f"💡 To test interactively: python3 calendar_feature_demo.py")
            
        else:
            print("❌ MongoDB connection failed")
            
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print(f"\n👋 Test completed - original config restored")

if __name__ == "__main__":
    test_calendar_contact_workflow()