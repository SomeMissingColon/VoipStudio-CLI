# PLANS_FOR_THE_FUTURE.md — Non-Committal Overview

This document outlines potential future directions for **vstudio-cli** and the reasons they may be explored. It does not imply delivery timelines or commitments.

---

## Context & Intent

**Current focus:** a shell-based, keyboard-first workflow that reads a call list, initiates and monitors calls, captures outcomes, and schedules next steps.

**Intent for future work:** evaluate additions that could improve reliability, portability, and day-to-day decision support while preserving the fast, low-friction terminal experience.

---

## Guiding Principles

- **Keep the loop tight:** fast load, one clear next action, minimal ceremony.  
- **Prefer explainability:** prioritization should show why items are ordered as they are.  
- **Be portable:** run predictably on common machines and move data safely between them.  
- **Minimize operational risk:** reversible changes; backups before mutation.  
- **Respect privacy:** least data collected, least access required.

---

## Candidate Feature: Embedded Database (Local, Single-User)

### Purpose
Provide a durable system of record that can retain interaction history, outcomes, scheduling, and notes beyond CSV limitations.

### Why It Might Help
- **Reliability:** transactional updates reduce chances of partial writes.  
- **History & insights:** consistent schema supports review and simple trend analysis.  
- **Recovery:** journaling and snapshots may reduce data-loss exposure.

### Functional Considerations
- Import from an existing CSV into a local store.  
- Persist interactions (calls, texts, notes), outcomes, scheduling fields.  
- Optional export back to CSV for interoperability.

### Non-Functional Considerations
- Near-instant startup and search for typical lists.  
- Crash safety and predictable recovery.  
- Single-user locking to avoid concurrent write conflicts.

### Risks / Trade-offs
- Added complexity vs. the simplicity of a flat file.  
- Migration paths and expectations for CSV parity.

### Signals to Evaluate
- Fewer corruption incidents, fewer manual restores, higher user confidence in saved state.

---

## Candidate Feature: S3 Workspace Sync (Backup & Portability)

### Purpose
Enable off-device backup/restore and moving a workspace between machines without manual file juggling.

### Why It Might Help
- **Continuity:** recover from device issues.  
- **Portability:** continue work on another machine with minimal setup.  
- **Auditability:** versioned snapshots provide a simple change history.

### Functional Considerations
- One-command “push” (snapshot upload) and “pull” (restore).  
- Version listing to choose restore points.  
- Integrity checks before and after transfer.

### Non-Functional Considerations
- Respect limited bandwidth and intermittent connectivity.  
- Keep credentials local; exclude secrets from sync.

### Risks / Trade-offs
- Conflict handling when multiple machines diverge.  
- User experience around overwrite prompts and staging restores.

### Signals to Evaluate
- Successful restores in testing; lower support burden for “lost data” cases.

---

## Candidate Feature: Containerized Distribution (Portable Runtime)

### Purpose
Offer a predictable way to run the app on modern systems with minimal environment drift.

### Why It Might Help
- **Consistency:** same runtime everywhere can reduce setup issues.  
- **Simplicity:** fewer dependency concerns for end users.  
- **Isolation:** clearer boundaries for file access and networking.

### Functional Considerations
- Interactive TUI in a containerized terminal session.  
- Host directory mounts for data persistence.  
- Straightforward handling for required tokens at runtime.

### Non-Functional Considerations
- Sensible artifact size and startup latency.  
- Signal handling and exit codes suitable for terminal use.

### Risks / Trade-offs
- Not all environments run containers comfortably (policy or tooling).  
- Terminal behavior can vary across hosts.

### Signals to Evaluate
- Reduced installation questions, shorter “time to first call.”

---

## Candidate Feature: Prioritization Menus & Focus Workflows

### Purpose
Reduce cognitive load by helping operators decide what to do next.

### Why It Might Help
- **Clarity:** curated queues (e.g., Today, Due, Overdue, Hot, New) surface relevant contacts.  
- **Momentum:** a Focus Mode may reduce context switching and improve throughput.  
- **Trust:** a transparent score can justify ordering.

### Functional Considerations
- Multiple list views with simple toggles and filters.  
- A priority signal derived from urgency (due dates), recency (last contact), intent (outcomes), and operator inputs (pin/snooze/tags).  
- Focus Mode presenting a sequenced queue with one-keystroke actions.

### Non-Functional Considerations
- Stable performance while sorting and filtering larger lists.  
- Clear rationale display for top ordering factors.

### Risks / Trade-offs
- Over-optimization could obscure simple workflows; transparency matters.  
- Tuning weights may require iteration; defaults should be conservative.

### Signals to Evaluate
- Higher completion rates for callbacks due today; reduced time spent “deciding.”

---

## Additional Areas Under Consideration

- **Lightweight analytics:** daily/weekly counters (calls placed, connects, meetings set).  
- **Batch actions:** scheduled follow-ups or status updates for selected groups.  
- **Workspace hygiene:** periodic archive rotation and optional local retention windows.

(These may be explored only if they do not slow the core call → outcome → next loop.)

---

## Privacy & Security Posture (Across Features)

- Store the minimum necessary data to support workflow.  
- Keep secrets out of backups and remote sync; prefer local secure storage when available.  
- Use clear, reversible operations (e.g., snapshot before mutation) to limit blast radius.

---

## Compatibility & Degradation

- Preserve a CSV path for users who prefer or require it (import/export).  
- Allow read-only modes when certain components (database, network, or container runtime) are unavailable.  
- Favor feature toggles over hard dependencies to keep the base workflow usable.

---

## Evaluation Framework (Non-Promissory)

- **Reliability:** fewer corrupted states; predictable recovery.  
- **Speed to action:** shorter path from opening the app to initiating work.  
- **Focus:** higher completion rates on time-bound tasks (e.g., callbacks due today).  
- **Portability:** smoother transitions between machines; successful restore drills.  
- **Operator feedback:** qualitative input on clarity and friction.

---

## Open Questions

- What is an acceptable baseline for “instant” interactions (load, search, switch view)?  
- Which portability scenarios matter most (backup safety vs. multi-device hopping)?  
- How much configurability should priority scoring expose before it becomes noise?  
- Are there compliance or retention expectations that influence backup/archival choices?  
- What minimum dataset size should inform performance targets?

---

## Sequencing (Tentative, Subject to Change)

1. Explore a local embedded database to stabilize state and history.  
2. Evaluate S3 snapshots for recovery and portability.  
3. Consider containerization to reduce setup variance.  
4. Prototype prioritization views and Focus Mode with clear rationale.

*This overview describes possibilities for discussion and evaluation. It does not constitute a commitment to deliver specific features or timelines.*
