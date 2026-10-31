from django.contrib import admin
from .admin import AttemptAdmin, ResponseAdmin

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exams.models import Exam, ExamQuestion, Option, Question

from . import services
from .models import Attempt, Response

User = get_user_model()


class AttemptTestBase(TestCase):
    """Shared fixtures: one instructor, two students and a 3-question exam."""

    @classmethod
    def setUpTestData(cls):
        cls.instructor = User.objects.create_user(
            username="ins", email="ins@example.com", password="Passw0rd!x",
            role=User.Role.INSTRUCTOR,
        )
        cls.student = User.objects.create_user(
            username="stu1", email="stu1@example.com", password="Passw0rd!x",
            role=User.Role.STUDENT,
        )
        cls.other = User.objects.create_user(
            username="stu2", email="stu2@example.com", password="Passw0rd!x",
            role=User.Role.STUDENT,
        )

    def make_exam(self, start_offset=-10, end_offset=60, duration=30,
                  published=True, questions=3, marks=2, title="Exam"):
        """Create an exam; offsets are minutes relative to now."""
        now = timezone.now()
        exam = Exam.objects.create(
            title=title,
            created_by=self.instructor,
            start_time=now + timedelta(minutes=start_offset),
            end_time=now + timedelta(minutes=end_offset),
            duration_minutes=duration,
            is_published=published,
        )
        for n in range(1, questions + 1):
            q = Question.objects.create(
                question_text=f"Q{n} of {title}?", created_by=self.instructor
            )
            for i in range(4):
                Option.objects.create(
                    question=q, option_text=f"opt{i}", is_correct=(i == 0)
                )
            ExamQuestion.objects.create(
                exam=exam, question=q, order=n, marks=marks
            )
        return exam

    def eq(self, exam, order):
        return exam.exam_questions.get(order=order)

    def option(self, exam_question, correct):
        return exam_question.question.options.filter(
            is_correct=correct
        ).order_by("id").first()

    def login(self, user=None):
        self.client.force_login(user or self.student)


class DashboardTests(AttemptTestBase):
    def test_lists_only_published_exams_with_details(self):
        self.make_exam(title="Published")
        self.make_exam(title="Hidden draft", published=False)
        self.login()
        resp = self.client.get(reverse("student_dashboard"))
        self.assertContains(resp, "Published")
        self.assertNotContains(resp, "Hidden draft")
        self.assertContains(resp, "30 min")

    def test_status_upcoming_open_closed(self):
        upcoming = self.make_exam(start_offset=30, end_offset=90)
        opened = self.make_exam(start_offset=-5, end_offset=30)
        closed = self.make_exam(start_offset=-90, end_offset=-30)
        self.assertEqual(services.exam_status(upcoming), "Upcoming")
        self.assertEqual(services.exam_status(opened), "Open")
        self.assertEqual(services.exam_status(closed), "Closed")

    def test_status_completed_after_submission(self):
        exam = self.make_exam()
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        attempt.submitted_at = timezone.now()
        attempt.save()
        self.assertEqual(services.exam_status(exam, attempt), "Completed")

    def test_requires_student_role(self):
        self.assertEqual(
            self.client.get(reverse("student_dashboard")).status_code, 302
        )
        self.login(self.instructor)
        self.assertEqual(
            self.client.get(reverse("student_dashboard")).status_code, 403
        )


class InstructionsTests(AttemptTestBase):
    def test_shows_duration_questions_and_total_marks(self):
        exam = self.make_exam(questions=3, marks=2, duration=45, end_offset=90)
        self.login()
        resp = self.client.get(reverse("exam_instructions", args=[exam.id]))
        self.assertContains(resp, "45 minutes")
        self.assertContains(resp, "Number of questions: 3")
        self.assertContains(resp, "Total marks: 6")
        self.assertContains(resp, "Start exam")

    def test_draft_exam_is_404_for_students(self):
        exam = self.make_exam(published=False)
        self.login()
        resp = self.client.get(reverse("exam_instructions", args=[exam.id]))
        self.assertEqual(resp.status_code, 404)

    def test_instructor_gets_403(self):
        exam = self.make_exam()
        self.login(self.instructor)
        resp = self.client.get(reverse("exam_instructions", args=[exam.id]))
        self.assertEqual(resp.status_code, 403)

    def test_no_start_button_when_upcoming(self):
        exam = self.make_exam(start_offset=30, end_offset=90)
        self.login()
        resp = self.client.get(reverse("exam_instructions", args=[exam.id]))
        self.assertNotContains(resp, "Start exam")


