import unittest
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout

from main import handle_search_tickets


def make_ticket():
    return {
        "id": "T001",
        "title": "WiFi connection lost",
        "category": "Network",
        "urgency": "high",
        "affected_users": 2,
        "priority": "high",
        "status": "open",
        "assigned_to": None,
    }


class SearchCliTests(unittest.TestCase):
    def test_invalid_category_reprompts_until_valid_choice(self):
        tickets = [make_ticket()]
        user_inputs = [
            "wifi",       # Title query
            "invalid",    # Invalid category
            "Network",    # Valid category retry
            "open",       # Status
            "high",       # Priority
        ]
        output = StringIO()

        with patch("builtins.input", side_effect=user_inputs) as mocked_input:
            with redirect_stdout(output):
                handle_search_tickets(tickets)

        self.assertEqual(mocked_input.call_count, 5)
        self.assertIn("Invalid category", output.getvalue())
        self.assertIn("T001", output.getvalue())
        self.assertIn("Matching tickets: 1", output.getvalue())

    def test_no_matching_tickets_displays_helpful_message(self):
        tickets = [make_ticket()]
        user_inputs = ["printer", "", "", ""]

        output = StringIO()
        with patch("builtins.input", side_effect=user_inputs):
            with redirect_stdout(output):
                handle_search_tickets(tickets)

        self.assertIn(
            "No tickets matched your search and filters.",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
