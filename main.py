"""CampusFlow — Technical Support Ticket Manager CLI.

Entry point for the interactive command-line interface.
"""

import sys
from typing import Any, Dict, List, Optional

from campusflow.exceptions import CampusFlowError, StorageError
from campusflow.understanding_check import run_understanding_check
from campusflow.notes import add_note, get_ticket_notes
from campusflow.reports import generate_report, get_work_queue
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket, get_ticket, list_tickets
from campusflow.workflow import assign_ticket, reopen_ticket, update_status

DEFAULT_DATA_FILE = "data/tickets.json"


def display_ticket_summary(ticket: Dict[str, Any]) -> None:
    """Print a one-line summary of a ticket."""
    assigned = ticket.get("assigned_to") or "Unassigned"
    notes_count = len(ticket.get("notes", []))
    print(
        f"[{ticket['id']}] {ticket['title']} "
        f"| Priority: {ticket['priority'].upper()} "
        f"| Status: {ticket['status']} "
        f"| Assigned: {assigned} "
        f"| Category: {ticket['category']} "
        f"| Notes: {notes_count}"
    )


def display_ticket_detail(ticket: Dict[str, Any]) -> None:
    """Print the complete details of a single ticket."""
    print("\n" + "=" * 48)
    print(f"Ticket ID:      {ticket['id']}")
    print(f"Title:          {ticket['title']}")
    print(f"Category:       {ticket['category']}")
    print(f"Urgency:        {ticket['urgency']}")
    print(f"Affected Users: {ticket['affected_users']}")
    print(f"Priority:       {ticket['priority'].upper()}")
    print(f"Status:         {ticket['status']}")
    print(f"Assigned To:    {ticket.get('assigned_to') or 'None (Unassigned)'}")
    notes = ticket.get("notes", [])
    if notes:
        print(f"\nFollow-up Notes ({len(notes)}):")
        for n in notes:
            print(f"  * [{n['note_id']}] {n['author']}: {n['message']}")
    else:
        print("Follow-up Notes: None")
    print("=" * 48)