class StartExamTests(AttemptTestBase):
    def start(self, exam, follow=False):
        return self.client.post(
            reverse("exam_start", args=[exam.id]), follow=follow
        )

    def test_start_open_exam_creates_attempt(self):
        exam = self.make_exam()
        self.login()
        resp = self.start(exam)
        attempt = Attempt.objects.get(student=self.student, exam=exam)
        self.assertRedirects(
            resp, reverse("attempt_page", args=[attempt.id])
        )
        self.assertIsNone(attempt.submitted_at)
        self.assertEqual(attempt.status, "IN_PROGRESS")

    def test_start_requires_post(self):
        exam = self.make_exam()
        self.login()
        resp = self.client.get(reverse("exam_start", args=[exam.id]))
        self.assertEqual(resp.status_code, 405)

    def test_cannot_start_upcoming_exam(self):
        exam = self.make_exam(start_offset=30, end_offset=90)
        self.login()
        resp = self.start(exam, follow=True)
        self.assertContains(resp, "has not started yet")
        self.assertFalse(Attempt.objects.exists())

    def test_cannot_start_closed_exam(self):
        exam = self.make_exam(start_offset=-90, end_offset=-30)
        self.login()
        resp = self.start(exam, follow=True)
        self.assertContains(resp, "closed")
        self.assertFalse(Attempt.objects.exists())

    def test_cannot_start_draft_exam(self):
        exam = self.make_exam(published=False)
        self.login()
        self.assertEqual(self.start(exam).status_code, 404)

    def test_cannot_start_exam_without_questions(self):
        exam = self.make_exam(questions=0)
        self.login()
        resp = self.start(exam, follow=True)
        self.assertContains(resp, "no questions")
        self.assertFalse(Attempt.objects.exists())

    def test_second_attempt_refused_after_submission(self):
        exam = self.make_exam()
        self.login()
        attempt = Attempt.objects.create(
            student=self.student, exam=exam, submitted_at=timezone.now()
        )
        resp = self.start(exam, follow=True)
        self.assertContains(resp, "already attempted")
        self.assertEqual(Attempt.objects.filter(exam=exam).count(), 1)
        self.assertEqual(Attempt.objects.get().id, attempt.id)

    def test_restart_while_in_progress_resumes_same_attempt(self):
        exam = self.make_exam()
        self.login()
        self.start(exam)
        resp = self.start(exam)
        self.assertEqual(Attempt.objects.filter(exam=exam).count(), 1)
        self.assertEqual(resp.status_code, 302)

    def test_database_enforces_one_attempt_per_student(self):
        exam = self.make_exam()
        Attempt.objects.create(student=self.student, exam=exam)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Attempt.objects.create(student=self.student, exam=exam)

    def test_each_student_gets_own_attempt(self):
        exam = self.make_exam()
        self.login(self.student)
        self.start(exam)
        self.login(self.other)
        self.start(exam)
        self.assertEqual(Attempt.objects.filter(exam=exam).count(), 2)

    def test_instructor_cannot_start(self):
        exam = self.make_exam()
        self.login(self.instructor)
        self.assertEqual(self.start(exam).status_code, 403)


class AttemptDeadlineTests(AttemptTestBase):
    def test_deadline_is_duration_when_window_is_long(self):
        exam = self.make_exam(duration=30, end_offset=120)
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        self.assertEqual(
            attempt.deadline, attempt.started_at + timedelta(minutes=30)
        )

    def test_deadline_is_window_end_when_earlier(self):
        exam = self.make_exam(duration=60, end_offset=10)
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        self.assertEqual(attempt.deadline, exam.end_time)
        self.assertLessEqual(attempt.seconds_remaining(), 10 * 60)

    def test_seconds_remaining_never_negative(self):
        exam = self.make_exam()
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        later = attempt.deadline + timedelta(minutes=5)
        self.assertEqual(attempt.seconds_remaining(later), 0)


class AttemptPageTests(AttemptTestBase):
    def setUp(self):
        self.exam = self.make_exam()
        self.attempt = Attempt.objects.create(
            student=self.student, exam=self.exam
        )
        self.url = reverse("attempt_page", args=[self.attempt.id])
        self.login()

    def test_renders_questions_options_navigator_and_timer(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Q1 of Exam?")
        self.assertContains(resp, 'id="timer"')
        self.assertContains(resp, 'id="navigator"')
        self.assertContains(resp, 'id="prev-btn"')
        self.assertContains(resp, 'id="next-btn"')
        self.assertEqual(len(resp.context["questions"]), 3)
        for q in resp.context["questions"]:
            self.assertEqual(len(q["options"]), 4)

    def test_correct_answers_are_never_sent_to_browser(self):
        resp = self.client.get(self.url)
        self.assertNotContains(resp, "is_correct")
        for q in resp.context["questions"]:
            for option in q["options"]:
                self.assertEqual(set(option), {"id", "text"})

    def test_remaining_time_comes_from_server(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=20)
        )
        resp = self.client.get(self.url)
        remaining = resp.context["remaining_seconds"]
        self.assertTrue(9 * 60 <= remaining <= 10 * 60)

    def test_previously_selected_answer_is_restored(self):
        eq = self.eq(self.exam, 1)
        opt = self.option(eq, correct=False)
        Response.objects.create(
            attempt=self.attempt, exam_question=eq, selected_option=opt
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["questions"][0]["selected"], opt.id)
        self.assertEqual(resp.context["answered_count"], 1)

    def test_other_student_gets_403(self):
        self.login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_after_deadline_page_is_not_shown(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=45)
        )
        resp = self.client.get(self.url, follow=True)
        self.assertContains(resp, "Time is over")

    def test_submitted_attempt_page_is_not_shown(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            submitted_at=timezone.now()
        )
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse("student_dashboard"))

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)


