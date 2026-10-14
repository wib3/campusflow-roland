import unittest

from campusflow.understanding_check import QUESTIONS, calculate_score


class TestUnderstandingCheck(unittest.TestCase):
    def test_question_bank_has_six_questions(self):
        self.assertEqual(len(QUESTIONS), 6)

    def test_every_question_has_four_options(self):
        for question in QUESTIONS:
            with self.subTest(question=question["question"]):
                self.assertEqual(
                    set(question["options"]),
                    {"A", "B", "C", "D"},
                )
                self.assertIn(question["answer"], question["options"])

    def test_all_correct_answers_score_six(self):
        answers = [question["answer"] for question in QUESTIONS]
        self.assertEqual(calculate_score(answers), 6)

    def test_all_wrong_answers_score_zero(self):
        answers = [
            next(
                option
                for option in question["options"]
                if option != question["answer"]
            )
            for question in QUESTIONS
        ]
        self.assertEqual(calculate_score(answers), 0)

    def test_mixed_answers_score_only_correct_responses(self):
        answers = [
            question["answer"] if index % 2 == 0 else "A"
            for index, question in enumerate(QUESTIONS)
        ]
        expected = sum(
            answer == question["answer"]
            for question, answer in zip(QUESTIONS, answers)
        )
        self.assertEqual(calculate_score(answers), expected)

    def test_no_answers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Exactly six answers"):
            calculate_score([])

    def test_fewer_than_six_answers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Exactly six answers"):
            calculate_score(["B", "C"])

    def test_invalid_answer_letter_is_rejected(self):
        answers = [question["answer"] for question in QUESTIONS]
        answers[0] = "Z"
        with self.assertRaisesRegex(ValueError, "A, B, C, or D"):
            calculate_score(answers)


if __name__ == "__main__":
    unittest.main()


class TestUnderstandingInteraction(unittest.TestCase):
    def test_invalid_choice_is_retried(self):
        from campusflow.understanding_check import run_understanding_check

        inputs = iter(["X", "B", "C", "reason 2", "B", "C", "reason 4", "C", "B"])
        messages = []
        result = run_understanding_check(
            input_fn=lambda prompt: next(inputs),
            output_fn=messages.append,
        )

        self.assertEqual(result["score"], 6)
        self.assertTrue(any("Invalid choice" in msg for msg in messages))

    def test_empty_explanation_is_retried(self):
        from campusflow.understanding_check import run_understanding_check

        inputs = iter(["B", "C", "", "reason 2", "B", "C", "reason 4", "C", "B"])
        messages = []
        result = run_understanding_check(
            input_fn=lambda prompt: next(inputs),
            output_fn=messages.append,
        )

        self.assertEqual(len(result["explanations"]), 2)
        self.assertTrue(any("short explanation" in msg for msg in messages))

    def test_final_score_is_displayed(self):
        from campusflow.understanding_check import run_understanding_check

        inputs = iter(["B", "C", "reason 2", "B", "C", "reason 4", "C", "B"])
        messages = []
        result = run_understanding_check(
            input_fn=lambda prompt: next(inputs),
            output_fn=messages.append,
        )

        self.assertEqual(result["score"], 6)
        self.assertTrue(any("6/6" in msg for msg in messages))
