"""NFR-01 performance regression tests.

These do not measure wall-clock speed of the machine (that is what
Testing/performance/load_test.py is for). They guard the thing that makes
pages slow as data grows: queries that run once per row. Each test builds a
small and a large data set and requires the SAME number of queries.
"""
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from exams.models import Exam, ExamQuestion, Option, Question

from .models import Attempt, Response

User = get_user_model()
PAGE_LIMIT_SECONDS = 3.0  # SRS NFR-1: normal pages load within 3 seconds


class PerformanceBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instructor = User.objects.create_user(
            username="perf_ins", email="perf_ins@example.com",
            password="Passw0rd!x", role=User.Role.INSTRUCTOR,
        )
        cls.student = User.objects.create_user(
            username="perf_stu", email="perf_stu@example.com",
            password="Passw0rd!x", role=User.Role.STUDENT,
        )

    def make_exam(self, questions, title="Perf exam", published=True,
                  start=-10, end=120, duration=60):
        now = timezone.now()
        exam = Exam.objects.create(
            title=title, created_by=self.instructor,
            start_time=now + timedelta(minutes=start),
            end_time=now + timedelta(minutes=end),
            duration_minutes=duration, is_published=published,
        )
        for order in range(1, questions + 1):
            question = Question.objects.create(
                question_text=f"{title} Q{order}?", marks=1,
                created_by=self.instructor,
            )
            Option.objects.bulk_create(
                Option(question=question, option_text=f"opt{i}",
                       is_correct=(i == 0))
                for i in range(4)
            )
            ExamQuestion.objects.create(
                exam=exam, question=question, order=order, marks=1
            )
        return exam

    def count_queries(self, url, user=None):
        self.client.force_login(user or self.student)
        with CaptureQueriesContext(connection) as ctx:
            started = time.perf_counter()
            response = self.client.get(url)
            elapsed = time.perf_counter() - started
        self.assertEqual(response.status_code, 200, url)
        self.assertLess(elapsed, PAGE_LIMIT_SECONDS)
        return len(ctx)


class StudentDashboardQueryTests(PerformanceBase):
    def test_dashboard_query_count_does_not_grow_with_exams(self):
        self.make_exam(2, title="First")
        small = self.count_queries(reverse("student_dashboard"))
        for n in range(15):
            self.make_exam(3, title=f"Extra {n}")
        large = self.count_queries(reverse("student_dashboard"))
        self.assertEqual(small, large)

    def test_dashboard_shows_correct_counts_and_marks(self):
        exam = self.make_exam(3)
        ExamQuestion.objects.filter(
            exam=exam, order=3
        ).update(marks=5)
        rows = None
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_dashboard"))
        rows = response.context["rows"]
        self.assertEqual(rows[0]["question_count"], 3)
        self.assertEqual(rows[0]["total_marks"], 7)

    def test_dashboard_exam_without_questions_has_zero_marks(self):
        self.make_exam(0, title="Empty")
        self.client.force_login(self.student)
        rows = self.client.get(reverse("student_dashboard")).context["rows"]
        self.assertEqual(rows[0]["question_count"], 0)
        self.assertEqual(rows[0]["total_marks"], 0)


class InstructorListQueryTests(PerformanceBase):
    def test_exam_list_query_count_does_not_grow_with_exams(self):
        self.make_exam(1, title="First", published=False)
        small = self.count_queries(reverse("exam_list"), self.instructor)
        for n in range(15):
            self.make_exam(1, title=f"Extra {n}", published=False)
        large = self.count_queries(reverse("exam_list"), self.instructor)
        self.assertEqual(small, large)

    def test_exam_list_still_blocks_edit_when_attempts_exist(self):
        exam = self.make_exam(1, title="Locked")
        self.make_exam(1, title="Editable", published=False)
        Attempt.objects.create(student=self.student, exam=exam)
        self.client.force_login(self.instructor)
        html = self.client.get(reverse("exam_list")).content.decode()
        self.assertEqual(html.count("Cannot edit or delete"), 1)

    def test_question_list_query_count_does_not_grow_with_questions(self):
        self.make_exam(1, title="First", published=False)
        small = self.count_queries(reverse("question_list"), self.instructor)
        for n in range(15):
            self.make_exam(2, title=f"Extra {n}", published=False)
        large = self.count_queries(reverse("question_list"), self.instructor)
        self.assertEqual(small, large)


