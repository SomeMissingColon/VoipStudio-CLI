# VStudio CLI - Advanced CRM & VoIP Management System

A powerful keyboard-first CLI/TUI for VoIPstudio call management with comprehensive CRM lifecycle tracking. This professional tool helps sales teams and customer service representatives manage contacts, place calls via VoIPstudio's REST API, track complete sales pipelines, and integrate with MongoDB for advanced data management.

## 🚀 Latest Features (v2.0)

### ✅ Complete CRM Lifecycle Management
- **Close-Won/Close-Lost Tracking**: Full sales pipeline with dedicated client and cemetery views
- **Interactive Dashboard**: Real-time statistics and quick access to all CRM functions
- **Quick Field Editing**: Edit any contact field on-the-go with comprehensive history tracking
- **Promote/Demote Commands**: Instant status changes from prospect to client or cemetery
- **Calendar Integration**: Interactive monthly calendar with event management

### 📊 Advanced Views & Navigation
- **Clients View** (`c` key): Manage successful deals and ongoing client relationships
- **Cemetery View** (`z` key): Analyze lost deals for continuous improvement
- **Dashboard** (`h` key): Central hub with statistics and quick actions
- **Calendar View** (`l` key): Interactive monthly calendar with callbacks and meetings

![Contact Management Interface](image-1-contact-view.png)
*Main contact processing interface with comprehensive hotkey navigation*

![Interactive Calendar](image-2-calendar-view.png) 
*Monthly calendar view showing scheduled callbacks and meetings*

![CRM Dashboard](image-3-dashboard-view.png)
*Interactive dashboard with statistics and quick actions*

## 🎯 Core Features

### **VoIP & Call Management**
- **VoIP Integration**: Place and monitor calls via VoIPstudio REST API
- **Call Outcome Tracking**: Automatic redirect to outcome selection after calls
- **Real-time Call Monitoring**: Live call status with duration tracking
- **Call History**: Complete audit trail of all call activities

### **Database & Storage**
- **MongoDB Integration**: Advanced database operations with full CRUD support
- **CSV Compatibility**: Seamless import/export with traditional CSV workflows  
- **Edit History Tracking**: Complete audit trail with revert capabilities
- **Data Safety**: Atomic writes, rotating backups, and crash recovery

### **Contact Lifecycle Management**
- **Status Progression**: New → Callback → Meeting → Close-Won/Close-Lost
- **Field Editing**: Quick modification of any contact field with validation
- **Contact Creation**: Add new contacts directly from dashboard
- **Priority Views**: Today's schedule, overdue items, new contacts

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MongoDB (local or remote instance)
- VoIPstudio account with API access

### Installation
```bash
# Clone the repository
git clone https://github.com/SomeMissingColon/VoipStudio-CLI.git
cd VoipStudio-CLI

# Install dependencies
pip install -r requirements.txt

# Set up MongoDB configuration
cp database_config.json.example database_config.json
# Edit database_config.json with your MongoDB settings
```

### Database Configuration

Create `database_config.json`:
```json
{
  "use_mongodb": true,
  "mongodb_uri": "mongodb://localhost:27017/",
  "database_name": "vstudio_crm",
  "csv_backup_enabled": true,
  "auto_migrate": true
}
```

### First Run Setup
```bash
# Launch the application
python3 vstudio_cli.py

# You'll be prompted to configure:
# - VoIPstudio API token (stored securely)
# - Database connection
# - Initial contact import (optional)
```

## 🎮 Usage Guide

### Main Interface Navigation

**Primary Actions:**
- `1` - Make call (with automatic outcome redirect)
- `2` - Send text message
- `3` - Next contact  
- `4` - Archive contact
- `5` - Add notes
- `↑/k` - Previous contact
- `↓/j` - Next contact
- `/` - Search contacts
- `q` - Quit application

**CRM Management:**
- `e` - Edit current contact fields
- `p` - Promote to client (close-won)
- `m` - Move to cemetery (close-lost)
- `o` - Handle call outcomes

**View Navigation:**
- `t` - Today's schedule
- `d` - Overdue items  
- `n` - New contacts
- `a` - All contacts
- `c` - Clients (close-won)
- `z` - Cemetery (close-lost)

**System Access:**
- `h` - Dashboard (statistics and actions)
- `l` - Calendar view (interactive monthly view)

### Dashboard Actions

From the dashboard (`h` key), you can:
- `n` - Create new contact
- `l` - Access calendar view  
- `v/c/z/t/d` - Switch to different contact views
- `r` - Refresh statistics
- `s` - Start working with contacts

### Contact Lifecycle Workflow

1. **Lead Generation**: Import or create new contacts (status: `new`)
2. **Initial Contact**: Make calls, update status to `callback` or `meeting_booked`
3. **Follow-up Phase**: Use calendar for scheduling and tracking
4. **Decision Point**: 
   - Success → Promote to client (`p` key, status: `close_won`)
   - Failure → Move to cemetery (`m` key, status: `close_lost`)
