#!/usr/bin/env python3
"""
Demo script to showcase the new monthly calendar view
This simulates the calendar interaction without requiring full CLI startup
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def demo_calendar():
    """Demo the calendar view functionality."""
    
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
    
    print("🎯 Calendar Demo - Interactive Monthly View")
    print("This demonstrates the new calendar features with test data")
    print("=" * 60)
    
    try:
        app = VStudioCLI(debug=False)
        app.testing_mode = True
        app._initialize_database()
        
        if app.db_manager:
            print("✅ MongoDB connected - launching calendar view...")
            print("\nCalendar Features:")
            print("• Monthly grid layout showing callbacks and meetings")
            print("• Navigation: 'p' = previous month, 'n' = next month")
            print("• 't' = today, 'd' = day details, 'q' = quit")
            print("• Color-coded events: Yellow ○ callbacks, Green ● meetings")
            print("• Red highlighting for overdue items")
            print("• Today highlighted in blue")
            print("\nStarting interactive calendar...")
            print("-" * 60)
            
            # Call the actual calendar view
            app._show_calendar_view()
            
        else:
            print("❌ MongoDB connection failed")
            
    except KeyboardInterrupt:
        print("\n\n👋 Calendar demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print("\n👋 Calendar demo completed - original config restored")

if __name__ == "__main__":
    demo_calendar()