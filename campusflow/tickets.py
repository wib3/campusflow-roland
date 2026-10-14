"""Ticket creation, validation, priority engine, and lookup for CampusFlow."""

from typing import Any, Dict, List, Optional
from campusflow.exceptions import TicketNotFoundError, ValidationError

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


def validate_ticket_input(
    title: Any, category: Any, urgency: Any, affected_users: Any
) -> Dict[str, Any]:
    """Validate and normalize ticket input fields.

    Raises:
        ValidationError: If any field fails validation.

    Returns:
        Dict with normalized fields: title, category, urgency, affected_users.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("Title must not be blank.")
    normalized_title = title.strip()

    if not isinstance(category, str) or category.strip().lower() not in ALLOWED_CATEGORIES:
        valid_opts = ", ".join(ALLOWED_CATEGORIES.values())
        raise ValidationError(
            f"Invalid category '{category}'. Allowed categories: {valid_opts}."
        )
    normalized_category = ALLOWED_CATEGORIES[category.strip().lower()]

    if not isinstance(urgency, str) or urgency.strip().lower() not in ALLOWED_URGENCIES:
        valid_opts = ", ".join(ALLOWED_URGENCIES.values())
        raise ValidationError(
            f"Invalid urgency '{urgency}'. Allowed urgencies: {valid_opts}."
        )
    normalized_urgency = ALLOWED_URGENCIES[urgency.strip().lower()]

    if isinstance(affected_users, bool):
        raise ValidationError("affected_users must be a positive integer.")
    elif isinstance(affected_users, float):
        raise ValidationError("affected_users must be a positive integer (not a decimal).")
    elif isinstance(affected_users, int):
        user_count = affected_users
    elif isinstance(affected_users, str):
        cleaned = affected_users.strip()
        if not cleaned.isdigit() and not (cleaned.startswith("+") and cleaned[1:].isdigit()):
            raise ValidationError("affected_users must be a positive integer.")
        user_count = int(cleaned)
    else:
        raise ValidationError("affected_users must be a positive integer.")

    if user_count <= 0:
        raise ValidationError(
            "affected_users must be a positive integer (greater than zero)."
        )

    return {
        "title": normalized_title,
        "category": normalized_category,
        "urgency": normalized_urgency,
        "affected_users": user_count,
    }


def calculate_priority(urgency: str, affected_users: int) -> str:
    """Calculate priority according to the four strict rules in order.

    Rule 1: high urgency AND 10 or more affected users -> critical
    Rule 2: high urgency OR 10 or more affected users  -> high
    Rule 3: medium urgency OR 3 or more affected users -> medium
    Rule 4: all remaining valid tickets                -> low
    """
    norm_urgency = urgency.strip().lower() if isinstance(urgency, str) else ""

    # Rule 1
    if norm_urgency == "high" and affected_users >= 10:
        return "critical"
    # Rule 2
    if norm_urgency == "high" or affected_users >= 10:
        return "high"
    # Rule 3
    if norm_urgency == "medium" or affected_users >= 3:
        return "medium"
    # Rule 4
    return "low"


def generate_next_id(tickets: List[Dict[str, Any]]) -> str:
    """Generate the next sequential ticket ID (T001, T002, ...).

    Scans existing IDs to avoid collisions even after reload or deletions.
    """
    max_num = 0
    for ticket in tickets:
        tid = str(ticket.get("id", "")).strip().upper()
        if tid.startswith("T") and tid[1:].isdigit():
            max_num = max(max_num, int(tid[1:]))
    return f"T{max_num + 1:03d}"


def create_ticket(
    tickets: List[Dict[str, Any]],
    title: Any,
    category: Any,
    urgency: Any,
    affected_users: Any,
) -> Dict[str, Any]:
    """Validate data, calculate priority, assign unique ID, and store ticket.

    Args:
        tickets: The list of tickets to append to.
        title: Title of the problem.
        category: Network, Hardware, Software, or Other.
        urgency: low, medium, or high.
        affected_users: Positive integer count.

    Returns:
        The newly created ticket dictionary.
    """
    validated = validate_ticket_input(title, category, urgency, affected_users)
    priority = calculate_priority(validated["urgency"], validated["affected_users"])
    ticket_id = generate_next_id(tickets)

    ticket: Dict[str, Any] = {
        "id": ticket_id,
        "title": validated["title"],
        "category": validated["category"],
        "urgency": validated["urgency"],
        "affected_users": validated["affected_users"],
        "priority": priority,
        "status": "open",
        "assigned_to": None,
        "notes": [],
    }

    tickets.append(ticket)
    return ticket


def get_ticket(tickets: List[Dict[str, Any]], ticket_id: str) -> Dict[str, Any]:
    """Look up a ticket by ID.

    Raises:
        TicketNotFoundError: If ticket_id does not exist.
    """
    if not isinstance(ticket_id, str):
        raise TicketNotFoundError(f"Invalid ticket ID: {ticket_id}")

    normalized_id = ticket_id.strip().upper()
    for ticket in tickets:
        if str(ticket.get("id", "")).strip().upper() == normalized_id:
            return ticket
    raise TicketNotFoundError(f"Ticket with ID '{ticket_id}' not found.")


def list_tickets(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of all tickets."""
    return list(tickets)
