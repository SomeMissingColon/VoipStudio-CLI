#!/usr/bin/env python3
"""
Calendar Feature Demo - Shows all the new calendar capabilities
This provides a guided tour of the enhanced calendar features
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def calendar_demo():
    """Demo all calendar features with guided instructions."""
    
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
    
    print("🎯 CALENDAR FEATURE DEMO")
    print("=" * 60)
    print("This demo showcases the complete calendar revamp with:")
    print("• Monthly grid layout")
    print("• Overdue events (RED highlighting)")
    print("• Multiple events per day (◆ symbol)")
    print("• Interactive navigation")
    print("• Detailed day views")
    print("• 🆕 NEW: Direct contact access from calendar!")
    print("=" * 60)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            today = datetime.now()
            
            print(f"\n✅ MongoDB Connected - {app.db_manager.get_contacts().__len__()} contacts loaded")
            
            print(f"\n📋 WHAT YOU'LL SEE IN THE CALENDAR:")
            print(f"")
            print(f"🔵 CURRENT MONTH ({today.strftime('%B %Y')}):")
            print(f"  • Day {today.day}: Highlighted in BLUE (today)")
            print(f"  • Day 15: Shows '◆ 4' (4 events on same day)")
            print(f"  • Days 25,26,27,29,31: Shows individual callbacks/meetings")
            print(f"")
            print(f"🔴 PREVIOUS MONTH (July 2025) - Press 'p' to navigate:")
            print(f"  • Days 23,26,28,30: RED overdue events")
            print(f"  • These will be clearly marked as overdue")
            print(f"")
            print(f"🎮 NAVIGATION CONTROLS:")
            print(f"  • 'p' = Previous month (see July overdue events)")
            print(f"  • 'n' = Next month")
            print(f"  • 't' = Jump back to today")
            print(f"  • 'd' + day number = Show day details")
            print(f"  • 'q' = Quit calendar")
            print(f"")
            print(f"🎯 DEMO INSTRUCTIONS:")
            print(f"1. Start by looking at current month layout")
            print(f"2. Press 'p' to go to July and see RED overdue events")
            print(f"3. Press 'n' to come back to August")
            print(f"4. Try 'd' then '15' to see the 4 events on day 15")
            print(f"5. 🆕 In day details: Press '1', '2', '3', or '4' to work on contacts!")
            print(f"6. 🆕 From contact view: Call, text, add notes, mark outcomes")
            print(f"7. Use 't' to ensure today is highlighted")
            print(f"")
            
            input("Press Enter to launch the interactive calendar demo...")
            
            print("\n" + "=" * 60)
            print("🚀 LAUNCHING INTERACTIVE CALENDAR")
            print("=" * 60)
            
            # Launch the actual calendar
            app._show_calendar_view()
            
        else:
            print("❌ MongoDB connection failed")
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print(f"\n" + "=" * 60)
        print("🎉 CALENDAR DEMO COMPLETED!")
        print("You've seen all the new features:")
        print("✅ Monthly grid layout")
        print("✅ Overdue event highlighting (RED)")
        print("✅ Multiple event indicators (◆)")
        print("✅ Month navigation (p/n)")
        print("✅ Day detail views (d + day)")
        print("✅ Today highlighting (blue)")
        print("=" * 60)
        print("👋 Original config restored")

if __name__ == "__main__":
    calendar_demo()