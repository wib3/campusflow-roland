"""Unit tests for centralized validation and lifecycle invariants (Engineer A)."""

import copy
import unittest

from campusflow.exceptions import CampusFlowError, InvalidTransitionError, StorageError, ValidationError
from campusflow.tickets import calculate_priority, create_ticket
from campusflow.validation import (
    can_transition,
    validate_affected_users,
    validate_category,
    validate_staff_name,
    validate_ticket_dict,
    validate_title,
    validate_transition,
    validate_urgency,
)
from campusflow.workflow import assign_ticket, update_status


class TestValidationAndInvariants(unittest.TestCase):
    """Test suite for Requirement A & Milestones A2, A3."""

    def setUp(self):
        self.tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi router dead",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]

    def test_case02_unassigned_open_to_in_progress_rejected_with_unchanged_data(self):
        """Case 02: Unassigned open -> in_progress rejected with unchanged data."""
        before = copy.deepcopy(self.tickets)

        with self.assertRaises(InvalidTransitionError) as ctx:
            update_status(self.tickets, "T001", "in_progress")

        self.assertIn("Assign the ticket before moving it to in_progress", str(ctx.exception))
        # Invariant: whole collection remains identical
        self.assertEqual(self.tickets, before)

    def test_case03_resolved_ticket_assignment_mutation_rejected(self):
        """Case 03: Resolved ticket cannot be assigned or mutated without reopening."""
        self.tickets[0]["assigned_to"] = "Ada"
        update_status(self.tickets, "T001", "in_progress")
        update_status(self.tickets, "T001", "resolved")
        self.assertEqual(self.tickets[0]["status"], "resolved")

        before = copy.deepcopy(self.tickets)

        # Attempt to change assignment
        with self.assertRaises(InvalidTransitionError):
            assign_ticket(self.tickets, "T001", "Bola")
        self.assertEqual(self.tickets, before)

        # Attempt to change status without explicit reopen
        for st in ("open", "in_progress", "resolved"):
            with self.subTest(status=st):
                with self.assertRaises(InvalidTransitionError):
                    update_status(self.tickets, "T001", st)
                self.assertEqual(self.tickets, before)

    def test_case04_invalid_affected_users_rejected(self):
        """Case 04: Invalid affected_users (0, negative, float, boolean, str in strict) rejected."""
        # 0
        with self.assertRaises(ValidationError):
            validate_affected_users(0, strict=True)
        # negative
        with self.assertRaises(ValidationError):
            validate_affected_users(-1, strict=True)
            validate_affected_users(-100, strict=True)
        # float
        with self.assertRaises(ValidationError):
            validate_affected_users(2.5, strict=True)
        # boolean (isinstance(True, int) is True in Python)
        with self.assertRaises(ValidationError):
            validate_affected_users(True, strict=True)
        with self.assertRaises(ValidationError):
            validate_affected_users(False, strict=True)
        # string masquerading as int in strict mode
        with self.assertRaises(ValidationError):
            validate_affected_users("10", strict=True)
        # non-numeric string
        with self.assertRaises(ValidationError):
            validate_affected_users("twenty", strict=False)

    def test_validate_title_invariants(self):
        """Title must be non-empty after trimming."""
        self.assertEqual(validate_title("  Laptop broken  "), "Laptop broken")
        for bad_title in ("", "   ", None, 123):
            with self.subTest(title=bad_title):
                with self.assertRaises(ValidationError):
                    validate_title(bad_title)

    def test_validate_category_invariants(self):
        """Category must be Network, Hardware, Software, or Other (case-insensitive normalized)."""
        self.assertEqual(validate_category("network"), "Network")
        self.assertEqual(validate_category("HARDWARE"), "Hardware")
        self.assertEqual(validate_category("software"), "Software")
        self.assertEqual(validate_category("Other"), "Other")

        for bad_cat in ("Printers", "Database", "Unknown", "", None):
            with self.subTest(cat=bad_cat):
                with self.assertRaises(ValidationError):
                    validate_category(bad_cat)

    def test_validate_urgency_invariants(self):
        """Urgency must be low, medium, or high (case-insensitive normalized)."""
        self.assertEqual(validate_urgency("LOW"), "low")
        self.assertEqual(validate_urgency("Medium"), "medium")
        self.assertEqual(validate_urgency("high"), "high")

        for bad_urg in ("urgent", "immediate", "critical", "", None):
            with self.subTest(urg=bad_urg):
                with self.assertRaises(ValidationError):
                    validate_urgency(bad_urg)

    def test_can_transition_helper(self):
        """can_transition returns True/False accurately without raising exceptions."""
        unassigned_open = {"status": "open", "assigned_to": None}
        self.assertFalse(can_transition(unassigned_open, "in_progress"))
        self.assertFalse(can_transition(unassigned_open, "resolved"))

        assigned_open = {"status": "open", "assigned_to": "Ada"}
        self.assertTrue(can_transition(assigned_open, "in_progress"))
        self.assertFalse(can_transition(assigned_open, "resolved"))

        in_progress = {"status": "in_progress", "assigned_to": "Ada"}
        self.assertTrue(can_transition(in_progress, "resolved"))
        self.assertFalse(can_transition(in_progress, "open"))

        resolved = {"status": "resolved", "assigned_to": "Ada"}
        self.assertTrue(can_transition(resolved, "open"))
        self.assertFalse(can_transition(resolved, "in_progress"))

    def test_validate_ticket_dict_schema_integrity(self):
        """validate_ticket_dict enforces schema presence, types, and priority consistency."""
        valid_ticket = {
            "id": "T001",
            "title": "Wi-Fi outage",
            "category": "Network",
            "urgency": "high",
            "affected_users": 15,
            "priority": "critical",
            "status": "open",
            "assigned_to": None,
            "notes": [],
        }
        # Valid ticket passes without error
        validate_ticket_dict(valid_ticket, calculate_priority_fn=calculate_priority)

        # Missing required key
        incomplete = copy.deepcopy(valid_ticket)
        del incomplete["category"]
        with self.assertRaises(StorageError):
            validate_ticket_dict(incomplete)

        # Invalid ID format
        bad_id = copy.deepcopy(valid_ticket)
        bad_id["id"] = "INVALID"
        with self.assertRaises(StorageError):
            validate_ticket_dict(bad_id)

        # Inconsistent priority calculation (e.g. tampering)
        tampered_priority = copy.deepcopy(valid_ticket)
        tampered_priority["priority"] = "low"  # High urgency + 15 users must be critical
        with self.assertRaises(StorageError):
            validate_ticket_dict(tampered_priority, calculate_priority_fn=calculate_priority)


if __name__ == "__main__":
    unittest.main()
