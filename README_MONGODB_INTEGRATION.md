# VStudio CLI CRM - MongoDB Integration

Your VStudio CLI application has been successfully upgraded to use MongoDB as the primary database backend! 🎉

## 🚀 What Changed

The application now **defaults to using MongoDB** instead of requiring a CSV file. This transforms your simple VoIP dialer into a full-featured CRM system.

### Before (CSV-only)
```bash
python vstudio_cli.py contacts.csv  # Required CSV file
```

### Now (MongoDB-first)
```bash
python vstudio_cli.py              # Uses MongoDB automatically
./start_crm.sh                     # Easy startup script
```

## 📊 New Features

### 🗄️ **MongoDB Backend**
- Automatic database connection on startup
- Full interaction history tracking  
- Advanced contact prioritization
- Real-time data persistence
- Crash-safe operations

### 🔄 **Hybrid Mode**
- MongoDB by default
- CSV fallback if database unavailable
- Force CSV mode with `--csv-only` flag
- Import/export between formats

### 📈 **CRM Capabilities**
- Contact lifecycle management
- Interaction timeline
- Task scheduling (callbacks/meetings)
- Priority scoring and views
- Audit trail

## 🎯 Quick Start Guide

### 1. **Start the CRM** (Easiest)
```bash
./start_crm.sh
```
This handles everything: MongoDB startup, database checks, and launches the CRM.

### 2. **Manual Startup**
```bash
# Ensure MongoDB is running
python setup_mongodb.py --check-only

# Start the CRM
python vstudio_cli.py
```

### 3. **With Options**
```bash
# Debug mode
python vstudio_cli.py --debug

# Force CSV mode
python vstudio_cli.py --csv-only contacts.csv

# With specific CSV file
python vstudio_cli.py my_contacts.csv
```

## 📋 Application Behavior

### **Database Mode (Default)**
- ✅ Connects to MongoDB automatically
- ✅ Loads contacts from database  
- ✅ Saves changes in real-time
- ✅ Full interaction history
- ✅ Advanced CRM features

### **CSV Fallback Mode**
- ⚠️ Used when MongoDB unavailable
- 📄 Prompts for CSV file if none provided
- 💾 Saves to CSV with backups
- 🔄 Limited CRM functionality

### **Forced CSV Mode**
```bash
python vstudio_cli.py --csv-only contacts.csv
```
- 📄 Bypasses MongoDB entirely
- 🔄 Uses original CSV workflow
- 💾 For compatibility/backup scenarios

## 🛠️ Database Management

### **View Database Contents**
```bash
# Quick stats
python db_stats.py

# Interactive explorer
python explore_db.py

# Raw MongoDB access
python -c "
from database import CRMDataManager, DatabaseConfig
config = DatabaseConfig()
config.use_mongodb = True
db = CRMDataManager(config)
contacts = db.get_contacts()
print(f'Found {len(contacts)} contacts')
"
```

### **Import New CSV Data**
```bash
# Import and migrate CSV to database
python setup_mongodb.py --csv new_contacts.csv
```

### **Export Database to CSV**
```bash
python -c "
from database import CRMDataManager, DatabaseConfig
config = DatabaseConfig()  
config.use_mongodb = True
db = CRMDataManager(config)
db.export_to_csv('exported_contacts.csv')
print('Database exported to exported_contacts.csv')
"
```

## 📊 Data Structure

Your data is now organized in MongoDB collections:

- **`contacts`**: Primary contact information
- **`interactions`**: All calls, texts, and notes
- **`tasks`**: Callbacks and meetings
- **`outcomes`**: Call results and categorization
- **`priority_rules`**: Scoring configuration
- **`calendar_map`**: Calendar sync tracking
- **`user_preferences`**: Settings and preferences  
- **`audit_log`**: Change history

## 🔧 Configuration

### **Database Settings** (`database_config.json`)
```json
{
  "use_mongodb": true,
  "mongodb_uri": "mongodb://localhost:27017/",
  "database_name": "vstudio_crm",
  "csv_backup_enabled": true,
  "auto_migrate": false
}
```

### **Environment Variables** (`.env`)
```bash
USE_MONGODB=true
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=vstudio_crm
```

## 🎛️ Command Line Options

```bash
# Show help
python vstudio_cli.py --help

# Available options:
python vstudio_cli.py [csv_file]     # Optional CSV file
                     [-v|--verbose]  # Verbose logging  
                     [-d|--debug]    # Debug mode
                     [--csv-only]    # Force CSV mode
```

## 🔍 Troubleshooting

### **MongoDB Not Running**
```bash
# Check status
python setup_mongodb.py --check-only

# Start manually  
mongod --dbpath /tmp/mongodb_data --port 27017 --bind_ip 127.0.0.1
```

### **Database Connection Issues**
```bash
# Reset database configuration
python -c "
import json
config = {
    'use_mongodb': True,
    'mongodb_uri': 'mongodb://localhost:27017/',
    'database_name': 'vstudio_crm'
}
json.dump(config, open('database_config.json', 'w'), indent=2)
"
```

### **Force CSV Mode**
```bash  
# Temporary override
python vstudio_cli.py --csv-only your_file.csv

# Permanent override
python -c "
import json  
config = json.load(open('database_config.json'))
config['use_mongodb'] = False
json.dump(config, open('database_config.json', 'w'), indent=2)
"
```

## 📈 Migration Status

Your existing CSV data has been migrated:
- ✅ Contacts imported to MongoDB
- ✅ Notes converted to interactions  
- ✅ Callbacks/meetings converted to tasks
- ✅ Original CSV backed up
- ✅ Indexes created for performance

## 🚀 Next Steps

1. **Start using the CRM**: `./start_crm.sh`
2. **Explore your data**: `python explore_db.py`  
3. **Customize priority rules**: Edit in database
4. **Set up cloud MongoDB**: Use MongoDB Atlas
5. **Create automated backups**: Schedule CSV exports

## 📚 Additional Resources

- **Database Explorer**: `python explore_db.py`
- **Quick Stats**: `python db_stats.py`
- **Setup Guide**: `MONGODB_SETUP.md`
- **Schema Documentation**: `mongodb_schema.py`

---

🎉 **Your VoIP dialer is now a full-featured CRM with MongoDB backend!** 

Start with: `./start_crm.sh`