"""Unit tests for CampusFlow Next follow-up notes (Engineer A)."""

import copy
import unittest

from campusflow.exceptions import CampusFlowError, InvalidTransitionError, TicketNotFoundError, ValidationError
from campusflow.notes import add_note, get_ticket_notes, next_note_id
from campusflow.workflow import reopen_ticket, update_status


class TestFollowUpNotes(unittest.TestCase):
    """Test suite covering structured follow-up notes and state safety."""

    def setUp(self):
        self.tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi outage in library",
                "category": "Network",
                "urgency": "high",
                "affected_users": 20,
                "priority": "critical",
                "status": "open",
                "assigned_to": "Ada",
                "notes": [],
            }
        ]

    def test_case05_valid_note_added_and_note_id_correct(self):
        """Case 05: Valid note added and assigned N001, then N002."""
        note1 = add_note(self.tickets, "T001", "Ada Okafor", "Rebooted primary access point.")
        self.assertEqual(note1["note_id"], "N001")
        self.assertEqual(note1["author"], "Ada Okafor")
        self.assertEqual(note1["message"], "Rebooted primary access point.")
        self.assertEqual(len(self.tickets[0]["notes"]), 1)

        note2 = add_note(self.tickets, "T001", "Bola Tin", "Investigating VLAN trunk configuration.")
        self.assertEqual(note2["note_id"], "N002")
        self.assertEqual(note2["author"], "Bola Tin")
        self.assertEqual(len(self.tickets[0]["notes"]), 2)

    def test_case06_blank_or_too_short_note_rejected_without_consuming_id(self):
        """Case 06: Blank and too-short notes rejected without consuming an ID."""
        before = copy.deepcopy(self.tickets)

        # Blank author
        with self.assertRaises(ValidationError):
            add_note(self.tickets, "T001", "   ", "Access point power reset")
        self.assertEqual(self.tickets, before)
        self.assertEqual(next_note_id(self.tickets[0]), "N001")

        # Too short message (< 5 characters)
        for short_msg in ("", "hi", "test", "  ok  "):
            with self.subTest(msg=short_msg):
                with self.assertRaises(ValidationError):
                    add_note(self.tickets, "T001", "Ada", short_msg)
                self.assertEqual(self.tickets, before)
                self.assertEqual(next_note_id(self.tickets[0]), "N001")

        # After rejected attempts, next valid note must still receive N001!
        valid_note = add_note(self.tickets, "T001", "Ada", "Access point reset")
        self.assertEqual(valid_note["note_id"], "N001")

    def test_too_long_note_rejected_without_consuming_id(self):
        """Messages > 300 characters are rejected without consuming an ID."""
        before = copy.deepcopy(self.tickets)
        long_message = "A" * 301

        with self.assertRaises(ValidationError):
            add_note(self.tickets, "T001", "Ada", long_message)
        self.assertEqual(self.tickets, before)
        self.assertEqual(next_note_id(self.tickets[0]), "N001")

        # Boundary: exactly 300 chars is valid
        boundary_note = add_note(self.tickets, "T001", "Ada", "B" * 300)
        self.assertEqual(boundary_note["note_id"], "N001")

    def test_case07_note_on_resolved_ticket_rejected_accepted_after_reopen(self):
        """Case 07: Note on resolved ticket rejected; note after reopen accepted.

        Workflow:
        open T001 -> add N001 -> in_progress -> add N002 -> resolve T001
        -> attempt N003 (rejected, state unchanged)
        -> reopen T001 -> add N003 (accepted, earlier notes preserved).
        """
        # Note on open ticket
        n1 = add_note(self.tickets, "T001", "Ada", "First investigation note")
        self.assertEqual(n1["note_id"], "N001")

        # Move to in_progress and add second note
        update_status(self.tickets, "T001", "in_progress")
        n2 = add_note(self.tickets, "T001", "Bola", "Replacing faulty patch cable")
        self.assertEqual(n2["note_id"], "N002")

        # Resolve ticket
        update_status(self.tickets, "T001", "resolved")
        self.assertEqual(self.tickets[0]["status"], "resolved")

        # Attempt to add note while resolved -> must be rejected
        snapshot = copy.deepcopy(self.tickets)
        with self.assertRaises(InvalidTransitionError):
            add_note(self.tickets, "T001", "Ada", "Trying to add note to resolved ticket")
        self.assertEqual(self.tickets, snapshot)
        self.assertEqual(len(self.tickets[0]["notes"]), 2)

        # Reopen ticket -> now note can be added with sequential ID N003!
        reopen_ticket(self.tickets, "T001")
        self.assertEqual(self.tickets[0]["status"], "open")

        n3 = add_note(self.tickets, "T001", "Ada", "Follow-up post-reopen investigation")
        self.assertEqual(n3["note_id"], "N003")
        self.assertEqual(len(self.tickets[0]["notes"]), 3)
        self.assertEqual([n["note_id"] for n in self.tickets[0]["notes"]], ["N001", "N002", "N003"])

    def test_malformed_notes_rejected_without_mutation(self):
        """Adding a note must not overwrite malformed existing notes data."""
        ticket = dict(self.tickets[0])
        ticket["notes"] = {"existing": "data"}
        before = copy.deepcopy(ticket)

        with self.assertRaises(ValidationError):
            add_note(ticket, "Ada", "Investigating the issue")

        self.assertEqual(ticket, before)

    def test_missing_notes_key_is_initialized_for_legacy_ticket(self):
        """A legacy ticket with no notes key can still receive a note."""
        ticket = dict(self.tickets[0])
        del ticket["notes"]

        note = add_note(ticket, "Ada", "Investigating the issue")

        self.assertEqual(note["note_id"], "N001")
        self.assertEqual(ticket["notes"], [note])

    def test_get_ticket_notes_in_deterministic_order(self):
        """Reading notes for a ticket returns all notes in sequential ID order."""
        add_note(self.tickets, "T001", "Ada", "Note number one")
        add_note(self.tickets, "T001", "Ada", "Note number two")
        add_note(self.tickets, "T001", "Ada", "Note number three")

        notes = get_ticket_notes(self.tickets, "T001")
        self.assertEqual([n["note_id"] for n in notes], ["N001", "N002", "N003"])

    def test_unknown_ticket_id_raises_not_found_without_mutation(self):
        """Attempting to add or view notes on a nonexistent ID raises TicketNotFoundError."""
        before = copy.deepcopy(self.tickets)
        with self.assertRaises(TicketNotFoundError):
            add_note(self.tickets, "T999", "Ada", "Valid message text")
        self.assertEqual(self.tickets, before)

        with self.assertRaises(TicketNotFoundError):
            get_ticket_notes(self.tickets, "T999")


if __name__ == "__main__":
    unittest.main()
