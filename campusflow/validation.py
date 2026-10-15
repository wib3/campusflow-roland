"""Centralized domain validation helpers and invariants for CampusFlow Next."""

from typing import Any, Dict, List, Optional
from campusflow.exceptions import InvalidTransitionError, ValidationError, StorageError

ALLOWED_CATEGORIES = {
    "network": "Network",
    "hardware": "Hardware",
    "software": "Software",
    "other": "Other",
}

ALLOWED_URGENCIES = {
    "low": "low",
    "medium": "medium",
    "high": "high",
}

ALLOWED_STATUSES = {"open", "in_progress", "resolved"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}


def validate_title(title: Any) -> str:
    """Validate ticket title: must be a non-blank string after trimming."""
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("Title must not be blank.")
    return title.strip()


def validate_category(category: Any) -> str:
    """Validate and normalize category: Network, Hardware, Software, or Other."""
    if not isinstance(category, str) or category.strip().lower() not in ALLOWED_CATEGORIES:
        valid_opts = ", ".join(ALLOWED_CATEGORIES.values())
        raise ValidationError(
            f"Invalid category '{category}'. Allowed categories: {valid_opts}."
        )
    return ALLOWED_CATEGORIES[category.strip().lower()]


def validate_urgency(urgency: Any) -> str:
    """Validate and normalize urgency: low, medium, or high."""
    if not isinstance(urgency, str) or urgency.strip().lower() not in ALLOWED_URGENCIES:
        valid_opts = ", ".join(ALLOWED_URGENCIES.values())
        raise ValidationError(
            f"Invalid urgency '{urgency}'. Allowed urgencies: {valid_opts}."
        )
    return ALLOWED_URGENCIES[urgency.strip().lower()]


def validate_affected_users(affected_users: Any, strict: bool = False) -> int:
    """Validate affected_users count.

    Must be a strictly positive integer (> 0).
    Rejects booleans (isinstance(True, int) is True in Python),
    floats (decimals), negative integers, and zero.

    If strict=True, strings are strictly rejected as well.
    If strict=False (e.g. raw CLI input), strings containing positive integer digits
    are converted, while non-numeric strings are rejected.
    """
    if isinstance(affected_users, bool):
        raise ValidationError("affected_users must be a positive integer.")
    if isinstance(affected_users, float):
        raise ValidationError("affected_users must be a positive integer (not a decimal).")

    if isinstance(affected_users, int):
        user_count = affected_users
    elif isinstance(affected_users, str):
        if strict:
            raise ValidationError("affected_users must be a positive integer (not a string).")
        cleaned = affected_users.strip()
        if not cleaned.isdigit() and not (cleaned.startswith("+") and cleaned[1:].isdigit()):
            raise ValidationError("affected_users must be a positive integer.")
        user_count = int(cleaned)
    else:
        raise ValidationError("affected_users must be a positive integer.")

    if user_count <= 0:
        raise ValidationError("affected_users must be a positive integer (greater than zero).")

    return user_count


def validate_staff_name(staff_name: Any) -> str:
    """Validate staff member name: non-empty string."""
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValidationError("Staff name must be a non-empty string.")
    return staff_name.strip()


def can_transition(ticket: Dict[str, Any], target_status: str) -> bool:
    """Check whether a ticket can transition to target_status without raising errors."""
    if not isinstance(ticket, dict) or not isinstance(target_status, str):
        return False
    target = target_status.strip().lower()
    if target not in ALLOWED_STATUSES:
        return False

    current = ticket.get("status")
    if current == "open":
        if target == "in_progress":
            assignee = ticket.get("assigned_to")
            return isinstance(assignee, str) and bool(assignee.strip())
        return False
    elif current == "in_progress":
        return target == "resolved"
    elif current == "resolved":
        return target == "open"
    return False


def validate_transition(ticket: Dict[str, Any], target_status: str) -> str:
    """Validate lifecycle transition: open -> in_progress -> resolved; reopen resolved -> open.

    Raises:
        ValidationError: If target_status is malformed.
        InvalidTransitionError: If transition violates lifecycle invariants.
    """
    if not isinstance(target_status, str):
        raise ValidationError("Status must be open, in_progress, or resolved.")
    normalized = target_status.strip().lower()
    if normalized not in ALLOWED_STATUSES:
        raise ValidationError("Status must be open, in_progress, or resolved.")

    current = ticket.get("status")
    if current == "resolved":
        raise InvalidTransitionError("Use reopen_ticket to explicitly reopen a resolved ticket.")

    next_status = {"open": "in_progress", "in_progress": "resolved"}
    if next_status.get(current) != normalized:
        raise InvalidTransitionError(f"Invalid status transition: {current} → {normalized}")

    if normalized == "in_progress":
        assignee = ticket.get("assigned_to")
        if not isinstance(assignee, str) or not assignee.strip():
            raise InvalidTransitionError("Assign the ticket before moving it to in_progress.")

    return normalized


