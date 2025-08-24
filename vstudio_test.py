#!/usr/bin/env python3
"""
VStudio CLI configured for test database - for developing past-due and scheduled features.
This is identical to vstudio_cli.py but uses the test database.
"""

import sys
import os
import json
from pathlib import Path

# Import the main VStudio CLI
from vstudio_cli import VStudioCLI

def main():
    """Main entry point for test version."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VStudio CLI (TEST MODE) - MongoDB CRM backend with test data",
        epilog="This version uses the test database (vstudio_crm_test) with enriched test data."
    )
    parser.add_argument("csv_file", nargs="?", help="CSV file (optional - will use test database)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
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
    
    print("🧪 VStudio CLI - TEST MODE")
    print("Using test database: vstudio_crm_test")
    print("=" * 50)
    
    try:
        app = VStudioCLI(debug=args.debug)
        app.run(args.csv_file)
    finally:
        # Restore original config
        if backup_config_path.exists():
            backup_config_path.rename(original_config_path)
        elif temp_config_path.exists():
            temp_config_path.unlink()  # Remove test config if no original existed
        
        print("\n👋 Test session ended - original config restored")

if __name__ == "__main__":
    main()