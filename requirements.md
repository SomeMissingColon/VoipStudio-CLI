vstudio-cli — Requirements

Working name: vstudio-cli
Purpose: A keyboard-first CLI/TUI that runs in a shell as a simple Python script. It walks a caller through a CSV list, places and monitors calls via VoIPstudio’s REST API, captures standardized outcomes, schedules callbacks/meetings to Google Calendar, and persists everything back to CSV with backups and an archive.

1. Scope & Objectives
In scope

Load a CSV file with at least a telephone column.

Present the current row in a readable, line-by-line detail view.

Keyboard actions: Call, Text (optional), Next, Delete, Add note.

Monitor live calls and auto-prompt for outcomes when a call ends.

Persist notes, statuses, and dates to the CSV (with backups and archives).

Create Google Calendar events for callbacks and meetings.

Use VoIPstudio’s REST API for call origination, monitoring, updates, and termination (API-first approach).

Out of scope (v1)

Inbound call handling.

Multi-user concurrency or shared editing/locking.

Full CRM pipeline management or analytics beyond simple counters.

2. Users & Runtime Environment

Primary user: Solo SDR/owner-operator calling from a terminal.

Runtime: Single Python script, executed from a shell. No background services.

OS: Linux (primary), macOS (secondary), Windows (best-effort).

Connectivity: Internet is required for VoIPstudio API and Google Calendar. The app should degrade gracefully when offline and retry queued operations later.

3. Input Format & Data Model
3.1 Input CSV

Required column: telephone

Optional: name, company, title, city, email, source, notes

Additional columns must be preserved and displayed where space allows.

3.2 Managed columns (auto-created if missing)

status (one of: new, bad_number, no_answer, callback, meeting_booked, do_not_call, deleted)

last_call_at (timestamp)

callback_on (date)

meeting_at (timestamp)

notes (timestamped entries; consistent order)

gcal_callback_event_id (string; nullable)

gcal_meeting_event_id (string; nullable)

gcal_calendar_id (string; nullable)

external_row_id (stable identifier derived from CSV path + row content)

3.3 Archives & backups

Archive CSV: Rows removed from the active list (deleted, bad number, do-not-call) are appended here with archived_at.

Backups: Rotating timestamped backups, created prior to every write to the active CSV.

4. Shell UX & Behaviors
4.1 Launch & load

On start, prompt for the CSV path (or accept as a CLI argument).

Validate headers and scan for obvious issues (blanks, dupes).

Normalize phone numbers to an internationally recognizable format when possible.

Present the first valid row.

4.2 Record view (TUI)

Header: Current index and total (e.g., “Record 12/243”), status, last_call_at, callback_on if present.

Body: Each visible field on its own line (Name, Company, Telephone, Email, Notes).

Footer: Hotkeys: 1 Call · 2 Text · 3 Next · 4 Delete · 5 Add note · ↑/k prev · ↓/j next · / search · q Quit

4.3 Navigation & search

Previous/next via arrows or vim-style keys.

Jump to first/last quickly.

Search by telephone, name, company, or email; repeatable next/previous match.

5. Primary actions
5.1 Call (1)

Initiates an outbound call to the current row’s telephone via VoIPstudio’s REST API.

Shows a live call monitor panel: dialing → ringing → connected → ended; simple timer visible.

If live state cannot be detected, provide a manual “End call” hotkey.

5.2 Text (2)

Optional. If SMS is available (external provider), open a quick text compose; on send, append a timestamped note. If unavailable, disable with an explanatory hint.

5.3 Next (3)

Advance to the next visible row without changing data.

5.4 Delete (4)

Move the row to the archive and set status=deleted. Advance to next.

5.5 Add note (5)

Prompt for free-text; append a timestamped entry to notes.

6. Post-call outcomes (auto-prompt when call ends)

Bad number

Set status=bad_number, move row to archive, clear any scheduled dates, cancel linked calendar events.