def validate_ticket_dict(ticket: Dict[str, Any], calculate_priority_fn: Optional[Any] = None) -> None:
    """Validate the complete internal schema and integrity of a single ticket dictionary.

    Raises:
        StorageError or ValidationError: If ticket data violates schema or invariants.
    """
    if not isinstance(ticket, dict):
        raise StorageError(f"Expected ticket dictionary, got {type(ticket).__name__}.")

    required_keys = {"id", "title", "category", "urgency", "affected_users", "priority", "status", "assigned_to"}
    missing = required_keys - set(ticket.keys())
    if missing:
        raise StorageError(f"Ticket {ticket.get('id', '?')} is missing required fields: {', '.join(sorted(missing))}.")

    # ID validation
    tid = ticket["id"]
    if not isinstance(tid, str) or not tid.strip().upper().startswith("T") or not tid.strip()[1:].isdigit():
        raise StorageError(f"Invalid ticket ID format '{tid}'. Must be 'T' followed by digits.")

    # Title
    if not isinstance(ticket["title"], str) or not ticket["title"].strip():
        raise StorageError(f"Ticket {tid} has blank or invalid title.")

    # Category
    if ticket["category"] not in ALLOWED_CATEGORIES.values():
        raise StorageError(f"Ticket {tid} has invalid category '{ticket['category']}'.")

    # Urgency
    if ticket["urgency"] not in ALLOWED_URGENCIES.values():
        raise StorageError(f"Ticket {tid} has invalid urgency '{ticket['urgency']}'.")

    # Affected users (strict: no bools, floats, strings in storage)
    users = ticket["affected_users"]
    if isinstance(users, bool) or not isinstance(users, int) or users <= 0:
        raise StorageError(f"Ticket {tid} has invalid affected_users '{users}'. Must be positive integer.")

    # Status
    status = ticket["status"]
    if status not in ALLOWED_STATUSES:
        raise StorageError(f"Ticket {tid} has invalid status '{status}'.")

    # Priority
    priority = ticket["priority"]
    if priority not in ALLOWED_PRIORITIES:
        raise StorageError(f"Ticket {tid} has invalid priority '{priority}'.")

    if calculate_priority_fn:
        expected_priority = calculate_priority_fn(ticket["urgency"], ticket["affected_users"])
        if priority != expected_priority:
            raise StorageError(
                f"Ticket {tid} has inconsistent priority '{priority}'; expected '{expected_priority}'."
            )

    # Invariant: in_progress must have non-empty assigned_to
    assignee = ticket["assigned_to"]
    if assignee is not None and (not isinstance(assignee, str) or not assignee.strip()):
        raise StorageError(f"Ticket {tid} has invalid assigned_to value '{assignee}'.")

    if status == "in_progress" and (assignee is None or not str(assignee).strip()):
        raise StorageError(f"Ticket {tid} is in_progress but has no assigned staff member.")

    # Notes validation
    notes = ticket.get("notes")
    if notes is not None:
        if not isinstance(notes, list):
            raise StorageError(f"Ticket {tid} notes must be a list.")
        seen_note_ids = set()
        for idx, note in enumerate(notes):
            if not isinstance(note, dict):
                raise StorageError(f"Ticket {tid} note at index {idx} is not a dictionary.")
            for key in ("note_id", "author", "message"):
                if key not in note:
                    raise StorageError(f"Ticket {tid} note at index {idx} missing key '{key}'.")
            nid = note["note_id"]
            if not isinstance(nid, str) or not nid.strip().upper().startswith("N") or not nid.strip()[1:].isdigit():
                raise StorageError(f"Ticket {tid} note at index {idx} has invalid note_id '{nid}'.")
            if nid in seen_note_ids:
                raise StorageError(f"Ticket {tid} has duplicate note ID '{nid}'.")
            seen_note_ids.add(nid)

            if not isinstance(note["author"], str) or not note["author"].strip():
                raise StorageError(f"Ticket {tid} note '{nid}' has blank author.")

            msg = note["message"]
            if not isinstance(msg, str) or len(msg.strip()) < 5 or len(msg.strip()) > 300:
                raise StorageError(f"Ticket {tid} note '{nid}' message length must be 5-300 characters.")