5. **Ongoing Management**: Use clients and cemetery views for analysis

### Field Editing (`e` key)

When editing a contact, you can modify:
1. Name
2. Company  
3. Phone Number
4. Email
5. Title
6. Address
7. City
8. Status
9. Notes
10. Callback Date
11. Meeting Date/Time

All changes are tracked with complete edit history and revert capability.

## 📋 Contact Statuses

- `new` - Never contacted before
- `callback` - Scheduled for follow-up call
- `meeting_booked` - Meeting scheduled
- `no_answer` - Attempted contact, no response
- `close_won` - Successfully closed deal (appears in Clients view)
- `close_lost` - Lost deal (appears in Cemetery view)  
- `do_not_call` - Do not contact again
- `bad_number` - Invalid phone number

## 🔧 Configuration

### Database Options

**MongoDB (Recommended)**:
```json
{
  "use_mongodb": true,
  "mongodb_uri": "mongodb://localhost:27017/",
  "database_name": "vstudio_crm"
}
```

**CSV Mode (Legacy)**:
```json
{
  "use_mongodb": false,
  "csv_backup_enabled": true,
  "csv_export_path": "contacts_export.csv"
}
```

### API Configuration

Configure VoIPstudio API access:
1. Log into VoIPstudio dashboard
2. Go to Settings → API  
3. Generate API token
4. Token is stored securely in OS keychain

## 📊 Data Management

### MongoDB Collections
- `contacts` - Main contact database
- `edit_history` - Complete audit trail of changes
- `interactions` - Call and communication history  
- `tasks` - Follow-up tasks and reminders

### CSV Import/Export
- Import existing CSV files with automatic field mapping
- Export to CSV for backup or external analysis
- Automatic backup rotation with timestamps

### Edit History & Revert
- Every field change is tracked with timestamp
- View complete edit history (`h` in edit mode)  
- Revert any change with confirmation
- Audit trail for compliance and analysis

## 🛡️ Security & Safety

### Data Protection
- API tokens stored in OS keychain (never in plaintext)
- PII masking in logs
- Restricted file permissions on backups
- MongoDB connection encryption support

### Backup & Recovery  
- Atomic database operations
- Automatic backup rotation
- Crash recovery with position restoration
- Archive system for deleted records

### Compliance Features
- Complete audit trail for all changes
- Call history tracking
- Data retention policies
- Export capabilities for compliance reporting

## 🔮 Future Roadmap

### Priority: Cloud Database Connectivity

**Primary Goal**: Enable multi-device synchronization through cloud database connectivity

**Planned Features**:
- ☁️ **MongoDB Atlas Integration**: Connect to cloud-hosted MongoDB for device synchronization
- 🔄 **Real-time Sync**: Live updates across multiple devices and team members
- 👥 **Team Collaboration**: Multi-user access with role-based permissions
- 📱 **Mobile Compatibility**: Cross-platform access from any device
- 🌐 **Web Dashboard**: Browser-based interface for remote access
- 🔐 **Enhanced Security**: Cloud-grade encryption and authentication
- 📈 **Analytics Dashboard**: Advanced reporting and team performance metrics
- 🔔 **Notifications**: Real-time alerts and task assignments
- 📧 **Email Integration**: Automatic follow-up email capabilities
- 🤖 **AI Insights**: Predictive analytics for conversion optimization

### Technical Improvements
- GraphQL API for efficient data queries
- Offline mode with automatic sync when connected
- Advanced search with full-text indexing
- Bulk operations for large contact lists
- Integration with popular CRM platforms
- Advanced reporting and dashboard customization

## 🧪 Testing

The project includes comprehensive test suites:

```bash
# Run feature tests
python3 test_complete_features.py
python3 test_dashboard_features.py  
python3 test_calendar_restored.py

# Run demo scripts
python3 demo_new_features.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow existing code patterns
- Add comprehensive logging
- Include test coverage for new features
- Update documentation for user-facing changes
- Maintain backward compatibility where possible

## 📄 License

This project is intended for legitimate business use only - customer service, sales calls, and other authorized communications with proper consent.

## 🆘 Support & Troubleshooting

### Common Issues

**MongoDB Connection Issues**:
```bash
# Check MongoDB service
sudo systemctl status mongod

# Test connection
python3 -c "from pymongo import MongoClient; print(MongoClient().admin.command('ping'))"
```

**API Authentication Issues**:
- Verify VoIPstudio token is valid
- Check token permissions in VoIPstudio dashboard
- Ensure internet connectivity

**Performance Issues**:
- Index MongoDB collections for large datasets
- Enable query optimization
- Consider cloud database for better performance

### Debug Mode
```bash
# Enable verbose logging
python3 vstudio_cli.py --debug

# View specific logs
tail -f vstudio.log
```

### Getting Help
- Create GitHub issues for bugs
- Check existing issues for solutions  
- Review the comprehensive test suite for usage examples
- Consult the edit history feature for data recovery

---

**Built with ❤️ for sales teams who need powerful, keyboard-driven CRM tools**