class AttemptQueryTests(PerformanceBase):
    def start(self, exam):
        return Attempt.objects.create(student=self.student, exam=exam)

    def test_attempt_page_query_count_is_independent_of_exam_size(self):
        small_exam = self.make_exam(3, title="Small")
        small_attempt = self.start(small_exam)
        small = self.count_queries(
            reverse("attempt_page", args=[small_attempt.id])
        )
        other = User.objects.create_user(
            username="perf_stu2", email="perf_stu2@example.com",
            password="Passw0rd!x", role=User.Role.STUDENT,
        )
        big_exam = self.make_exam(50, title="Big")
        big_attempt = Attempt.objects.create(student=other, exam=big_exam)
        large = self.count_queries(
            reverse("attempt_page", args=[big_attempt.id]), other
        )
        self.assertEqual(small, large)

    def test_save_answer_uses_few_queries(self):
        exam = self.make_exam(5)
        attempt = self.start(exam)
        eq = exam.exam_questions.get(order=1)
        option = eq.question.options.filter(is_correct=True).first()
        self.client.force_login(self.student)
        payload = {"question": eq.id, "option": option.id}
        url = reverse("attempt_answer", args=[attempt.id])
        self.client.post(url, payload)  # first save creates the row
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx), 11, [q["sql"][:60] for q in ctx])
        self.assertEqual(Response.objects.filter(attempt=attempt).count(), 1)

    def test_fifty_question_attempt_page_loads_within_three_seconds(self):
        exam = self.make_exam(50, title="Fifty")
        attempt = self.start(exam)
        self.count_queries(reverse("attempt_page", args=[attempt.id]))


class ResultsQueryTests(PerformanceBase):
    """FR-7 pages: the query count must not grow with the number of rows."""

    def submit(self, student, exam, answer_all=False):
        attempt = Attempt.objects.create(student=student, exam=exam)
        Attempt.objects.filter(pk=attempt.pk).update(
            submitted_at=timezone.now(), score=1, percentage="50.00"
        )
        if answer_all:
            for eq in exam.exam_questions.select_related("question"):
                Response.objects.create(
                    attempt=attempt, exam_question=eq,
                    selected_option=eq.question.options.first(),
                )
        return attempt

    def test_student_history_query_count_does_not_grow_with_attempts(self):
        self.submit(self.student, self.make_exam(2, title="First"))
        small = self.count_queries(reverse("student_history"))
        for n in range(15):
            self.submit(self.student, self.make_exam(2, title=f"Extra {n}"))
        large = self.count_queries(reverse("student_history"))
        self.assertEqual(small, large)

    def test_instructor_report_query_count_does_not_grow_with_attempts(self):
        exam = self.make_exam(2, title="Reported")
        self.submit(self.student, exam)
        url = reverse("instructor_exam_report", args=[exam.id])
        small = self.count_queries(url, self.instructor)
        for n in range(15):
            extra = User.objects.create_user(
                username=f"perf_extra{n}", email=f"perf_extra{n}@example.com",
                password="Passw0rd!x", role=User.Role.STUDENT,
            )
            self.submit(extra, exam)
        large = self.count_queries(url, self.instructor)
        self.assertEqual(small, large)

    def test_question_review_query_count_is_independent_of_exam_size(self):
        small_exam = self.make_exam(3, title="Small", start=-120, end=-60)
        small_attempt = self.submit(self.student, small_exam, answer_all=True)
        small = self.count_queries(
            reverse("question_review", args=[small_attempt.id])
        )
        big_exam = self.make_exam(50, title="Big", start=-120, end=-60)
        big_attempt = self.submit(self.student, big_exam, answer_all=True)
        large = self.count_queries(
            reverse("question_review", args=[big_attempt.id])
        )
        self.assertEqual(small, large)

    def test_review_still_shows_your_answer_and_the_correct_one(self):
        exam = self.make_exam(2, title="Review", start=-120, end=-60)
        attempt = self.submit(self.student, exam, answer_all=True)
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("question_review", args=[attempt.id])
        )
        rows = response.context["review_rows"]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertTrue(row["correct_option"].is_correct)
