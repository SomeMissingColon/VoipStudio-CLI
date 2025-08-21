vstudio-cli — Next Steps Roadmap (Requirements)

Context: Extend the current shell-based Python TUI to support a persistent database, cloud synchronization with S3, containerized distribution for broad compatibility, and richer menus that help users prioritize outreach.

1. Objectives

Database Support

Introduce a local, embedded database as the system of record, while remaining compatible with the existing CSV workflow.

Capture full interaction history (calls, texts, notes, outcomes), scheduling, priorities, and user preferences.

S3 Connectivity

Provide reliable push/pull of data artifacts (database snapshots, CSV imports/exports, archives, logs) to a designated S3 bucket.

Enable optional off-device backup/restore and cross-machine portability.

Containerization

Package the application in a portable container that runs the TUI reliably on modern Linux/macOS/Windows hosts.

Keep setup friction minimal: one container artifact with clear runtime options for storage and credentials.

Prioritization Menus

Add new menu views to plan daily activity and sequence calls intelligently.

Provide a transparent, adjustable scoring model and quick “focus” workflows.

2. Phased Delivery Plan
Phase A — Database Foundation (local-first, CSV compatible)

Add a persistence layer with an embedded database as the primary store.

Implement a one-time CSV import and optional ongoing write-through back to CSV for compatibility.

Normalize entities and introduce a comprehensive audit trail of interactions.

Ship read-only analytics counters (e.g., contacted today, meetings set this week).

Exit criteria

App reads/writes from the database by default; CSV import completes with parity.

Notes, outcomes, and schedules persist across sessions.

No data loss during normal use or on unexpected app termination.

Phase B — S3 Sync (backup, restore, portability)

Add push (backup) and pull (restore) operations to/from S3 with versioning awareness.

Support selective sync of database, archive CSV, logs, and optional exports.

Implement conflict detection and operator prompts (e.g., newer remote vs. local).

Exit criteria

Successful push/pull of a complete workspace to S3 with versioning.

Clear, user-driven conflict resolution.

Optional scheduled reminders to back up (never automatic without consent).

Phase C — Containerization (portable runtime)

Provide a containerized app that opens the TUI in an interactive terminal.

Support mounting a host directory for data and a mechanism to pass credentials at runtime.

Validate cross-platform behavior (Linux, macOS; Windows via supported container runtime).

Exit criteria

App runs interactively in a container on target platforms.

Data is persisted outside the container via a mounted directory.

Basic health and minimal footprint validated.

Phase D — Prioritization Menus & Focus Workflows

Add views for “Today,” “Due callbacks,” “Overdue,” “Hot leads,” “New,” and “Meetings.”

Introduce a priority score and sorting; allow quick overrides (pin/snooze).

Provide Focus Mode to work a curated queue with minimal navigation.

Exit criteria

Users can plan a day in under a minute using built-in views.

Focus Mode presents a sequenced list with keyboard-only actions.

Priority scoring is explainable and adjustable.

3. Architecture Changes
3.1 Persistence Layer (DB-first with CSV compatibility)

Primary store: embedded relational database suitable for local single-user use.

CSV import/export:

One-time import to bootstrap the database.

Optional periodic export to CSV for interoperability and archival.

Write-through mode (optional): mirror critical updates back to CSV for users still dependent on flat files.

3.2 Data Model (high level)

Contact: id, phone, name, email, company, tags, metadata.

Interaction: id, contact_id, type (call/text/note), timestamp, duration, outcome, body.

Outcome: id, interaction_id, category (bad_number/no_answer/callback/meeting_booked/do_not_call), notes.

Task: id, contact_id, type (callback/meeting), due_at or start/end, state, priority, external_refs (calendar ids).

CalendarMap: contact_id, task_id, provider, external_event_id.

PriorityRule: rule id, weight, enabled, last_updated.

UserPrefs: display options, default durations, reminder preferences.

Audit: entity, entity_id, action, timestamp, before/after hashes.

3.3 Concurrency & Safety

Single-user access; prevent simultaneous writers by lightweight locking.

Atomic commits for multi-entity updates (e.g., outcome + task + audit).

Crash-safe journaling; deterministic recovery on restart.

4. S3 Integration (Design & Behavior)
4.1 Scope of Sync

Must support: database file(s), archive CSV, exports, logs.

Optional later: attachment payloads (e.g., exported reports) and artifacts.

4.2 Sync Operations

Push: package a consistent snapshot and upload with a versioned key scheme.

Pull: fetch a chosen version; validate integrity; stage to a temp area; then swap atomically.

List versions: show recoverable restore points with timestamps and labels.

4.3 Integrity & Security

Object versioning required for the bucket.

Server-side encryption required; envelope or managed keys as policy dictates.

Client-side integrity checksums and post-transfer verification.

Never upload secrets; credentials are kept local.

4.4 Conflicts

