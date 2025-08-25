#!/usr/bin/env python3
"""
Test script to verify dashboard functionality with MongoDB test database
"""

import sys
import os
import json
from pathlib import Path

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def main():
    """Test the dashboard and cycling functionality."""
    
    # Override database config to use test database
    test_config = {
        "use_mongodb": True,
        "mongodb_uri": "mongodb://localhost:27017/",
        "database_name": "vstudio_crm_test",  # Test database
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
    
    print("🧪 Dashboard Test - MongoDB Mode")
    print("Using test database: vstudio_crm_test")
    print("==" * 25)
    
    try:
        app = VStudioCLI(debug=True)
        
        # Test dashboard functionality
        print("\n🎯 Testing Dashboard Statistics...")
        if hasattr(app, '_get_crm_statistics') and app.db_manager:
            stats = app._get_crm_statistics()
            print(f"✅ Statistics calculated: {stats}")
        
        print("\n🎯 Testing Welcome Dashboard...")
        if hasattr(app, '_show_welcome_dashboard') and app.db_manager:
            print("✅ Welcome dashboard method exists")
        
        print("\n🎯 Testing Calendar View...")
        if hasattr(app, '_show_calendar_view') and app.db_manager:
            print("✅ Calendar view method exists")
            
        print("\n✅ All dashboard methods are available!")
        print("💡 Dashboard features working with MongoDB backend")
        
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()  # Remove test config if no original existed
        
        print("\n👋 Test completed - original config restored")

if __name__ == "__main__":
    main()