No answer

Set status=no_answer, append “called {date} ~ no answer” to notes. Keep row in place.

Call back

Prompt for a due date (allow relative inputs).

Set callback_on, status=callback.

Create a Google Calendar event and store the resulting identifier.

Meeting booked

Prompt for a specific date/time.

Set meeting_at, status=meeting_booked.

Create a Google Calendar event and store the resulting identifier.

Do not call back

Set status=do_not_call, move row to archive, cancel linked calendar events.

Default outcome if Enter is pressed without a selection: No answer.

7. VoIPstudio integration — methodology (API-first, shell-friendly)

All interactions use the official REST API; no browser automation. The base URL format and authentication model are defined in VoIPstudio’s Introduction. A user token (“API Key”) is required and must be sent on each request using the documented header. Tokens can be obtained either via a login flow or created in the Web Dashboard as long-lived API keys; idle tokens expire unless you use API tokens with an expiry policy suitable for your workflow. The API uses resource-oriented endpoints and JSON responses. 
VoIPstudio

7.1 Authentication flow

Obtain a user token once per operator (either by logging in through the documented login endpoint or by generating an API key in the Web Dashboard).

For every API request, include the X-Auth-Token header with the user token per the “Making requests” guidance in the Introduction.

If short-lived tokens are in use, either perform light periodic API traffic or create longer-expiry API keys using the documented token issuance endpoint to avoid frequent re-authentication. 
VoIPstudio

7.2 Placing an outbound call

Use the Calls resource to create a new call, providing the destination number in E.164 format. Supply the originating user and caller ID when relevant to your account setup. Capture the returned call identifier for monitoring. 
VoIPstudio

7.3 Monitoring a live call

Poll the specific call by ID until the state indicates the call has ended. Use a conservative polling interval to balance responsiveness and API usage.

As a fallback during transient errors, you may query the collection of live calls and reconcile by the call identifier or destination.

Where permitted and useful, manage recording/monitoring state, answer certain call states, attach an action link for CRM context, or transfer an ongoing call using the update endpoint on the Call resource. 
VoIPstudio

7.4 Ending a call from the shell

If the operator ends the call from the TUI while the call is still live in the network, terminate the live call using the dedicated termination endpoint on the Call resource. 
VoIPstudio

7.5 Post-call details (history)

After the live call ends, retrieve Call Detail Records (CDRs) through the History module to obtain billable seconds, final disposition, and timestamps for reporting or notes. Filtering and paging are supported as documented in the Introduction (filters and pager). 
VoIPstudio
+1

8. Google Calendar integration — methodology (no code)

Authorization: Use OAuth 2.0 to access a target calendar with event-level scope. Persist tokens securely and refresh as needed.

Callback events: For “Call back,” create an event titled accordingly with contact name/number, scheduled on the chosen date at a configurable default time, with a short default duration. Include telephone, a summary of recent notes, and a reference to the CSV row in the description. Add the contact as an attendee only if an email exists and invitations are enabled.

Meeting events: For “Meeting booked,” create an event at the specified date/time with a standard meeting duration. Use the same description pattern and optional attendee handling.

Idempotency: Derive a stable external identifier from the row and event type. Before creating, check for an existing event with that identifier; when rescheduling, update; when archiving or marking do-not-call, cancel the event.

Offline queue: If event operations fail due to connectivity/auth, queue them locally and retry automatically on next launch.

9. Dates, times, and time zones

Accept natural, concise input for dates and times (including relative forms like “+3 days”), show the parsed interpretation for confirmation, and store with timezone offsets.

Display all times in the local system timezone.

10. Visibility, ordering, and filters

Hide terminal statuses (deleted, do_not_call, bad_number) from active navigation.

Default ordering is the original CSV order.

Optional filtered views: “due callbacks today,” “overdue,” and “meetings this week.”

11. Persistence & safety

Atomic writes: write to a temporary file, then replace the CSV.

