#!/bin/bash
# VStudio CLI CRM Startup Script with MongoDB

set -e

echo "🚀 Starting VStudio CLI CRM with MongoDB backend..."
echo "=================================================="

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
if ! timeout 5 mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo "⚠️  MongoDB not running, starting MongoDB..."
    
    # Create data directory if it doesn't exist
    mkdir -p /tmp/mongodb_data
    
    # Start MongoDB in background
    echo "🗄️  Starting MongoDB server..."
    mongod --dbpath /tmp/mongodb_data --port 27017 --bind_ip 127.0.0.1 --fork --logpath /tmp/mongodb.log
    
    # Wait for MongoDB to start
    echo "⏳ Waiting for MongoDB to be ready..."
    sleep 3
    
    # Verify connection
    if ! timeout 10 mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        echo "❌ Failed to start MongoDB. Please check /tmp/mongodb.log for errors."
        exit 1
    fi
fi

echo "✅ MongoDB is running!"

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Check if database is set up
echo "🔍 Checking database setup..."
if ! python -c "
from database import CRMDataManager, DatabaseConfig
config = DatabaseConfig()
config.use_mongodb = True
try:
    db = CRMDataManager(config)
    contacts = db.get_contacts()
    print(f'Database ready - {len(contacts)} contacts found')
except Exception as e:
    print(f'Database setup needed: {e}')
    exit(1)
" 2>/dev/null; then
    echo "⚠️  Database not properly set up. Run setup first:"
    echo "   python setup_mongodb.py --csv your_data.csv"
    exit 1
fi

echo "✅ Database is ready!"
echo ""
echo "🎯 Starting VStudio CLI CRM..."
echo "=================================================="

# Start the application
if [ $# -eq 0 ]; then
    echo "Usage: $0 <csv-file> [additional options]"
    echo "Example: $0 contacts.csv --debug"
    exit 1
fi

# Run the main application
python vstudio_cli.py "$@"

echo ""
echo "👋 VStudio CLI CRM session ended."