# CampusFlow — Technical Support Ticket Manager

CampusFlow is a Python command-line helpdesk ticket management system designed for campus technical support teams to record issues, automatically calculate priority, assign responsibility, track resolution workflows, and report metrics.

## Engineering Team
* **Engineer 1 (wib3):** Ticket Creation, Validation, Priority Engine, Ticket View (`campusflow/tickets.py`), and Unit Tests (`tests/test_tickets.py`).
* **Engineer 2 (rolandelaigwu6-ui):** Ticket Assignment, Lifecycle Workflow, Work Queue, Reporting (`campusflow/workflow.py`, `campusflow/reports.py`), and Unit Tests (`tests/test_workflow.py`).

## Core Features
1. **F1 — Ticket Creation & Validation:** Validates title, category, urgency, and positive user count. Automatically generates unique IDs (`T001`, `T002`, ...).
2. **F2 — List / View:** Displays all tickets and inspects ticket details.
3. **F3 — Assignment:** Assigns tickets to staff members; validates IDs and non-empty names.
4. **F4 — Lifecycle Workflow:** Enforces valid transitions (`open` -> `in_progress` -> `resolved`), requires assignment before progress, and explicit reopen for resolved tickets.
5. **F5 — Work Queue:** Lists only open tickets awaiting work (excluding in_progress and resolved), ordered by priority (`critical` -> `high` -> `medium` -> `low`) and breaks ties by ticket ID.
6. **F6 — Reports:** Summarizes total tickets with breakdowns by status and priority.
7. **F7 — Persistence:** Safe JSON save/load with support for fresh start on missing file and error detection on malformed data.

## CampusFlow Next Features (Sprint 2)
8. **Requirement A — Centralized Validation & Lifecycle Safety:** Type-pure validation (`affected_users` positive integers, non-blank title, legal category/urgency). Unassigned tickets cannot enter `in_progress`. Resolved tickets cannot be mutated without explicit reopen. All rejected operations guarantee zero mutation of stored tickets.
9. **Requirement B — Structured Follow-up Notes:** Threaded notes per ticket (`note_id`, `author`, `message`). Sequential IDs (`N001`, `N002`, ...); rejected notes do not consume IDs. Notes allowed only on `open` or `in_progress` tickets.
10. **Requirement E — Safe JSON Persistence & Validation:** Atomic JSON save/load with full collection schema validation on load. Corrupted files, duplicate ticket IDs, tampered priority, or schema violations raise `StorageError` and preserve in-memory state. Backward-compatible migration ensures legacy tickets without notes are seamlessly upgraded.

## JSON Storage Envelope Format
Tickets are persisted as a JSON array of ticket objects (`data/tickets.json`):
```json
[
  {
    "id": "T001",
    "title": "Wi-Fi outage in CS lab",
    "category": "Network",
    "urgency": "high",
    "affected_users": 15,
    "priority": "critical",
    "status": "in_progress",
    "assigned_to": "Ada",
    "notes": [
      {
        "note_id": "N001",
        "author": "Ada",
        "message": "Power-cycled access point AP-04."
      }
    ]
  }
]
```

## Running CampusFlow
```bash
python3 main.py
```

## Running Automated Tests
```bash
python3 -m unittest discover -s tests -v
```

## Documentation
* [Diagnostic Baseline Check](docs/baseline-check.md)
* [Architecture & Design Decisions](docs/design-decisions.md)
* [AI Learning Log & Defense Questions](docs/ai-learning-log.md)

## Integration Status
* **F1 — Ticket Creation & Validation:** (`campusflow/tickets.py`)
* **F2 — List & View Tickets:** (`campusflow/tickets.py`)
* **F3 — Staff Assignment:** (`campusflow/workflow.py`)
* **F4 — Lifecycle Transitions & Reopen:** (`campusflow/workflow.py`)
* **F5 — Open-Ticket Work Queue:** (`campusflow/reports.py`)
* **F6 — Summary Reports:** (`campusflow/reports.py`)
* **F7 / Req E — Safe JSON Persistence & Full Collection Validation:** (`campusflow/storage.py`)
* **Req A — Centralized Validation Helpers & Invariants:** (`campusflow/validation.py`)
* **Req B — Structured Follow-up Notes:** (`campusflow/notes.py`)
* **Interactive CLI Interface:** (`main.py`)
