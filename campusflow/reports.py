"""Read-only queue and reporting functions."""

PRIORITIES = ("critical", "high", "medium", "low")
STATUSES = ("open", "in_progress", "resolved")


def get_work_queue(tickets):
    """Return open tickets by priority, then numeric ID, without changing storage."""
    priority_rank = {priority: rank for rank, priority in enumerate(PRIORITIES)}
    return sorted(
        (ticket for ticket in tickets if ticket["status"] == "open"),
        key=lambda ticket: (priority_rank[ticket["priority"]], int(ticket["id"][1:])),
    )


def generate_report(tickets):
    """Return ticket counts and resolution metrics without modifying tickets."""
    categories = ("Network", "Hardware", "Software", "Other")
    report = {
        "total": 0,
        "by_status": dict.fromkeys(STATUSES, 0),
        "by_priority": dict.fromkeys(PRIORITIES, 0),
        "by_category": dict.fromkeys(categories, 0),
        "unresolved": 0,
        "resolved": 0,
        "resolution_percentage": 0.0,
    }

    for ticket in tickets:
        status = ticket["status"]
        report["by_status"][status] += 1
        report["by_priority"][ticket["priority"]] += 1
        report["by_category"][ticket["category"]] += 1
        report["total"] += 1

        if status == "resolved":
            report["resolved"] += 1
        else:
            report["unresolved"] += 1

    if report["total"]:
        report["resolution_percentage"] = (
            report["resolved"] / report["total"]
        ) * 100

    return report
