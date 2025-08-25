#!/usr/bin/env python3
"""
Test all calendar features including overdue and multiple events
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def test_all_calendar_features():
    """Test calendar with overdue events and multiple events."""
    
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
    
    print("🧪 Complete Calendar Features Test")
    print("=" * 50)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            # Test current month events
            print(f"📅 Testing {current_date.strftime('%B %Y')} events...")
            current_events = app._get_month_events(current_year, current_month)
            print(f"✅ Found events for {len(current_events)} days in current month")
            
            # Show current month events
            if current_events:
                print(f"\n🔵 {current_date.strftime('%B %Y')} Events:")
                for day, day_events in sorted(current_events.items()):
                    print(f"  Day {day}: {len(day_events)} event(s)")
                    for event in day_events:
                        contact_name = event['contact'].get('name', 'Unknown')
                        event_type = event['type'].title()
                        print(f"    - {event_type}: {contact_name} at {event['time']}")
                    
                    # Check for multiple events (should show ◆ symbol)
                    if len(day_events) > 1:
                        print(f"      📍 This will show as [cyan]◆ {len(day_events)}[/cyan] on calendar")
            
            # Test previous month (for overdue events)
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year
            
            prev_date = datetime(prev_year, prev_month, 1)
            print(f"\n📅 Testing {prev_date.strftime('%B %Y')} overdue events...")
            prev_events = app._get_month_events(prev_year, prev_month)
            print(f"✅ Found events for {len(prev_events)} days in previous month")
            
            # Show previous month events (overdue)
            if prev_events:
                print(f"\n🔴 {prev_date.strftime('%B %Y')} Overdue Events:")
                for day, day_events in sorted(prev_events.items()):
                    print(f"  Day {day}: {len(day_events)} overdue event(s)")
                    for event in day_events:
                        contact_name = event['contact'].get('name', 'Unknown')
                        event_type = event['type'].title()
                        print(f"    - OVERDUE {event_type}: {contact_name} at {event['time']}")
                        print(f"      📍 This will show in [red]RED[/red] on calendar")
            
            print(f"\n✅ Calendar Test Summary:")
            print(f"  📅 Current month ({current_date.strftime('%B')}): {len(current_events)} days with events")
            print(f"  🔴 Previous month ({prev_date.strftime('%B')}): {len(prev_events)} days with overdue events")
            print(f"  🔵 Multiple event days: {sum(1 for events in current_events.values() if len(events) > 1)}")
            
            print(f"\n🎯 What to expect in calendar view:")
            print(f"  • Navigate to {prev_date.strftime('%B %Y')} with 'p' to see RED overdue events")
            print(f"  • In {current_date.strftime('%B %Y')}, day 15 should show [cyan]◆ 4[/cyan] (multiple events)")
            print(f"  • Today ({current_date.day}) should be highlighted in blue")
            print(f"  • Use 'd' + day number to see detailed event lists")
            
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
    test_all_calendar_features()