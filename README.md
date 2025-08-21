# VStudio CLI

A keyboard-first CLI/TUI for VoIPstudio call management. This tool helps sales professionals and customer service representatives manage CSV-based contact lists, place calls via VoIPstudio's REST API, track outcomes, and schedule follow-ups in Google Calendar.

## Features

- **CSV Management**: Load contact lists with automatic backup and archiving
- **VoIP Integration**: Place and monitor calls via VoIPstudio REST API
- **Outcome Tracking**: Capture call results and schedule callbacks/meetings
- **Google Calendar**: Automatic event creation for callbacks and meetings
- **Keyboard Navigation**: Efficient keyboard-first interface
- **Data Safety**: Atomic writes, rotating backups, and crash recovery

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
```bash
python vstudio_cli.py contacts.csv
```

### CSV Format

Required column:
- `telephone` - Phone number

Optional columns:
- `name`, `company`, `title`, `city`, `email`, `source`, `notes`

The application will automatically add these managed columns:
- `status`, `last_call_at`, `callback_on`, `meeting_at`, `notes`
- `gcal_callback_event_id`, `gcal_meeting_event_id`, `gcal_calendar_id`
- `external_row_id`

### Configuration

On first run, you'll be prompted for:
- VoIPstudio API token (stored securely in OS keychain)
- Google Calendar credentials (OAuth flow)

### Keyboard Shortcuts

- `1` - Make call
- `2` - Send text (if available)
- `3` - Next record
- `4` - Delete record (archive)
- `5` - Add note
- `↑/k` - Previous record
- `↓/j` - Next record
- `/` - Search
- `q` - Quit

### Call Outcomes

After each call, you can select:
1. **Bad number** - Archives record, cancels calendar events
2. **No answer** - Keeps record active, adds note
3. **Call back** - Schedules callback, creates calendar event
4. **Meeting booked** - Schedules meeting, creates calendar event
5. **Do not call back** - Archives record, cancels calendar events

## API Requirements

### VoIPstudio API Token

Get your API token from:
1. Log into VoIPstudio web dashboard
2. Go to Settings → API
3. Generate a new API token

### Google Calendar Setup

For Google Calendar integration:
1. Create a Google Cloud Project
2. Enable the Calendar API
3. Create OAuth 2.0 credentials
4. Download the credentials JSON file

## File Structure

```
/
├── vstudio_cli.py          # Main application
├── requirements.txt        # Python dependencies
├── contacts.csv           # Your contact list
├── archive.csv           # Archived records
└── backups/              # Timestamped CSV backups
    ├── contacts_20240101_120000.csv
    └── ...
```

## Safety Features

- **Atomic Writes**: All CSV updates are atomic to prevent corruption
- **Rotating Backups**: Automatic timestamped backups before each save
- **Archive System**: Deleted records are preserved in archive.csv
- **Graceful Shutdown**: Handles Ctrl+C and terminates active calls
- **Crash Recovery**: Resumes at last position on restart

## Logging

Application logs are written to stdout with timestamp and level:
```
2024-01-01 12:00:00 - INFO - Loading CSV: contacts.csv
2024-01-01 12:00:01 - INFO - Loaded 150 records
```

## Security

- API tokens stored securely in OS keychain
- PII masked in logs (phone numbers, emails)
- OAuth tokens refreshed automatically
- Restricted file permissions on backups

## Troubleshooting

### Common Issues

1. **CSV Loading Errors**
   - Ensure file has 'telephone' column
   - Check file encoding (should be UTF-8)
   - Verify file is not locked by another application

2. **API Connection Issues**
   - Verify API token is correct
   - Check internet connectivity
   - Review VoIPstudio account status

3. **Calendar Integration Issues**
   - Ensure OAuth credentials are valid
   - Check Google Calendar API quota
   - Verify calendar permissions

### Debug Mode

Enable verbose logging:
```bash
python vstudio_cli.py -v contacts.csv
```

## Contributing

This is a single-script application designed for simplicity and portability. When contributing:

1. Maintain single-file architecture
2. Follow existing code style
3. Add appropriate logging
4. Test with various CSV formats
5. Ensure cross-platform compatibility

## License

This project is intended for legitimate business use only - customer service, sales calls, and other authorized communications with proper consent.