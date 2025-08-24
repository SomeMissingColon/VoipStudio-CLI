#!/usr/bin/env python3
"""
MongoDB Setup Script for VStudio CLI CRM

This script helps set up MongoDB for the VStudio CLI application:
1. Checks MongoDB installation and connection
2. Creates database and collections
3. Sets up indexes for optimal performance
4. Migrates existing CSV data
5. Configures the application to use MongoDB
"""

import json
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

from database import DatabaseConfig, CRMDataManager


class MongoDBSetup:
    """MongoDB setup and configuration manager."""
    
    def __init__(self):
        self.mongodb_uri = "mongodb://localhost:27017/"
        self.database_name = "vstudio_crm"
        self.client = None
        
    def check_mongodb_installation(self) -> bool:
        """Check if MongoDB is installed and accessible."""
        logger.info("Checking MongoDB installation...")
        
        if not MONGODB_AVAILABLE:
            logger.error("PyMongo not installed. Please install with: pip install pymongo")
            return False
        
        # Check if MongoDB server is running
        try:
            client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            client.close()
            logger.info("✓ MongoDB server is running and accessible")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError):
            logger.error("✗ MongoDB server is not running or not accessible")
            return False
        except Exception as e:
            logger.error(f"✗ Error connecting to MongoDB: {e}")
            return False
    
    def install_mongodb_instructions(self):
        """Print MongoDB installation instructions."""
        logger.info("\n" + "="*60)
        logger.info("MongoDB Installation Instructions")
        logger.info("="*60)
        logger.info("\nFor Ubuntu/Debian:")
        logger.info("1. wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -")
        logger.info("2. echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list")
        logger.info("3. sudo apt update")
        logger.info("4. sudo apt install -y mongodb-org")
        logger.info("5. sudo systemctl start mongod")
        logger.info("6. sudo systemctl enable mongod")
        
        logger.info("\nFor macOS:")
        logger.info("1. brew tap mongodb/brew")
        logger.info("2. brew install mongodb-community")
        logger.info("3. brew services start mongodb/brew/mongodb-community")
        
        logger.info("\nFor Windows:")
        logger.info("1. Download MongoDB Community Server from https://www.mongodb.com/try/download/community")
        logger.info("2. Run the installer and follow the setup wizard")
        logger.info("3. Start MongoDB service from Services manager")
        
        logger.info("\nAlternatively, use MongoDB Atlas (cloud):")
        logger.info("1. Sign up at https://www.mongodb.com/atlas")
        logger.info("2. Create a free cluster")
        logger.info("3. Get your connection string")
        logger.info("4. Update the mongodb_uri in database_config.json")
        
        logger.info("\n" + "="*60)
    
    def create_database_structure(self) -> bool:
        """Create database and collections with proper indexes."""
        try:
            logger.info("Setting up database structure...")
            
            from mongodb_schema import CRMDatabase
            
            db_manager = CRMDatabase(self.mongodb_uri, self.database_name)
            
            if not db_manager.connect():
                logger.error("Failed to connect to MongoDB")
                return False
            
            # Create indexes
            db_manager.create_indexes()
            
            # Setup default priority rules
            db_manager.setup_default_priority_rules()
            
            logger.info("✓ Database structure created successfully")
            db_manager.disconnect()
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create database structure: {e}")
            return False
    
    def migrate_csv_data(self, csv_path: Path) -> bool:
        """Migrate existing CSV data to MongoDB."""
        try:
            logger.info(f"Migrating data from {csv_path}...")
            
            # Create database manager
            config = DatabaseConfig()
            config.use_mongodb = True
            config.mongodb_uri = self.mongodb_uri
            config.database_name = self.database_name
            config.auto_migrate = True
            
            db_manager = CRMDataManager(config)
            
            # Load and migrate CSV data
            if db_manager.load_data_from_csv(csv_path):
                logger.info("✓ CSV data migrated successfully")
                return True
            else:
                logger.error("✗ Failed to migrate CSV data")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error during CSV migration: {e}")
            return False
    
    def update_application_config(self) -> bool:
        """Update application configuration to use MongoDB."""
        try:
            config_path = Path("database_config.json")
            
            # Load existing config or create new one
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update MongoDB settings
            config.update({
                "use_mongodb": True,
                "mongodb_uri": self.mongodb_uri,
                "database_name": self.database_name,
                "csv_backup_enabled": True,
                "auto_migrate": False,  # Disable auto-migration after initial setup
            })
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("✓ Application configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to update application config: {e}")
            return False
    
    def test_database_operations(self) -> bool:
        """Test basic database operations."""
        try:
            logger.info("Testing database operations...")
            
            config = DatabaseConfig()
            config.use_mongodb = True
            config.mongodb_uri = self.mongodb_uri
            config.database_name = self.database_name
            
            db_manager = CRMDataManager(config)
            
            # Test getting contacts
            contacts = db_manager.get_contacts(limit=5)
            logger.info(f"✓ Retrieved {len(contacts)} contacts")
            
            # Test priority views
            today_contacts = db_manager.get_priority_view_data("today")
            new_contacts = db_manager.get_priority_view_data("new")
            
            logger.info(f"✓ Priority views working - Today: {len(today_contacts)}, New: {len(new_contacts)}")
            
            db_manager.close()
            return True
            
        except Exception as e:
            logger.error(f"✗ Database operations test failed: {e}")
            return False
    
    def run_setup(self, csv_path: Path = None) -> bool:
        """Run the complete MongoDB setup process."""
        logger.info("Starting MongoDB setup for VStudio CLI CRM")
        logger.info("="*50)
        
        # Step 1: Check MongoDB installation
        if not self.check_mongodb_installation():
            self.install_mongodb_instructions()
            return False
        
        # Step 2: Create database structure
        if not self.create_database_structure():
            return False
        
        # Step 3: Migrate CSV data if provided
        if csv_path and csv_path.exists():
            if not self.migrate_csv_data(csv_path):
                return False
        else:
            logger.info("No CSV file provided, skipping data migration")
        
        # Step 4: Update application configuration
        if not self.update_application_config():
            return False
        
        # Step 5: Test database operations
        if not self.test_database_operations():
            return False
        
        logger.info("\n" + "="*50)
        logger.info("✓ MongoDB setup completed successfully!")
        logger.info("="*50)
        logger.info("\nNext steps:")
        logger.info("1. Run: python vstudio_cli.py your_contacts.csv")
        logger.info("2. The application will now use MongoDB as the backend")
        logger.info("3. CSV exports are still available for compatibility")
        logger.info("4. Check database_config.json for additional settings")
        
        return True


def main():
    """Main setup script entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup MongoDB for VStudio CLI CRM")
    parser.add_argument("--csv", type=Path, help="CSV file to migrate (optional)")
    parser.add_argument("--uri", default="mongodb://localhost:27017/", 
                       help="MongoDB connection URI (default: mongodb://localhost:27017/)")
    parser.add_argument("--database", default="vstudio_crm", 
                       help="Database name (default: vstudio_crm)")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check MongoDB installation, don't setup")
    
    args = parser.parse_args()
    
    setup = MongoDBSetup()
    setup.mongodb_uri = args.uri
    setup.database_name = args.database
    
    if args.check_only:
        # Just check if MongoDB is available
        if setup.check_mongodb_installation():
            logger.info("MongoDB is ready for use!")
            sys.exit(0)
        else:
            logger.error("MongoDB is not available")
            setup.install_mongodb_instructions()
            sys.exit(1)
    
    # Run full setup
    if setup.run_setup(args.csv):
        logger.info("Setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()