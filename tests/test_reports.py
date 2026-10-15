import copy
import unittest

from campusflow.reports import generate_report, get_work_queue


def ticket(ticket_id, priority, status="open", category="Software"):
    return {
        "id": ticket_id,
        "priority": priority,
        "status": status,
        "category": category,
    }


class ReportsTests(unittest.TestCase):
    def test_queue_priority_order(self):
        tickets = [ticket("T001", "low"), ticket("T002", "medium"),
                   ticket("T003", "high"), ticket("T004", "critical")]
        self.assertEqual([t["id"] for t in get_work_queue(tickets)],
                         ["T004", "T003", "T002", "T001"])

    def test_queue_ties_use_numeric_ids_beyond_three_digits(self):
        tickets = [ticket("T1000", "high"), ticket("T010", "high"), ticket("T002", "high")]
        self.assertEqual([t["id"] for t in get_work_queue(tickets)],
                         ["T002", "T010", "T1000"])

    def test_queue_excludes_in_progress_and_resolved(self):
        tickets = [ticket("T001", "low"), ticket("T002", "critical", "in_progress"),
                   ticket("T003", "critical", "resolved")]
        self.assertEqual(get_work_queue(tickets), [tickets[0]])

    def test_queue_does_not_reorder_or_modify_storage(self):
        tickets = [ticket("T002", "low"), ticket("T001", "critical")]
        before = copy.deepcopy(tickets)
        get_work_queue(tickets)
        self.assertEqual(tickets, before)

    def test_empty_queue(self):
        self.assertEqual(get_work_queue([]), [])

    def test_empty_report_includes_zero_counts(self):
        self.assertEqual(generate_report([]), {
            "total": 0,
            "by_status": {"open": 0, "in_progress": 0, "resolved": 0},
            "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_category": {"Network": 0, "Hardware": 0, "Software": 0, "Other": 0},
            "unresolved": 0,
            "resolved": 0,
            "resolution_percentage": 0.0,
        })

    def test_report_counts_every_ticket_without_mutation(self):
        tickets = [ticket("T001", "critical"), ticket("T002", "high", "in_progress"),
                   ticket("T003", "low", "resolved"), ticket("T004", "high")]
        before = copy.deepcopy(tickets)
        self.assertEqual(generate_report(tickets), {
            "total": 4,
            "by_status": {"open": 2, "in_progress": 1, "resolved": 1},
            "by_priority": {"critical": 1, "high": 2, "medium": 0, "low": 1},
            "by_category": {"Network": 0, "Hardware": 0, "Software": 4, "Other": 0},
            "unresolved": 3,
            "resolved": 1,
            "resolution_percentage": 25.0,
        })
        self.assertEqual(tickets, before)

    def test_report_counts_by_category(self):
        tickets = [
            ticket("T001", "critical", category="Network"),
            ticket("T002", "high", category="Hardware"),
            ticket("T003", "low", category="Network"),
            ticket("T004", "medium", category="Other"),
        ]

        report = generate_report(tickets)

        self.assertEqual(report["by_category"], {
            "Network": 2,
            "Hardware": 1,
            "Software": 0,
            "Other": 1,
        })

    def test_report_counts_resolved_and_unresolved(self):
        tickets = [
            ticket("T001", "critical", "open"),
            ticket("T002", "high", "in_progress"),
            ticket("T003", "low", "resolved"),
        ]

        report = generate_report(tickets)

        self.assertEqual(report["unresolved"], 2)
        self.assertEqual(report["resolved"], 1)

    def test_report_resolution_percentage_and_empty_dataset(self):
        tickets = [
            ticket("T001", "critical", "resolved"),
            ticket("T002", "high", "open"),
            ticket("T003", "low", "in_progress"),
            ticket("T004", "medium", "resolved"),
        ]

        self.assertEqual(generate_report(tickets)["resolution_percentage"], 50.0)
        self.assertEqual(generate_report([])["resolution_percentage"], 0.0)
