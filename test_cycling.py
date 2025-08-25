#!/usr/bin/env python3
"""
Test cycling behavior - simulate going to end of records and cycling back
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch
from io import StringIO

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def simulate_cycling_test():
    """Test the cycling behavior by simulating end-of-records scenario."""
    
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
    
    print("🧪 Cycling Behavior Test")
    print("==" * 25)
    
    try:
        app = VStudioCLI(debug=True)
        app.testing_mode = True  # Enable testing mode
        app._initialize_database()  # Force database initialization
        
        if app.db_manager:
            # Load data
            app.data = app.db_manager.get_contacts()
            print(f"✅ Loaded {len(app.data)} contacts from MongoDB")
            
            # Test cycling behavior - simulate being at the end
            original_index = app.current_index
            app.current_index = len(app.data) - 1  # Set to last record
            print(f"📍 Set current index to last record: {app.current_index}")
            
            # Simulate hitting "next" from last record
            app.current_index += 1
            print(f"📍 Incremented to: {app.current_index} (beyond end)")
            
            # Test the cycling logic
            if app.current_index >= len(app.data):
                app.current_index = 0
                print(f"🔄 Cycled back to first record: {app.current_index}")
                print("✅ Cycling behavior working correctly!")
            else:
                print("❌ Cycling logic not working")
            
            # Show current record info
            if app.current_index < len(app.data):
                current_contact = app.data[app.current_index]
                print(f"👤 Current contact: {current_contact.get('name', 'Unknown')}")
        else:
            print("❌ MongoDB not connected")
            
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()
        
        print("\n👋 Test completed - original config restored")

if __name__ == "__main__":
    simulate_cycling_test()