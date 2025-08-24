# MongoDB Setup for VStudio CLI CRM

This document explains how to use the MongoDB database backend for your VStudio CLI CRM application.

## 🎯 Overview

Your VStudio CLI application now supports both CSV and MongoDB backends:

- **CSV Mode**: Original file-based storage (backward compatible)
- **MongoDB Mode**: Database-backed storage with advanced CRM features

The MongoDB setup provides:
- Full interaction history tracking
- Advanced priority scoring
- Task management (callbacks, meetings)
- Calendar integration tracking
- Audit trails
- High-performance queries

## 🚀 Quick Start

### 1. Setup MongoDB Database

```bash
# Setup with existing CSV data
python setup_mongodb.py --csv your_contacts.csv

# Or setup empty database
python setup_mongodb.py
```

### 2. Start Application with MongoDB

```bash
# Using the startup script (recommended)
./start_with_mongodb.sh your_contacts.csv

# Or manually
source venv/bin/activate
python vstudio_cli.py your_contacts.csv
```

## 📊 Database Schema

The MongoDB CRM database includes these collections:

### Contacts
- Primary contact information
- Priority scores
- Metadata (creation date, data quality, etc.)
- Tags for categorization

### Interactions
- Call records
- SMS messages
- Notes and communications
- Timestamped activity log

### Tasks
- Callbacks
- Meetings
- Follow-up reminders
- Calendar integration

### Outcomes
- Call results tracking
- Success metrics
- Activity categorization

### Priority Rules
- Configurable scoring weights
- Urgency calculations
- Data quality factors

## 🔧 Configuration

### Database Configuration (`database_config.json`)

```json
{
  "use_mongodb": true,
  "mongodb_uri": "mongodb://localhost:27017/",
  "database_name": "vstudio_crm",
  "csv_backup_enabled": true,
  "auto_migrate": false
}
```

### Environment Variables (`.env`)

```bash
# MongoDB Settings
USE_MONGODB=true
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=vstudio_crm

# For MongoDB Atlas (cloud)
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

## 🏗️ Priority Views

MongoDB mode enables advanced contact prioritization:

- **Today**: Contacts with tasks due today
- **Overdue**: Past-due callbacks and meetings
- **Hot Leads**: Recently engaged contacts
- **New**: Uncontacted leads
- **All Active**: Complete active contact list

## 📈 Data Migration

### Automatic Migration
When first loading a CSV with `auto_migrate: true`:
1. CSV data is imported to MongoDB
2. Notes are parsed into interaction records
3. Callbacks/meetings become task records
4. Original CSV is backed up

### Manual Migration
```bash
# Migrate specific CSV file
python setup_mongodb.py --csv contacts.csv

# Check migration status
python -c "
from database import CRMDataManager, DatabaseConfig
config = DatabaseConfig()
config.use_mongodb = True
db = CRMDataManager(config)
contacts = db.get_contacts()
print(f'Total contacts: {len(contacts)}')
"
```

## 💾 Data Export

Export MongoDB data back to CSV:

```python
from database import CRMDataManager, DatabaseConfig

config = DatabaseConfig()
config.use_mongodb = True
db = CRMDataManager(config)

# Export all contacts
db.export_to_csv("exported_contacts.csv")
```

## 🔍 Advanced Queries

The MongoDB backend supports complex queries:

```python
# Get contacts with specific status
contacts = db.get_contacts(status_filter="callback")

# Get prioritized contacts
contacts = db.get_contacts(sort_by="priority_score", limit=10)

# Get today's priority contacts
today_contacts = db.get_priority_view_data("today")
```

## 🛠️ Troubleshooting

### MongoDB Connection Issues

1. **Check if MongoDB is running:**
```bash
python setup_mongodb.py --check-only
```

2. **Start MongoDB manually:**
```bash
# For systemd systems
sudo systemctl start mongod

# Manual start
mongod --dbpath /tmp/mongodb_data --port 27017
```

3. **Check logs:**
```bash
# System MongoDB logs
sudo journalctl -u mongod

# Manual MongoDB logs
tail -f /tmp/mongodb.log
```

### Data Issues

1. **Reset database:**
```bash
# Drop and recreate database
python -c "
from mongodb_schema import CRMDatabase
db = CRMDatabase()
db.connect()
db.client.drop_database('vstudio_crm')
"
python setup_mongodb.py --csv your_data.csv
```

2. **Export data before reset:**
```bash
python -c "
from database import CRMDataManager, DatabaseConfig
config = DatabaseConfig()
config.use_mongodb = True
db = CRMDataManager(config)
db.export_to_csv('backup_export.csv')
"
```

### Performance Issues

1. **Check indexes:**
```python
from mongodb_schema import CRMDatabase
db = CRMDatabase()
db.connect()
db.create_indexes()  # Recreate indexes
```

2. **Check database size:**
```bash
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
stats = client['vstudio_crm'].command('dbstats')
print(f'Database size: {stats[\"dataSize\"]/1024/1024:.2f} MB')
"
```

## 🔄 Switching Between Modes

### Switch to MongoDB Mode
```bash
# Update configuration
python -c "
import json
config = json.load(open('database_config.json'))
config['use_mongodb'] = True
json.dump(config, open('database_config.json', 'w'), indent=2)
"
```

### Switch to CSV Mode
```bash
# Update configuration
python -c "
import json
config = json.load(open('database_config.json'))
config['use_mongodb'] = False
json.dump(config, open('database_config.json', 'w'), indent=2)
"
```

## 📊 Monitoring

Monitor your MongoDB CRM:

```python
# Check database statistics
from database import CRMDataManager, DatabaseConfig

config = DatabaseConfig()
config.use_mongodb = True
db = CRMDataManager(config)

contacts = db.get_contacts()
new_contacts = db.get_priority_view_data("new")
today_contacts = db.get_priority_view_data("today")

print(f"Total Contacts: {len(contacts)}")
print(f"New Contacts: {len(new_contacts)}")
print(f"Today's Tasks: {len(today_contacts)}")
```

## 🚀 Next Steps

1. **Customize Priority Scoring**: Modify weights in the database
2. **Add Custom Fields**: Extend the schema for your needs
3. **Create Reports**: Query the database for analytics
4. **Automate Backups**: Set up regular CSV exports
5. **Scale Up**: Move to MongoDB Atlas for cloud hosting

## 📚 Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [PyMongo Tutorial](https://pymongo.readthedocs.io/)
- [MongoDB Atlas](https://www.mongodb.com/atlas) (Cloud hosting)

---

Your MongoDB-backed VStudio CLI CRM is now ready for advanced customer relationship management! 🎉