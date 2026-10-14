import copy
import unittest

from campusflow.search import search_tickets


def ticket(ticket_id, title, category, status, priority):
    return {
        "id": ticket_id,
        "title": title,
        "category": category,
        "status": status,
        "priority": priority,
        "assigned_to": None,
    }


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [
            ticket("T001", "WiFi connection lost", "Network", "open", "high"),
            ticket("T002", "WiFi password reset", "Software", "resolved", "low"),
            ticket("T003", "Printer not working", "Hardware", "open", "medium"),
        ]

    def test_title_search_is_case_insensitive_substring(self):
        results = search_tickets(self.tickets, title_query="WIFI")
        self.assertEqual([item["id"] for item in results], ["T001", "T002"])

    def test_combined_filters_use_and(self):
        results = search_tickets(
            self.tickets,
            title_query="wifi",
            category="Network",
            status="open",
            priority="high",
        )
        self.assertEqual([item["id"] for item in results], ["T001"])

    def test_nonmatching_combined_filters_return_empty_list(self):
        results = search_tickets(
            self.tickets,
            title_query="wifi",
            category="Hardware",
        )
        self.assertEqual(results, [])

    def test_empty_filters_return_all_tickets(self):
        results = search_tickets(self.tickets)
        self.assertEqual([item["id"] for item in results], ["T001", "T002", "T003"])

    def test_invalid_filter_is_rejected(self):
        with self.assertRaises(ValueError):
            search_tickets(self.tickets, status="waiting")

    def test_search_does_not_modify_ticket_collection(self):
        before = copy.deepcopy(self.tickets)
        search_tickets(self.tickets, title_query="wifi", status="open")
        self.assertEqual(self.tickets, before)


if __name__ == "__main__":
    unittest.main()
