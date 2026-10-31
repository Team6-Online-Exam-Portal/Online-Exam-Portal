from datetime import timedelta

from decimal import Decimal
from time import perf_counter
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import DatabaseError, IntegrityError, transaction
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
        self.assertContains(resp, "Time is up")
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.is_submitted)

    def test_submitted_attempt_page_goes_to_result(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            submitted_at=timezone.now()
        )
        resp = self.client.get(self.url)
        self.assertRedirects(
            resp, reverse("attempt_result", args=[self.attempt.id])
        )

    def test_attempt_page_is_not_cached(self):
        resp = self.client.get(self.url)
        self.assertIn("no-store", resp["Cache-Control"])

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


# ----------------------------------------------------------------- FR-6 ----

class EvaluationTests(AttemptTestBase):
    """Scoring rules: full marks per correct answer, no negative marking."""

    def attempt_with(self, exam, picks):
        """picks: {order: 'right' | 'wrong' | None}; absent = untouched."""
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        for order, pick in picks.items():
            eq = self.eq(exam, order)
            option = None
            if pick == "right":
                option = self.option(eq, correct=True)
            elif pick == "wrong":
                option = self.option(eq, correct=False)
            Response.objects.create(
                attempt=attempt, exam_question=eq, selected_option=option
            )
        return attempt

    def test_all_correct_gets_full_marks(self):
        exam = self.make_exam(questions=3, marks=2)
        attempt = self.attempt_with(
            exam, {1: "right", 2: "right", 3: "right"}
        )
        done = services.evaluate_and_submit(attempt)
        self.assertEqual(done.score, 6)
        self.assertEqual(done.percentage, Decimal("100.00"))
        self.assertIsNotNone(done.submitted_at)

    def test_mixed_answers_score_only_correct_ones(self):
        exam = self.make_exam(questions=3, marks=2)
        attempt = self.attempt_with(exam, {1: "right", 2: "wrong", 3: None})
        done = services.evaluate_and_submit(attempt)
        self.assertEqual(done.score, 2)
        self.assertEqual(done.percentage, Decimal("33.33"))

    def test_no_negative_marking(self):
        exam = self.make_exam(questions=3, marks=2)
        attempt = self.attempt_with(
            exam, {1: "wrong", 2: "wrong", 3: "wrong"}
        )
        self.assertEqual(services.evaluate_and_submit(attempt).score, 0)

    def test_unanswered_questions_without_rows_score_zero(self):
        exam = self.make_exam(questions=3, marks=2)
        attempt = self.attempt_with(exam, {})
        done = services.evaluate_and_submit(attempt)
        self.assertEqual(done.score, 0)
        self.assertEqual(done.percentage, Decimal("0.00"))

    def test_each_question_uses_its_own_marks(self):
        exam = self.make_exam(questions=2, marks=1)
        ExamQuestion.objects.filter(pk=self.eq(exam, 2).pk).update(marks=5)
        attempt = self.attempt_with(exam, {1: "wrong", 2: "right"})
        done = services.evaluate_and_submit(attempt)
        self.assertEqual(done.score, 5)
        self.assertEqual(done.percentage, Decimal("83.33"))

    def test_response_flags_are_stored(self):
        exam = self.make_exam(questions=2)
        attempt = self.attempt_with(exam, {1: "right", 2: "wrong"})
        services.evaluate_and_submit(attempt)
        flags = {
            r.exam_question.order: r.is_correct
            for r in attempt.responses.select_related("exam_question")
        }
        self.assertEqual(flags, {1: True, 2: False})

    def test_percentage_rounding_and_zero_total(self):
        self.assertEqual(
            services.calculate_percentage(1, 3), Decimal("33.33")
        )
        self.assertEqual(
            services.calculate_percentage(2, 3), Decimal("66.67")
        )
        self.assertEqual(services.calculate_percentage(0, 0), Decimal("0.00"))

    def test_pass_mark_is_40_percent(self):
        self.assertTrue(services.is_pass(Decimal("40.00")))
        self.assertFalse(services.is_pass(Decimal("39.99")))

    def test_evaluation_happens_exactly_once(self):
        exam = self.make_exam(questions=2, marks=1)
        attempt = self.attempt_with(exam, {1: "right"})
        first = services.evaluate_and_submit(attempt)
        stamp = first.submitted_at
        # Tamper after submission, then evaluate again.
        Response.objects.filter(attempt=attempt).update(selected_option=None)
        again = services.evaluate_and_submit(attempt)
        self.assertEqual(again.score, 1)
        self.assertEqual(again.submitted_at, stamp)

    def test_late_evaluation_is_stamped_at_deadline(self):
        exam = self.make_exam()
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        late = attempt.deadline + timedelta(minutes=10)
        done = services.evaluate_and_submit(attempt, now=late)
        self.assertEqual(done.submitted_at, attempt.deadline)

    def test_fifty_question_exam_evaluates_within_two_seconds(self):
        exam = self.make_exam(questions=50, marks=1, end_offset=120)
        picks = {n: "right" for n in range(1, 51)}
        attempt = self.attempt_with(exam, picks)
        started = perf_counter()
        done = services.evaluate_and_submit(attempt)
        self.assertLess(perf_counter() - started, 2.0)
        self.assertEqual(done.score, 50)