class SaveAnswerTests(AttemptTestBase):
    def setUp(self):
        self.exam = self.make_exam()
        self.attempt = Attempt.objects.create(
            student=self.student, exam=self.exam
        )
        self.url = reverse("attempt_answer", args=[self.attempt.id])
        self.eq1 = self.eq(self.exam, 1)
        self.login()

    def answer(self, eq, option_id):
        return self.client.post(
            self.url, {"question": eq.id, "option": option_id}
        )

    def test_select_answer_is_saved(self):
        opt = self.option(self.eq1, correct=True)
        resp = self.answer(self.eq1, opt.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["answered"], 1)
        saved = Response.objects.get(
            attempt=self.attempt, exam_question=self.eq1
        )
        self.assertEqual(saved.selected_option, opt)

    def test_changing_answer_updates_same_row(self):
        right = self.option(self.eq1, correct=True)
        wrong = self.option(self.eq1, correct=False)
        self.answer(self.eq1, right.id)
        self.answer(self.eq1, wrong.id)
        rows = Response.objects.filter(attempt=self.attempt)
        self.assertEqual(rows.count(), 1)
        self.assertEqual(rows.get().selected_option, wrong)

    def test_clearing_answer_leaves_question_unanswered(self):
        opt = self.option(self.eq1, correct=True)
        self.answer(self.eq1, opt.id)
        resp = self.answer(self.eq1, "")
        self.assertEqual(resp.json()["answered"], 0)
        self.assertIsNone(
            Response.objects.get(attempt=self.attempt).selected_option
        )

    def test_option_from_another_question_is_rejected(self):
        foreign = self.option(self.eq(self.exam, 2), correct=True)
        resp = self.answer(self.eq1, foreign.id)
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Response.objects.exists())

    def test_question_from_another_exam_is_rejected(self):
        other_exam = self.make_exam(title="Other")
        foreign_eq = self.eq(other_exam, 1)
        opt = self.option(foreign_eq, correct=True)
        self.assertEqual(self.answer(foreign_eq, opt.id).status_code, 400)

    def test_garbage_input_is_rejected(self):
        self.assertEqual(
            self.client.post(self.url, {"question": "abc"}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                self.url, {"question": self.eq1.id, "option": "xyz"}
            ).status_code,
            400,
        )

    def test_answer_after_deadline_is_rejected(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=31)
        )
        opt = self.option(self.eq1, correct=True)
        resp = self.answer(self.eq1, opt.id)
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Response.objects.exists())

    def test_answer_on_submitted_attempt_is_rejected(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            submitted_at=timezone.now()
        )
        opt = self.option(self.eq1, correct=True)
        self.assertEqual(self.answer(self.eq1, opt.id).status_code, 403)

    def test_other_student_cannot_save_into_my_attempt(self):
        self.login(self.other)
        opt = self.option(self.eq1, correct=True)
        self.assertEqual(self.answer(self.eq1, opt.id).status_code, 403)
        self.assertFalse(Response.objects.exists())

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

class AdminProtectionTests(AttemptTestBase):
    def setUp(self):
        self.exam = self.make_exam()

        self.submitted_attempt = Attempt.objects.create(
            student=self.student,
            exam=self.exam,
            submitted_at=timezone.now(),
        )

        self.eq1 = self.eq(self.exam, 1)
        self.option1 = self.option(self.eq1, correct=True)

        self.response = Response.objects.create(
            attempt=self.submitted_attempt,
            exam_question=self.eq1,
            selected_option=self.option1,
        )

        self.attempt_admin = AttemptAdmin(Attempt, admin.site)
        self.response_admin = ResponseAdmin(Response, admin.site)

        self.request = type("Request", (), {})()
        self.request.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
        )

    def test_submitted_attempt_cannot_be_changed(self):
        self.assertFalse(
            self.attempt_admin.has_change_permission(
                self.request, self.submitted_attempt
            )
        )

    def test_submitted_attempt_cannot_be_deleted(self):
        self.assertFalse(
            self.attempt_admin.has_delete_permission(
                self.request, self.submitted_attempt
            )
        )

    def test_submitted_attempt_fields_are_read_only(self):
        readonly = self.attempt_admin.get_readonly_fields(
            self.request, self.submitted_attempt
        )

        self.assertIn("student", readonly)
        self.assertIn("exam", readonly)
        self.assertIn("started_at", readonly)
        self.assertIn("submitted_at", readonly)
        self.assertIn("percentage", readonly)

    def test_response_of_submitted_attempt_cannot_be_changed(self):
        self.assertFalse(
            self.response_admin.has_change_permission(
                self.request, self.response
            )
        )

    def test_response_of_submitted_attempt_cannot_be_deleted(self):
        self.assertFalse(
            self.response_admin.has_delete_permission(
                self.request, self.response
            )
        )