Rotating backups prior to every write.

Archive retains full data for audit.

Session-local undo for recent actions when feasible.

Crash recovery restores cursor position and replays any queued calendar operations.

12. Security & privacy

Store VoIPstudio tokens and Google tokens securely (OS keychain preferred; if not available, restrict file permissions).

Mask PII in logs (e.g., telephone numbers, emails).

Ensure any recording/monitoring features comply with local laws and account policies.

13. Error handling

CSV issues (missing telephone, malformed headers, locked files) produce clear, non-destructive errors.

Phone normalization errors prompt for correction with an override path.

VoIPstudio API failures trigger re-auth prompts when appropriate and benefit from retry with backoff; live-call monitoring can fall back from the per-ID endpoint to the live list during transient faults.

Calendar failures queue operations and surface a retry banner in the TUI.

Date/time inputs re-prompt with helpful validation messages.

14. Performance & reliability

Fast startup in a shell.

Live call polling at a conservative cadence to avoid noisy API usage.

The TUI remains responsive while awaiting call end events.

15. Telemetry & logging

Local log entries for: app lifecycle, CSV paths, action selections, call attempts/outcomes (PII masked), calendar ops, and CSV write results.

No external telemetry enabled by default.

16. Acceptance criteria

Load & display: A CSV containing only telephone loads; the first row renders clearly; invalid CSVs yield actionable, non-destructive errors.

Call flow: Selecting Call initiates a VoIPstudio call; the monitor shows state changes; on end, the outcome menu appears automatically.

Outcomes: Each outcome updates CSV fields precisely as specified; Callback and Meeting create calendar events; Bad number and Do-not-call archive the row and cancel any linked events.

Notes & deletes: Add note appends a timestamped entry visible in the record view; Delete moves the row to the archive with correct status.

Safety: Every write is atomic with a rotation backup; on restart, the app resumes at the previous record and processes any queued calendar operations.

VoIPstudio specifics: Outbound calls are created using the Calls resource with E.164 destinations; live status is obtained by querying the specific call or the live calls list; updates (answer/transfer/monitoring) and termination use the documented endpoints; final metrics are retrievable from History/CDRs. 
VoIPstudio
+1

17. Non-functional requirements

Usability: Keyboard-first controls, predictable keybindings, clear prompts that minimize friction.

Accessibility: High-contrast terminal theme and legible typography.

Maintainability: Modular adapters for calls (VoIPstudio), SMS (optional), and calendar; clear separation of concerns.

Portability: Minimal dependencies; runs as a simple Python script in a shell across major platforms.

18. Tech stack (shell-friendly)

Language & runtime: Python 3.x executed directly from a shell, packaged as a single script or simple entrypoint.

Terminal UI: A lightweight Python TUI framework suitable for keyboard-first flows.

HTTP client: A standard Python HTTP/JSON client appropriate for REST APIs.

CSV handling: A standard Python CSV reader/writer supporting atomic replace patterns.

Time parsing: A Python library that understands natural language date/time where possible.

Secure storage: OS-level keychain where available; otherwise a restricted-permissions file for tokens.

Cross-platform considerations: Minimal, widely available dependencies only.

19. Open questions

Preferred default in VoIPstudio: use Calls for all origination, or mix in Webcalls/Leadcalls for specific account setups? 
VoIPstudio

Should recording/monitor control be included in v1 or deferred? 
VoIPstudio

Should callbacks use a dedicated calendar separate from meetings?

Are attendee invitations enabled by default when email exists?

Preferred default durations and reminders for callbacks and meetings?

20. References (methodology basis)

Introduction: Base URL, authentication model, token lifetimes, request header, pagination, and filters. 
VoIPstudio

Calls: Create outbound calls; list and query live calls; get call by ID; update (answer/transfer/monitoring, action links); terminate. 
VoIPstudio

History: Call Detail Records (CDRs) and related post-call data. 
VoIPstudio
