
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Question, Option

User = get_user_model()


class QuestionManagementTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="TestPass@123",
            role=User.Role.INSTRUCTOR,
        )
        self.client.login(
            email="teacher@example.com",
            password="TestPass@123",
        )

    def test_instructor_can_view_questions(self):
        response = self.client.get(reverse("question_list"))
        self.assertEqual(response.status_code, 200)

    def test_instructor_can_create_question(self):
        response = self.client.post(
            reverse("question_create"),
            {
                "question_text": "What is 2 + 2?",
                "options-TOTAL_FORMS": "4",
                "options-INITIAL_FORMS": "0",
                "options-MIN_NUM_FORMS": "4",
                "options-MAX_NUM_FORMS": "4",
                "options-0-option_text": "4",
                "options-0-is_correct": "on",
                "options-1-option_text": "3",
                "options-2-option_text": "5",
                "options-3-option_text": "6",
            },
        )
        self.assertRedirects(response, reverse("question_list"))
        self.assertTrue(
            Question.objects.filter(
                question_text="What is 2 + 2?",
                created_by=self.teacher,
            ).exists()
        )
        question = Question.objects.get(question_text="What is 2 + 2?")
        self.assertEqual(question.options.count(), 4)
        self.assertEqual(
            question.options.filter(is_correct=True).count(), 1
        )

    def test_duplicate_options_are_rejected(self):
        response = self.client.post(
            reverse("question_create"),
            {
                "question_text": "Duplicate test?",
                "options-TOTAL_FORMS": "4",
                "options-INITIAL_FORMS": "0",
                "options-MIN_NUM_FORMS": "4",
                "options-MAX_NUM_FORMS": "4",
                "options-0-option_text": "Same",
                "options-0-is_correct": "on",
                "options-1-option_text": "Same",
                "options-2-option_text": "Other",
                "options-3-option_text": "Last",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Question.objects.filter(
                question_text="Duplicate test?"
            ).exists()
        )

    def test_question_requires_one_correct_option(self):
        response = self.client.post(
            reverse("question_create"),
            {
                "question_text": "Correct answer test?",
                "options-TOTAL_FORMS": "4",
                "options-INITIAL_FORMS": "0",
                "options-MIN_NUM_FORMS": "4",
                "options-MAX_NUM_FORMS": "4",
                "options-0-option_text": "One",
                "options-1-option_text": "Two",
                "options-2-option_text": "Three",
                "options-3-option_text": "Four",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Question.objects.filter(
                question_text="Correct answer test?"
            ).exists()
        )