class SubmitFlowTests(AttemptTestBase):
    def setUp(self):
        self.exam = self.make_exam(questions=5, marks=1)
        self.attempt = Attempt.objects.create(
            student=self.student, exam=self.exam
        )
        self.submit_url = reverse("attempt_submit", args=[self.attempt.id])
        self.result_url = reverse("attempt_result", args=[self.attempt.id])
        self.login()

    def pick(self, order, correct):
        eq = self.eq(self.exam, order)
        Response.objects.update_or_create(
            attempt=self.attempt,
            exam_question=eq,
            defaults={"selected_option": self.option(eq, correct=correct)},
        )

    def test_confirmation_page_shows_unanswered_count(self):
        self.pick(1, True)
        self.pick(2, False)
        resp = self.client.get(self.submit_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "3 unanswered questions")
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.is_submitted)  # GET never submits

    def test_confirmation_page_when_all_answered(self):
        for n in range(1, 6):
            self.pick(n, True)
        resp = self.client.get(self.submit_url)
        self.assertContains(resp, "answered all 5 questions")

    def test_manual_submit_scores_and_opens_result(self):
        for n in (1, 2):
            self.pick(n, True)
        self.pick(3, False)
        resp = self.client.post(self.submit_url)
        self.assertRedirects(resp, self.result_url)
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.is_submitted)
        self.assertEqual(self.attempt.score, 2)
        self.assertEqual(self.attempt.percentage, Decimal("40.00"))

    def test_result_page_shows_score_percentage_and_pass(self):
        for n in (1, 2):
            self.pick(n, True)
        self.client.post(self.submit_url)
        resp = self.client.get(self.result_url)
        self.assertContains(resp, "2 / 5")
        self.assertContains(resp, "40.00%")
        self.assertContains(resp, "Pass")

    def test_result_page_shows_fail_below_pass_mark(self):
        self.pick(1, True)
        self.client.post(self.submit_url)
        resp = self.client.get(self.result_url)
        self.assertContains(resp, "20.00%")
        self.assertContains(resp, "Fail")

    def test_double_submit_does_not_rescore(self):
        self.pick(1, True)
        self.client.post(self.submit_url)
        self.attempt.refresh_from_db()
        stamp, score = self.attempt.submitted_at, self.attempt.score
        resp = self.client.post(self.submit_url)
        self.assertRedirects(resp, self.result_url)
        self.attempt.refresh_from_db()
        self.assertEqual(
            (self.attempt.submitted_at, self.attempt.score), (stamp, score)
        )

    def test_back_or_reload_cannot_reopen_a_submitted_attempt(self):
        self.client.post(self.submit_url)
        page = self.client.get(
            reverse("attempt_page", args=[self.attempt.id])
        )
        self.assertRedirects(page, self.result_url)

    def test_answers_are_locked_after_submission(self):
        self.pick(1, True)
        self.client.post(self.submit_url)
        eq = self.eq(self.exam, 2)
        resp = self.client.post(
            reverse("attempt_answer", args=[self.attempt.id]),
            {"question": eq.id, "option": self.option(eq, True).id},
        )
        self.assertEqual(resp.status_code, 403)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.score, 1)
        self.assertEqual(self.attempt.responses.count(), 1)

    def test_timer_zero_auto_submits_saved_answers(self):
        self.pick(1, True)
        self.pick(2, True)
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=31)
        )
        resp = self.client.post(self.submit_url, follow=True)
        self.assertRedirects(resp, self.result_url)
        self.assertContains(resp, "submitted automatically")
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.score, 2)
        self.assertEqual(self.attempt.submitted_at, self.attempt.deadline)

    def test_answer_after_deadline_is_rejected_and_not_scored(self):
        self.pick(1, True)
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=31)
        )
        eq = self.eq(self.exam, 2)
        resp = self.client.post(
            reverse("attempt_answer", args=[self.attempt.id]),
            {"question": eq.id, "option": self.option(eq, True).id},
        )
        self.assertEqual(resp.status_code, 403)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.score, 1)

    def test_abandoned_attempt_is_scored_when_dashboard_is_opened(self):
        self.pick(1, True)
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=45)
        )
        resp = self.client.get(reverse("student_dashboard"))
        self.assertContains(resp, "Completed")
        self.assertContains(resp, "View result")
        self.attempt.refresh_from_db()
        self.assertTrue(self.attempt.is_submitted)
        self.assertEqual(self.attempt.score, 1)

    def test_abandoned_attempt_cannot_be_restarted(self):
        Attempt.objects.filter(pk=self.attempt.pk).update(
            started_at=timezone.now() - timedelta(minutes=45)
        )
        resp = self.client.post(
            reverse("exam_start", args=[self.exam.id]), follow=True
        )
        self.assertContains(resp, "already attempted")
        self.assertEqual(Attempt.objects.count(), 1)

    def test_no_result_for_unsubmitted_attempt(self):
        resp = self.client.get(self.result_url)
        self.assertRedirects(
            resp, reverse("attempt_page", args=[self.attempt.id])
        )
        resp = self.client.get(self.result_url, follow=True)
        self.assertContains(resp, "not been submitted")

    def test_failed_save_keeps_attempt_open_and_retry_works(self):
        self.pick(1, True)
        with mock.patch.object(
            services, "evaluate_and_submit", side_effect=DatabaseError("boom")
        ), self.assertLogs("attempts.views", level="ERROR"):
            resp = self.client.post(self.submit_url, follow=True)
        self.assertContains(resp, "could not be saved")
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.is_submitted)
        self.assertEqual(self.attempt.score, 0)
        # Retry without the failure
        resp = self.client.post(self.submit_url)
        self.assertRedirects(resp, self.result_url)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.score, 1)

    def test_other_student_cannot_submit_or_view_result(self):
        self.login(self.other)
        self.assertEqual(self.client.get(self.submit_url).status_code, 403)
        self.assertEqual(self.client.post(self.submit_url).status_code, 403)
        self.assertEqual(self.client.get(self.result_url).status_code, 403)
        self.attempt.refresh_from_db()
        self.assertFalse(self.attempt.is_submitted)

    def test_instructor_cannot_submit_or_view_result(self):
        self.login(self.instructor)
        self.assertEqual(self.client.post(self.submit_url).status_code, 403)
        self.assertEqual(self.client.get(self.result_url).status_code, 403)

    def test_anonymous_is_sent_to_login(self):
        self.client.logout()
        for url in (self.submit_url, self.result_url):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse("login"), resp.url)

    def test_put_not_allowed_on_submit(self):
        self.assertEqual(self.client.put(self.submit_url).status_code, 405)

    def test_attempt_page_has_submit_button_and_auto_submit_form(self):
        resp = self.client.get(
            reverse("attempt_page", args=[self.attempt.id])
        )
        self.assertContains(resp, 'id="submit-btn"')
        self.assertContains(resp, 'id="auto-submit-form"')
