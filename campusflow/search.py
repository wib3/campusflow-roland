"""Read-only ticket search and filtering functions."""

ALLOWED_CATEGORIES = ("Network", "Hardware", "Software", "Other")
ALLOWED_STATUSES = ("open", "in_progress", "resolved")
ALLOWED_PRIORITIES = ("critical", "high", "medium", "low")


def search_tickets(tickets, title_query="", category=None, status=None, priority=None):
    """Search ticket titles and apply all supplied filters using AND."""
    query = title_query.casefold().strip()

    results = [
        ticket for ticket in tickets
        if query in ticket["title"].casefold()
    ]

    if category is not None:
        if category not in ALLOWED_CATEGORIES:
            raise ValueError("Invalid category filter.")
        results = [ticket for ticket in results if ticket["category"] == category]

    if status is not None:
        if status not in ALLOWED_STATUSES:
            raise ValueError("Invalid status filter.")
        results = [ticket for ticket in results if ticket["status"] == status]

    if priority is not None:
        if priority not in ALLOWED_PRIORITIES:
            raise ValueError("Invalid priority filter.")
        results = [ticket for ticket in results if ticket["priority"] == priority]

    return results