Detect time skew and last-write wins vs. user-confirmed merge:

Offer to replace local, keep local, or duplicate into a new local workspace folder.

Maintain a small restore log for traceability.

5. Containerization (Interactive TUI)
5.1 Goals

One portable artifact to run the TUI on most modern machines.

Minimal host prerequisites; persistent host-mounted data directory.

5.2 Runtime Expectations

Interactive terminal access with correct signal handling and exit codes.

Local time zone honored for display and scheduling.

Data and logs persisted to a mounted host path outside the container.

5.3 Security Posture

Run with least privilege and read-only root filesystem where practical.

No embedded secrets; credentials provided at runtime through environment or mounted files under strict permissions.

Network egress only to required services.

5.4 Compatibility

Multi-architecture image to support common CPU types.

Clear guidance for Windows terminal integration.

6. Prioritization Menus & Scoring
6.1 New Menus

Today: callbacks and meetings scheduled for the current day, plus pinned items.

Due Callbacks: ordered by due time ascending.

Overdue: oldest first; encourage immediate action or snooze.

Hot Leads: filtered by recent engagement, opens, or operator-set tags.

New: uncontacted entries for net-new outreach.

Meetings: upcoming meetings, grouped by day.

6.2 Priority Score (transparent & editable)

Inputs (examples):

Time sensitivity: due date proximity, overdue age.

Intent signals: last outcome (e.g., “call back”), meeting status.

Recency: last interaction, number of attempts.

Data quality: valid phone/email, complete contact profile.

Operator signals: pinned, snoozed, tags.

Weights: default weights provided; allow user to adjust and save presets.

Display: show the score and a brief rationale (top 2–3 factors).

6.3 Focus Mode

Presents a curated list with one-keystroke actions: call, next, snooze, pin, note, reschedule.

Optional time-boxed sprint with a small on-screen timer and progress counters.

7. UX & CLI Behaviors

Global menu: quick switch between views (Today, Due, Overdue, Hot, New, Meetings, All).

Filters: add/remove tags, set min score, set date ranges.

Batch actions: mark a subset as “no answer,” schedule follow-ups in bulk, or apply tags.

Context-aware defaults: e.g., in “Due Callbacks,” default action is to start calling in order.

Assistive prompts: when picking a next action, show the top reason for the item’s priority.

8. Interop & Backward Compatibility

CSV import/export: maintain compatibility with existing columns; export includes computed fields where helpful (e.g., status, next due).

Graceful degradation: if the database is not available, allow read-only CSV mode with limited features.

Calendar mapping: preserve existing event IDs and avoid duplicates on re-imports.

9. Observability

Structured logs: actions, outcomes, task updates, sync attempts, errors (PII masked).

Counters: total calls, connects, meetings, callbacks scheduled/completed, per-day breakdowns.

Sync journal: recent push/pull events with success/failure and version info.

10. Security & Privacy

Secrets handling: keep tokens and keys off backups; exclude them from S3 sync.

Data minimization: only necessary fields are stored; redact sensitive values in logs.

Retention: configurable retention for logs and archives; ability to purge by date.

Access controls: local file permissions for database and archives.

11. Acceptance Criteria (Per Phase)
A — Database

Database becomes the default store; CSV imports cleanly; all app features (notes, outcomes, scheduling) persist.

Crash/restart preserves state with no corruption; audit log entries exist for each change.

B — S3

Push creates a versioned snapshot; Pull restores it atomically.

Conflicts are detected and resolved with explicit operator choice.

Encryption and integrity checks confirmed; secrets are never uploaded.

C — Container

Interactive TUI runs from a container on supported hosts.

Data persists via a mounted path; exit codes and signals behave correctly.

No embedded secrets; minimal privileges validated.

D — Prioritization

All new views available and switchable via the menu.

Priority scoring is visible, explainable, and adjustable; Focus Mode works end-to-end.

Batch operations and snooze/pin workflows function without data loss.

12. Risks & Mitigations

Data migration errors: dry-run import, snapshot before changes, automatic rollback on failure.

Sync conflicts: explicit prompts, clear version labels, restore log.

Container TTY quirks: test popular terminals and shells; provide guidance for terminal settings.

Over-complex scoring: keep defaults simple; allow quick reset to baseline weights.

13. Open Questions

Preferred embedded database and maximum expected dataset size.

Exact S3 bucket policies (versioning, encryption type, lifecycle retention).

Whether to sync archives and logs by default or only on demand.

Default views and weights for the priority score; should industry presets be offered.

Any requirement for multi-user access in a future phase.

14. Deliverables

Updated requirements and data model documentation.

Database-backed application with CSV import/export and an audit trail.

S3 push/pull with integrity checks, version listing, and conflict handling.

Containerized artifact runnable on target platforms with interactive TUI.

Prioritization menus, scoring controls, and Focus Mode with batch actions.

Operator guide covering migrations, sync, and day-planning workflows.
