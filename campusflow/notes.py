"""Structured follow-up notes for CampusFlow Next."""

from typing import Any, Dict, List, Optional
from campusflow.exceptions import InvalidTransitionError, TicketNotFoundError, ValidationError


def next_note_id(ticket: Dict[str, Any]) -> str:
    """Generate the next sequential note ID (N001, N002, ...) for a ticket.

    Scans existing notes in the ticket to guarantee uniqueness across reloads.
    A rejected note attempt does not consume an ID.
    """
    notes = ticket.get("notes", [])
    max_num = 0
    for note in notes:
        nid = str(note.get("note_id", "")).strip().upper()
        if nid.startswith("N") and nid[1:].isdigit():
            max_num = max(max_num, int(nid[1:]))
    return f"N{max_num + 1:03d}"


def validate_note_input(author: Any, message: Any) -> Dict[str, str]:
    """Validate and clean note author and message.

    Rules:
        - Author cannot be blank after trimming.
        - Message length must be 5 to 300 characters after trimming.

    Raises:
        ValidationError: If input violates length or content constraints.

    Returns:
        Dict with cleaned 'author' and 'message'.
    """
    if not isinstance(author, str) or not author.strip():
        raise ValidationError("Note author must not be blank.")

    if not isinstance(message, str):
        raise ValidationError("Note message must be a string.")

    cleaned_msg = message.strip()
    if len(cleaned_msg) < 5:
        raise ValidationError("Note message must be at least 5 characters long.")
    if len(cleaned_msg) > 300:
        raise ValidationError("Note message must not exceed 300 characters.")

    return {
        "author": author.strip(),
        "message": cleaned_msg,
    }


def add_note(
    tickets_or_ticket: Any,
    ticket_id_or_author: Any,
    author_or_message: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a validated follow-up note to an open or in_progress ticket.

    Signatures supported:
        - add_note(tickets, ticket_id, author, message)
        - add_note(ticket, author, message)

    Raises:
        TicketNotFoundError: If ticket ID does not exist in collection.
        InvalidTransitionError: If the ticket is resolved.
        ValidationError: If author or message is invalid.

    Returns:
        The newly created note dictionary.
    """
    # Disambiguate arguments
    if isinstance(tickets_or_ticket, list):
        tickets = tickets_or_ticket
        ticket_id = ticket_id_or_author
        author = author_or_message
        msg = message

        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise TicketNotFoundError("Ticket ID must be a non-empty string.")
        normalized_id = ticket_id.strip().upper()

        ticket = None
        for t in tickets:
            if str(t.get("id", "")).strip().upper() == normalized_id:
                ticket = t
                break
        if ticket is None:
            raise TicketNotFoundError(f"Ticket with ID '{ticket_id}' not found.")
    elif isinstance(tickets_or_ticket, dict):
        ticket = tickets_or_ticket
        author = ticket_id_or_author
        msg = author_or_message
    else:
        raise ValidationError("First argument must be a tickets list or ticket dictionary.")

    # Invariant: notes may only be added to open or in_progress tickets
    status = ticket.get("status")
    if status == "resolved":
        raise InvalidTransitionError("Cannot add notes to a resolved ticket. Reopen the ticket first.")
    if status not in {"open", "in_progress"}:
        raise InvalidTransitionError(f"Cannot add notes to ticket in state '{status}'.")

    # Validate note author and message
    cleaned = validate_note_input(author, msg)

    # Older tickets may omit notes, but malformed existing data must not
    # be silently discarded.
    if "notes" not in ticket:
        ticket["notes"] = []
    elif not isinstance(ticket["notes"], list):
        raise ValidationError("Ticket notes must be a list.")

    note_id = next_note_id(ticket)
    new_note: Dict[str, Any] = {
        "note_id": note_id,
        "author": cleaned["author"],
        "message": cleaned["message"],
    }

    ticket["notes"].append(new_note)
    return new_note


def get_ticket_notes(tickets_or_ticket: Any, ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all notes for a ticket, ordered by note ID.

    Signatures supported:
        - get_ticket_notes(tickets, ticket_id)
        - get_ticket_notes(ticket)
    """
    if isinstance(tickets_or_ticket, list):
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise TicketNotFoundError("Ticket ID must be a non-empty string.")
        normalized_id = ticket_id.strip().upper()
        target_ticket = None
        for t in tickets_or_ticket:
            if str(t.get("id", "")).strip().upper() == normalized_id:
                target_ticket = t
                break
        if target_ticket is None:
            raise TicketNotFoundError(f"Ticket with ID '{ticket_id}' not found.")
        ticket = target_ticket
    elif isinstance(tickets_or_ticket, dict):
        ticket = tickets_or_ticket
    else:
        raise ValidationError("First argument must be a tickets list or ticket dictionary.")

    notes = list(ticket.get("notes", []))
    # Sort deterministically by numeric note_id suffix
    def note_sort_key(n: Dict[str, Any]) -> int:
        nid = str(n.get("note_id", "")).strip().upper()
        if nid.startswith("N") and nid[1:].isdigit():
            return int(nid[1:])
        return 0

    return sorted(notes, key=note_sort_key)
