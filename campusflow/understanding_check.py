"""Question bank and scoring helpers for the CampusFlow understanding check."""

QUESTIONS = [
    {
        "question": "An unassigned open ticket is moved to in_progress. What should happen?",
        "options": {
            "A": "Assign it automatically",
            "B": "Reject the change and preserve all data",
            "C": "Resolve the ticket",
            "D": "Delete the ticket",
        },
        "answer": "B",
    },
    {
        "question": "What is the resolution percentage when there are zero tickets?",
        "options": {
            "A": "100%",
            "B": "Undefined; crash the application",
            "C": "0%",
            "D": "1%",
        },
        "answer": "C",
    },
    {
        "question": "Title='wifi', category='Network', status='open': what should combined filters return?",
        "options": {
            "A": "Tickets matching any one filter",
            "B": "Only tickets matching every supplied filter",
            "C": "All Network tickets",
            "D": "All open tickets",
        },
        "answer": "B",
    },
    {
        "question": "A resolved ticket receives an Add Note request. What should happen?",
        "options": {
            "A": "Add the note immediately",
            "B": "Change the ticket to open automatically",
            "C": "Reject the note until the ticket is reopened",
            "D": "Delete its existing notes",
        },
        "answer": "C",
    },
    {
        "question": "A JSON file contains duplicate ticket IDs. What should loading do?",
        "options": {
            "A": "Keep both records",
            "B": "Silently delete one record",
            "C": "Reject the load without changing current memory",
            "D": "Rename one ID automatically",
        },
        "answer": "C",
    },
    {
        "question": "A PR changes validation but has no negative tests. What is the appropriate review action?",
        "options": {
            "A": "Approve immediately",
            "B": "Request focused negative tests and reasoning",
            "C": "Delete the PR",
            "D": "Ignore the missing tests",
        },
        "answer": "B",
    },
]


def calculate_score(answers):
    """Return the number of correct answers, from zero to six."""
    if len(answers) != len(QUESTIONS):
        raise ValueError("Exactly six answers are required.")

    normalized_answers = [answer.strip().upper() for answer in answers]
    if any(answer not in {"A", "B", "C", "D"} for answer in normalized_answers):
        raise ValueError("Answers must be A, B, C, or D.")

    return sum(
        answer == question["answer"]
        for question, answer in zip(QUESTIONS, normalized_answers)
    )


def run_understanding_check(input_fn=input, output_fn=print):
    """Run six scenarios, retry invalid choices, and collect two explanations."""
    answers = []
    explanations = []

    for index, question in enumerate(QUESTIONS, start=1):
        output_fn(f"\nQ{index}. {question['question']}")
        for letter, option in question["options"].items():
            output_fn(f"  {letter}. {option}")

        while True:
            choice = input_fn("Your answer (A/B/C/D): ").strip().upper()
            if choice in {"A", "B", "C", "D"}:
                answers.append(choice)
                break
            output_fn("Invalid choice. Please enter A, B, C, or D.")

        if index in {2, 4}:
            explanation = input_fn("Briefly explain your reasoning: ").strip()
            while not explanation:
                output_fn("Please enter a short explanation.")
                explanation = input_fn("Briefly explain your reasoning: ").strip()
            explanations.append(explanation)

    score = calculate_score(answers)
    output_fn(f"\nUnderstanding check score: {score}/6")
    return {"score": score, "answers": answers, "explanations": explanations}
