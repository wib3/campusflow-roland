import copy
import json
import os
import shutil
import tempfile
import unittest

from campusflow.exceptions import StorageError
from campusflow.notes import next_note_id
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import generate_next_id


class StorageTests(unittest.TestCase):
    """Test suite for saving and loading tickets via JSON persistence."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.test_dir, "tickets.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_non_existent_file_returns_empty_list(self):
        """Loading from a nonexistent path returns an empty list (fresh start)."""
        non_existent = os.path.join(self.test_dir, "missing.json")
        tickets = load_tickets(non_existent)
        self.assertEqual(tickets, [])

    def test_save_and_load_round_trip(self):
        """Saving tickets and then loading produces the exact same records."""
        sample_tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi down",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            },
            {
                "id": "T002",
                "title": "Mouse broken",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "in_progress",
                "assigned_to": "Ada",
                "notes": [],
            },
        ]
        save_tickets(sample_tickets, self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded = load_tickets(self.storage_file)
        self.assertEqual(loaded, sample_tickets)

    def test_save_creates_nested_directories_automatically(self):
        """save_tickets creates any missing parent directories."""
        nested_file = os.path.join(self.test_dir, "data", "subfolder", "tickets.json")
        sample_tickets = [
            {
                "id": "T001",
                "title": "Test",
                "category": "Other",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]
        save_tickets(sample_tickets, nested_file)
        self.assertTrue(os.path.exists(nested_file))
        loaded = load_tickets(nested_file)
        self.assertEqual(loaded, sample_tickets)

    def test_load_corrupted_json_raises_storage_error_and_preserves_file(self):
        """Corrupted JSON raises StorageError without deleting the corrupted file."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid json content, missing brackets:")

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

        # File must NOT be deleted
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("invalid json content", content)

    def test_load_non_list_json_raises_storage_error(self):
        """If JSON contains a root object that is not a list, raise StorageError."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({"not": "a list"}, f)

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

    def test_load_list_with_non_dict_elements_raises_storage_error(self):
        """If JSON list contains elements that are not dicts, raise StorageError."""
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(["string_item", 123], f)

        with self.assertRaises(StorageError):
            load_tickets(self.storage_file)

    def test_save_non_list_raises_storage_error(self):
        """Passing a non-list to save_tickets raises StorageError."""
        with self.assertRaises(StorageError):
            save_tickets({"not": "a list"}, self.storage_file)  # type: ignore

    def test_case12_saving_and_loading_preserves_notes_and_next_ids(self):
        """Case 12: Saving and loading preserves all notes and guarantees ID continuity."""
        tickets = [
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
                        "message": "Power-cycled access points.",
                    },
                    {
                        "note_id": "N002",
                        "author": "Bola",
                        "message": "Checking gateway routes.",
                    },
                ],
            }
        ]
        save_tickets(tickets, self.storage_file)
        loaded = load_tickets(self.storage_file)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(loaded[0]["notes"]), 2)
        self.assertEqual(loaded[0]["notes"][0]["note_id"], "N001")
        self.assertEqual(loaded[0]["notes"][1]["note_id"], "N002")

        # Invariant: next ticket ID and next note ID do not collide after reload
        self.assertEqual(generate_next_id(loaded), "T002")
        self.assertEqual(next_note_id(loaded[0]), "N003")

    def test_case13_duplicate_ticket_id_rejected_without_state_loss(self):
        """Duplicate IDs in storage are rejected without mutating existing memory."""
        in_memory_tickets = [
            {
                "id": "T001",
                "title": "Existing in-memory ticket",
                "category": "Software",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]
        snapshot = copy.deepcopy(in_memory_tickets)

        duplicate_data = [
            {
                "id": "T001",
                "title": "First ticket",
                "category": "Network",
                "urgency": "high",
                "affected_users": 10,
                "priority": "critical",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            },
            {
                "id": "T001",
                "title": "Second ticket with same ID",
                "category": "Hardware",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
                "notes": [],
            },
        ]

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(duplicate_data, f)

        with self.assertRaises(StorageError) as ctx:
            load_tickets(self.storage_file)

        self.assertIn("Duplicate ticket ID", str(ctx.exception))
        self.assertEqual(
            in_memory_tickets,
            snapshot,
            "A failed load must not mutate the caller's existing ticket list.",
        )

    def test_failed_load_validates_migrated_copies(self):
        """Legacy migration is applied to copies, not decoded source records."""
        from unittest.mock import patch
        from campusflow import storage

        data = [
            {
                "id": "T001",
                "title": "Valid legacy ticket",
                "category": "Software",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            },
            {
                "id": "T002",
                "title": "Invalid ticket",
                "category": "InvalidCategory",
                "urgency": "low",
                "affected_users": 1,
                "priority": "low",
                "status": "open",
                "assigned_to": None,
            },
        ]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        original_validate = storage.validate_ticket_dict
        validated_records = []

        def record_validation(ticket, **kwargs):
            validated_records.append(ticket)
            return original_validate(ticket, **kwargs)

        with patch(
            "campusflow.storage.validate_ticket_dict",
            side_effect=record_validation,
        ):
            with self.assertRaises(StorageError):
                load_tickets(self.storage_file)

        # Both records were copied and migrated before validation.
        self.assertEqual(len(validated_records), 2)
        self.assertTrue(all("notes" in ticket for ticket in validated_records))
        self.assertIsNot(validated_records[0], data[0])
        self.assertIsNot(validated_records[1], data[1])

    def test_legacy_ticket_without_notes_is_migrated_on_successful_load(self):
        """A valid legacy ticket receives an empty notes list when loaded."""
        legacy_ticket = {
            "id": "T001",
            "title": "Legacy ticket",
            "category": "Software",
            "urgency": "low",
            "affected_users": 1,
            "priority": "low",
            "status": "open",
            "assigned_to": None,
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([legacy_ticket], f)

        loaded = load_tickets(self.storage_file)

        self.assertEqual(loaded[0]["notes"], [])
        self.assertNotIn("notes", legacy_ticket)

    def test_bug_hunter_priority_inconsistency_rejected(self):
        """Bug-Hunter (Engineer A): Detects maliciously tampered priority in storage.

        Initial state: File contains ticket with urgency='high' and affected_users=15,
        but priority='low' (violating Rule 1).
        Expected result: StorageError raised rejecting the tampered file.
        """
        tampered = [
            {
                "id": "T001",
                "title": "Tampered record",
                "category": "Network",
                "urgency": "high",
                "affected_users": 15,
                "priority": "low",  # Inconsistent: high + 15 MUST be 'critical'
                "status": "open",
                "assigned_to": None,
                "notes": [],
            }
        ]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(tampered, f)

        with self.assertRaises(StorageError) as ctx:
            load_tickets(self.storage_file)
        self.assertIn("inconsistent priority", str(ctx.exception))

    def test_bug_hunter_in_progress_without_assignee_rejected(self):
        """Bug-Hunter (Engineer A): Detects invalid lifecycle state in storage.

        Initial state: File contains ticket with status='in_progress' but assigned_to=None.
        Expected result: StorageError raised, preventing illegal ticket state injection.
        """
        illegal_state = [
            {
                "id": "T001",
                "title": "Unassigned progress ticket",
                "category": "Hardware",
                "urgency": "medium",
                "affected_users": 3,
                "priority": "medium",
                "status": "in_progress",  # Invariant violation: in_progress requires assignee
                "assigned_to": None,
                "notes": [],
            }
        ]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(illegal_state, f)

        with self.assertRaises(StorageError) as ctx:
            load_tickets(self.storage_file)
        self.assertIn("in_progress but has no assigned staff", str(ctx.exception))



if __name__ == "__main__":
    unittest.main()
