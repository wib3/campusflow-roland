"""Assignment and lifecycle operations on a shared list of ticket dictionaries."""


from campusflow.exceptions import InvalidTransitionError, TicketNotFoundError, ValidationError
from campusflow.validation import can_transition

def get_ticket(tickets, ticket_id):
    """Return the matching ticket; raise TicketNotFoundError for an unknown ID."""
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise TicketNotFoundError("Ticket ID must be a non-empty string.")
    normalized_id = ticket_id.strip().upper()
    for ticket in tickets:
        if ticket["id"] == normalized_id:
            return ticket
    raise TicketNotFoundError(f"Unknown ticket ID: {normalized_id}")


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign or reassign an unresolved ticket and return the updated record."""
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] == "resolved":
        raise InvalidTransitionError("Reopen a resolved ticket before assigning it.")
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValidationError("Staff name must be a non-empty string.")
    ticket["assigned_to"] = staff_name.strip()
    return ticket


def update_status(tickets, ticket_id, new_status):
    """Advance open → in_progress → resolved; reopening is a separate operation."""
    ticket = get_ticket(tickets, ticket_id)
    if not isinstance(new_status, str):
        raise ValidationError("Status must be open, in_progress, or resolved.")
    new_status = new_status.strip().lower()
    if new_status not in {"open", "in_progress", "resolved"}:
        raise ValidationError("Status must be open, in_progress, or resolved.")
    current_status = ticket["status"]
    if current_status == "resolved":
        raise InvalidTransitionError("Use reopen_ticket to explicitly reopen a resolved ticket.")
    next_status = {"open": "in_progress", "in_progress": "resolved"}
    if next_status.get(current_status) != new_status:
        raise InvalidTransitionError(f"Invalid status transition: {current_status} → {new_status}")
    assignee = ticket.get("assigned_to")
    if new_status == "in_progress" and (
        not isinstance(assignee, str) or not assignee.strip()
    ):
        raise InvalidTransitionError("Assign the ticket before moving it to in_progress.")
    ticket["status"] = new_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Explicitly reopen a resolved ticket, preserving its assignment."""
    ticket = get_ticket(tickets, ticket_id)
    if ticket["status"] != "resolved":
        raise InvalidTransitionError("Only a resolved ticket can be reopened.")
    ticket["status"] = "open"
    return ticket
