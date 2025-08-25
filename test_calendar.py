#!/usr/bin/env python3
"""
Test the new monthly calendar grid functionality
"""

import sys
import os
import json
from pathlib import Path

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def test_calendar_functionality():
    """Test the new calendar view functionality."""
    
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
    
    print("🧪 Calendar View Test")
    print("==" * 25)
    
    try:
        app = VStudioCLI(debug=False)  # Disable debug to reduce output
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("✅ MongoDB connected successfully")
            
            # Test month events method
            from datetime import datetime
            current_date = datetime.now()
            events = app._get_month_events(current_date.year, current_date.month)
            
            print(f"✅ Found events for {len(events)} days in {current_date.strftime('%B %Y')}")
            
            # Show sample of events
            if events:
                print("\n📅 Sample Events:")
                for day, day_events in list(events.items())[:3]:  # Show first 3 days with events
                    print(f"  Day {day}: {len(day_events)} event(s)")
                    for event in day_events:
                        contact_name = event['contact'].get('name', 'Unknown')
                        event_type = event['type'].title()
                        print(f"    - {event_type}: {contact_name} at {event['time']}")
            
            print("\n✅ Calendar functionality is ready!")
            print("💡 To test interactively, run the main CLI and choose calendar view from dashboard")
            
        else:
            print("❌ MongoDB connection failed")
            
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print("\n👋 Test completed - original config restored")

if __name__ == "__main__":
    test_calendar_functionality()