# Priority Features Guide

## Overview

The VStudio CLI now includes powerful priority features for managing past-due and scheduled calls. These features help you focus on the most urgent contacts and stay organized with your daily schedule.

## Quick Start

### Using Test Mode
```bash
# Start with test database (recommended for development)
python vstudio_cli.py --testing
```

### Using Production Mode
```bash
# Start with production database
python vstudio_cli.py
```

## Priority Views

The CLI includes four priority views accessible via hotkeys:

### 🟢 Today's Schedule (Press `t`)
- Shows all callbacks and meetings due today
- Sorted by time (earliest first)
- Displays meeting times in header
- Shows "📞 Due today" or "📅 Meeting today at time"

### 🔴 Overdue Items (Press `d`)
- Shows all past-due callbacks and meetings
- Sorted by urgency (most overdue first)
- Color-coded urgency indicators:
  - 🔥 1 day overdue
  - ⚠️  2-3 days overdue  
  - ‼️  4+ days overdue

### 🟡 New Contacts (Press `n`)
- Shows contacts that have never been called
- Sorted alphabetically by company
- Perfect for first outreach campaigns

### 🔵 All Contacts (Press `a`)
- Shows all active contacts
- Default view when starting the application
- Sorted by company name

## Urgency Indicators

The system automatically shows urgency information in the record header:

- **🔥 1 day overdue** - Critical priority
- **⚠️  2 days overdue** - High priority  
- **‼️  5 days overdue** - Maximum urgency
- **📞 Due today** - Today's callback
- **📅 Meeting today at 2:30 PM** - Today's scheduled meeting

## Hotkey Navigation

While in any view, use these hotkeys:

### View Switching
- `t` - Switch to Today's schedule
- `d` - Switch to Overdue items
- `n` - Switch to New contacts
- `a` - Switch to All contacts

### Standard Navigation
- `1` - Make call
- `2` - Send text message
- `3` / `j` / `Enter` - Next record
- `k` / `↑` - Previous record
- `4` - Delete/archive record
- `5` - Add note
- `/` - Search
- `o` - Record call outcome
- `q` - Quit

## Test Database

The CLI includes a comprehensive test database with realistic scenarios:

- **17 items scheduled for today** (callbacks and meetings)
- **13 overdue items** (1-7 days past due)
- **15 new contacts** (never contacted)
- **50 total contacts** with Canadian company data

### Setting up Test Data
```bash
# Generate fresh test data
python create_test_data.py

# Import to test database  
python -c "
from setup_test_db import setup_test_database
setup_test_database()
"
```

## Best Practices

### Daily Workflow
1. Start with **Overdue view** (`d`) - Handle urgent items first
2. Move to **Today view** (`t`) - Work through today's schedule  
3. Process **New contacts** (`n`) when you have time
4. Use **All view** (`a`) for general browsing

### Priority Management
- Red indicators (🔥 ⚠️ ‼️) require immediate attention
- Green indicators (📞 📅) are due today
- Focus on most overdue items first in overdue view
- Schedule follow-ups to avoid items becoming overdue

### Testing and Development
- Always use `--testing` flag when developing new features
- Test database is completely separate from production data
- Safe to experiment with call outcomes and status changes
- Regenerate test data anytime with `create_test_data.py`

## Technical Details

### Database Integration
- Utilizes MongoDB priority views from the database layer
- Real-time sorting based on urgency and time
- Maintains CSV compatibility for existing workflows
- Automatic view switching preserves current record context

### Performance
- Views are loaded on-demand for fast switching
- Intelligent sorting reduces time to find urgent items
- Database indexes optimized for priority queries
- Minimal memory footprint with lazy loading

## Troubleshooting

### No Items in Priority Views
- Ensure MongoDB is running: Check if test database exists
- Verify test data import: Run `python create_test_data.py` again
- Check database connection: Look for connection error messages

### View Switching Not Working
- Priority views require database mode (not CSV-only)
- Hotkeys only appear when `self.db_manager` is available
- Try restarting with `--testing` flag

### Urgency Indicators Not Showing
- Verify date formats in database match ISO format
- Check that callback_on and meeting_at fields have valid dates
- Test data generator creates proper date formats automatically

## Examples

### Typical Daily Session
```
$ python vstudio_cli.py --testing
🧪 TESTING MODE - Using test database (vstudio_crm_test)

# Press 'd' to see overdue items
[Shows: "Brian Harris - ‼️  5 days overdue"]

# Press 't' to see today's schedule  
[Shows: "📅 Meeting today at 2:30 PM - Jennifer Smith"]

# Press 'n' to see new leads
[Shows: "Sarah Johnson - TechStart Solutions - New contact"]
```

This priority system transforms the CLI from a simple contact browser into a powerful workflow management tool, ensuring no important follow-ups fall through the cracks!