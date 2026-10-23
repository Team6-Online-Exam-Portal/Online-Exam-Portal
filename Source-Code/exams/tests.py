
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from .forms import ExamForm
from .models import Question


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