def handle_create_ticket(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Prompt the user and create a new ticket."""
    print("\n--- Create New Ticket ---")
    title = input("Enter ticket title: ").strip()
    category = input("Enter category (Network, Hardware, Software, Other): ").strip()
    urgency = input("Enter urgency (low, medium, high): ").strip()
    affected_users_input = input("Enter number of affected users: ").strip()

    ticket = create_ticket(
        tickets=tickets,
        title=title,
        category=category,
        urgency=urgency,
        affected_users=affected_users_input,
    )
    save_tickets(tickets, data_path)
    print(f"\n[Success] Created Ticket {ticket['id']} with Priority '{ticket['priority'].upper()}'.")


def handle_list_tickets(tickets: List[Dict[str, Any]]) -> None:
    """List all tickets."""
    print("\n--- All Tickets ---")
    all_tickets = list_tickets(tickets)
    if not all_tickets:
        print("No tickets found in the system.")
        return

    for ticket in all_tickets:
        display_ticket_summary(ticket)
    print(f"\nTotal: {len(all_tickets)} ticket(s)")


def handle_view_ticket(tickets: List[Dict[str, Any]]) -> None:
    """Look up and inspect a ticket by ID."""
    print("\n--- View Ticket Details ---")
    ticket_id = input("Enter ticket ID (e.g. T001): ").strip()
    ticket = get_ticket(tickets, ticket_id)
    display_ticket_detail(ticket)


def handle_assign_ticket(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Assign or reassign an unresolved ticket to a staff member."""
    print("\n--- Assign Ticket ---")
    ticket_id = input("Enter ticket ID: ").strip()
    staff_name = input("Enter staff member name: ").strip()
    ticket = assign_ticket(tickets, ticket_id, staff_name)
    save_tickets(tickets, data_path)
    print(f"\n[Success] Ticket {ticket['id']} assigned to '{ticket['assigned_to']}'.")


def handle_update_status(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Advance ticket lifecycle: open -> in_progress -> resolved."""
    print("\n--- Update Ticket Status ---")
    ticket_id = input("Enter ticket ID: ").strip()
    print("Allowed transitions: open -> in_progress (requires assignee), in_progress -> resolved")
    new_status = input("Enter new status (in_progress, resolved): ").strip()
    ticket = update_status(tickets, ticket_id, new_status)
    save_tickets(tickets, data_path)
    print(f"\n[Success] Ticket {ticket['id']} status updated to '{ticket['status']}'.")


def handle_reopen_ticket(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Explicitly reopen a resolved ticket."""
    print("\n--- Reopen Ticket ---")
    ticket_id = input("Enter ticket ID to reopen: ").strip()
    ticket = reopen_ticket(tickets, ticket_id)
    save_tickets(tickets, data_path)
    print(f"\n[Success] Ticket {ticket['id']} reopened (status is now 'open').")


def handle_work_queue(tickets: List[Dict[str, Any]]) -> None:
    """Display open tickets awaiting work, sorted by priority then ID."""
    print("\n--- Open Tickets Awaiting Work (Priority Queue) ---")
    queue = get_work_queue(tickets)
    if not queue:
        print("No open tickets awaiting work.")
        return

    for ticket in queue:
        display_ticket_summary(ticket)
    print(f"\nQueue count: {len(queue)} open ticket(s)")


def handle_generate_report(tickets: List[Dict[str, Any]]) -> None:
    """Display ticket totals, breakdowns, and resolution metrics."""
    print("\n--- Ticket Metrics & Status Report ---")
    report = generate_report(tickets)

    print(f"Total Tickets: {report['total']}")
    print(f"Unresolved Tickets: {report['unresolved']}")
    print(f"Resolved Tickets: {report['resolved']}")
    print(f"Resolution Rate: {report['resolution_percentage']:.1f}%")

    print("\nBreakdown by Status:")
    for status, count in report["by_status"].items():
        print(f"  * {status:12s}: {count}")

    print("\nBreakdown by Priority:")
    for priority, count in report["by_priority"].items():
        print(f"  * {priority.upper():12s}: {count}")

    print("\nBreakdown by Category:")
    for category, count in report["by_category"].items():
        print(f"  * {category:12s}: {count}")


def handle_search_tickets(tickets: List[Dict[str, Any]]) -> None:
    """Search ticket titles and optionally filter by category, status, and priority."""
    from campusflow.search import (
        ALLOWED_CATEGORIES,
        ALLOWED_PRIORITIES,
        ALLOWED_STATUSES,
        search_tickets,
    )

    print("\n--- Search and Filter Tickets ---")
    title_query = input("Title contains (press Enter for any title): ").strip()

    def choose_filter(label: str, choices: tuple) -> Optional[str]:
        while True:
            value = input(
                f"{label} ({', '.join(choices)}) or Enter to skip: "
            ).strip()
            if not value:
                return None

            for choice in choices:
                if value.casefold() == choice.casefold():
                    return choice

            print(f"Invalid {label.lower()}. Choose one of: {', '.join(choices)}.")

    category = choose_filter("Category", ALLOWED_CATEGORIES)
    status = choose_filter("Status", ALLOWED_STATUSES)
    priority = choose_filter("Priority", ALLOWED_PRIORITIES)

    results = search_tickets(
        tickets,
        title_query=title_query,
        category=category,
        status=status,
        priority=priority,
    )

    if not results:
        print("No tickets matched your search and filters.")
        return

    for ticket in results:
        display_ticket_summary(ticket)

    print(f"\nMatching tickets: {len(results)}")





def handle_view_notes(tickets: List[Dict[str, Any]]) -> None:
    """Display a ticket's follow-up notes."""
    ticket_id = input("Ticket ID: ").strip()
    notes = get_ticket_notes(tickets, ticket_id)

    if not notes:
        print(f"No follow-up notes for ticket {ticket_id.strip().upper()}.")
        return

    print(f"\nFollow-up notes for {ticket_id.strip().upper()}:")
    for note in notes:
        print(f"[{note['note_id']}] {note['author']}: {note['message']}")


def handle_add_note(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Prompt the user and add a structured follow-up note to an active ticket."""
    print("\n--- Add Follow-up Note ---")
    ticket_id = input("Enter ticket ID: ").strip()
    author = input("Enter your name/role (Author): ").strip()
    message = input("Enter follow-up message (5-300 characters): ").strip()
    note = add_note(tickets, ticket_id, author, message)
    save_tickets(tickets, data_path)
    print(
        f"\n[Success] Added Note '{note['note_id']}' by '{note['author']}' "
        f"to Ticket {ticket_id.upper()}."
    )


def run_menu(tickets: List[Dict[str, Any]], data_path: str) -> None:
    """Main CLI menu interaction loop."""
    menu = """
======================================================
       CampusFlow — Technical Support Manager
======================================================
1. Create New Ticket (F1)
2. View All Tickets (F2)
3. View Single Ticket Details (F2)
4. Assign Ticket to Staff (F3)
5. Update Ticket Status (F4)
6. Reopen Resolved Ticket (F4)
7. Open Tickets Awaiting Work (F5 Queue)
8. Generate Summary Report (F6)
9. Search and Filter Tickets
10. Understanding Check
11. Add Follow-up Note
12. View Ticket Notes
13. Save and Exit (F7)
======================================================
Select an option (1-13): """

    while True:
        try:
            choice = input(menu).strip()
            if choice == "1":
                handle_create_ticket(tickets, data_path)
            elif choice == "2":
                handle_list_tickets(tickets)
            elif choice == "3":
                handle_view_ticket(tickets)
            elif choice == "4":
                handle_assign_ticket(tickets, data_path)
            elif choice == "5":
                handle_update_status(tickets, data_path)
            elif choice == "6":
                handle_reopen_ticket(tickets, data_path)
            elif choice == "7":
                handle_work_queue(tickets)
            elif choice == "8":
                handle_generate_report(tickets)
            elif choice == "9":
                handle_search_tickets(tickets)
            elif choice == "10":
                run_understanding_check()
            elif choice == "11":
                handle_add_note(tickets, data_path)
            elif choice == "12":
                handle_view_notes(tickets)
            elif choice in {"13", "exit", "quit", "q"}:
                save_tickets(tickets, data_path)
                print("\n[CampusFlow] Tickets saved successfully. Goodbye!\n")
                break
            else:
                print(f"\n[Warning] Invalid option '{choice}'. Please select a number between 1 and 13.")
        except CampusFlowError as err:
            print(f"\n[Operation Failed] {err}")
        except (KeyboardInterrupt, EOFError):
            print("\n\n[CampusFlow] Interrupted. Saving changes and exiting...")
            try:
                save_tickets(tickets, data_path)
            except StorageError:
                pass
            print("[CampusFlow] Goodbye!\n")
            break


def main() -> None:
    """CLI application entrypoint."""
    data_path = DEFAULT_DATA_FILE
    try:
        tickets = load_tickets(data_path)
        print(f"[CampusFlow] Loaded {len(tickets)} ticket(s) from '{data_path}'.")
    except StorageError as err:
        print(f"[CampusFlow Warning] {err}")
        print(
            "[CampusFlow] Startup stopped to protect existing data. "
            "Fix the storage file and restart."
        )
        return

    run_menu(tickets, data_path)


if __name__ == "__main__":
    main()
