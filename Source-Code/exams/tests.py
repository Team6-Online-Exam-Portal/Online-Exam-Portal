
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .forms import ExamForm
from .models import Exam, Question, Option

User = get_user_model()


# ==================================================
# FR-4: Exam Form Tests
# ==================================================

class ExamFormTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="instructor1",
            email="instructor1@example.com",
            password="TestPass123!",
            role=User.Role.INSTRUCTOR,
        )

        self.question = Question.objects.create(
            question_text="What is Python?",
            created_by=self.instructor,
        )

    def valid_form_data(self):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        return {
            "title": "Python Exam",
            "description": "Basic Python questions",
            "start_time": start.strftime("%Y-%m-%dT%H:%M"),
            "end_time": end.strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": 60,
            "questions": [self.question.pk],
        }

    def test_valid_exam_form(self):
        form = ExamForm(
            data=self.valid_form_data(),
            user=self.instructor,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_exam_requires_at_least_one_question(self):
        data = self.valid_form_data()
        data["questions"] = []

        form = ExamForm(data=data, user=self.instructor)

        self.assertFalse(form.is_valid())
        self.assertIn("questions", form.errors)

    def test_duration_must_be_between_1_and_180(self):
        data = self.valid_form_data()
        data["duration_minutes"] = 181

        form = ExamForm(data=data, user=self.instructor)

        self.assertFalse(form.is_valid())
        self.assertIn("duration_minutes", form.errors)

    def test_end_time_must_follow_start_time(self):
        data = self.valid_form_data()
        data["end_time"] = data["start_time"]

        form = ExamForm(data=data, user=self.instructor)

        self.assertFalse(form.is_valid())
        self.assertIn("end_time", form.errors)

    def test_duration_cannot_exceed_exam_window(self):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(minutes=30)

        data = self.valid_form_data()
        data["start_time"] = start.strftime("%Y-%m-%dT%H:%M")
        data["end_time"] = end.strftime("%Y-%m-%dT%H:%M")
        data["duration_minutes"] = 60

        form = ExamForm(data=data, user=self.instructor)

        self.assertFalse(form.is_valid())
        self.assertIn("duration_minutes", form.errors)

    def test_instructor_only_sees_own_questions(self):
        another_instructor = User.objects.create_user(
            username="instructor2",
            email="instructor2@example.com",
            password="TestPass123!",
            role=User.Role.INSTRUCTOR,
        )

        other_question = Question.objects.create(
            question_text="Private question",
            created_by=another_instructor,
        )

        form = ExamForm(user=self.instructor)

        available_ids = list(
            form.fields["questions"].queryset.values_list(
                "id", flat=True
            )
        )

        self.assertIn(self.question.pk, available_ids)
        self.assertNotIn(other_question.pk, available_ids)


# ==================================================
# FR-3: Question Management Tests
# ==================================================

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

        question = Question.objects.get(
            question_text="What is 2 + 2?"
        )

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
