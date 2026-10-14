import unittest
from contextlib import redirect_stdout
from io import StringIO

from main import handle_generate_report


def ticket(ticket_id, priority, status, category):
    return {
        "id": ticket_id,
        "title": f"Ticket {ticket_id}",
        "category": category,
        "urgency": "medium",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": None,
    }


class ReportCliTests(unittest.TestCase):
    def test_report_displays_all_metrics_and_breakdowns(self):
        tickets = [
            ticket("T001", "critical", "resolved", "Network"),
            ticket("T002", "high", "in_progress", "Hardware"),
            ticket("T003", "low", "open", "Software"),
        ]

        output = StringIO()
        with redirect_stdout(output):
            handle_generate_report(tickets)

        displayed = output.getvalue()
        self.assertIn("Total Tickets: 3", displayed)
        self.assertIn("Unresolved Tickets: 2", displayed)
        self.assertIn("Resolved Tickets: 1", displayed)
        self.assertIn("Resolution Rate: 33.3%", displayed)
        self.assertIn("Breakdown by Status:", displayed)
        self.assertIn("Breakdown by Priority:", displayed)
        self.assertIn("Breakdown by Category:", displayed)
        self.assertIn("Network", displayed)
        self.assertIn("Hardware", displayed)
        self.assertIn("Software", displayed)

    def test_empty_report_displays_zero_metrics(self):
        output = StringIO()
        with redirect_stdout(output):
            handle_generate_report([])

        displayed = output.getvalue()
        self.assertIn("Total Tickets: 0", displayed)
        self.assertIn("Unresolved Tickets: 0", displayed)
        self.assertIn("Resolved Tickets: 0", displayed)
        self.assertIn("Resolution Rate: 0.0%", displayed)
        self.assertIn("Breakdown by Category:", displayed)


if __name__ == "__main__":
    unittest.main()
