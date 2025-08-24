#!/bin/bash
# VStudio CLI CRM - Start with MongoDB Backend

set -e

echo "🚀 VStudio CLI CRM - MongoDB Edition"
echo "===================================="

# Activate virtual environment first
echo "🐍 Activating Python virtual environment..."
source venv/bin/activate

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
if ! timeout 5 python -c "
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
    print('MongoDB is accessible')
except:
    exit(1)
" >/dev/null 2>&1; then
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
    if ! timeout 10 python -c "
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=8000)
    client.admin.command('ping')
    print('MongoDB is accessible')
except Exception as e:
    print(f'MongoDB not accessible: {e}')
    exit(1)
" >/dev/null 2>&1; then
        echo "❌ Failed to start MongoDB. Please check /tmp/mongodb.log for errors."
        exit 1
    fi
fi

echo "✅ MongoDB is running!"

# Database is accessible, remove duplicate venv activation

# Check database status
echo "📊 Checking CRM database..."
python db_stats.py

echo ""
echo "🎯 Starting VStudio CLI CRM..."
echo "=================================="

# Start the application with MongoDB backend
python vstudio_cli.py "$@"

echo ""
echo "👋 VStudio CLI CRM session ended."