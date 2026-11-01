"""NFR-4 usability tests (SRS 6.4, Test Plan UT_41, UT_42, UT_43).

These check what can be checked without a browser: every screen uses the
shared layout (header with user name and Logout, viewport tag, one stylesheet),
tables can stack on a phone, errors sit next to their field, confirmation and
error messages look and read the same everywhere, and a student reaches an
exam in 2 clicks. The real 360 px rendering is checked in a browser by
Testing/usability/responsive_check.py.
"""
import re
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from attempts.models import Attempt
from exams.models import Exam, ExamQuestion, Option, Question

User = get_user_model()
PASSWORD = "Passw0rd!x"


def rendered_messages(response, level):
    """Message texts of one level, as the user sees them on the page."""
    html = response.content.decode()
    found = re.findall(
        rf'<div class="message message-{level}"[^>]*>\s*'
        r'<span class="visually-hidden">[^<]*</span>(.*?)\s*</div>',
        html, re.S,
    )
    return [text.strip() for text in found]


def field_blocks(html):
    """Split a page into its .field blocks (label + input + errors)."""
    parts = html.split('<div class="field')[1:]
    return ['<div class="field' + part.split("</form>")[0] for part in parts]


class UsabilityBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instructor = User.objects.create_user(
            username="ins_ui", email="ins_ui@example.com",
            password=PASSWORD, role=User.Role.INSTRUCTOR,
        )
        cls.student = User.objects.create_user(
            username="stu_ui", email="stu_ui@example.com",
            password=PASSWORD, role=User.Role.STUDENT,
        )
        now = timezone.now()
        cls.question = Question.objects.create(
            question_text="What is 2 + 2?", created_by=cls.instructor
        )
        for i, text in enumerate(["4", "3", "5", "6"]):
            Option.objects.create(
                question=cls.question, option_text=text, is_correct=(i == 0)
            )
        cls.exam = Exam.objects.create(
            title="Open exam", created_by=cls.instructor, is_published=True,
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(hours=2), duration_minutes=30,
        )
        ExamQuestion.objects.create(
            exam=cls.exam, question=cls.question, order=1, marks=1
        )
        cls.upcoming = Exam.objects.create(
            title="Upcoming exam", created_by=cls.instructor, is_published=True,
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=2), duration_minutes=30,
        )
        ExamQuestion.objects.create(
            exam=cls.upcoming, question=cls.question, order=1, marks=1
        )
        cls.draft = Exam.objects.create(
            title="Draft exam", created_by=cls.instructor, is_published=False,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2), duration_minutes=30,
        )
        ExamQuestion.objects.create(
            exam=cls.draft, question=cls.question, order=1, marks=1
        )

    def get(self, name, *args, user=None):
        if user:
            self.client.force_login(user)
        response = self.client.get(reverse(name, args=args))
        self.assertEqual(response.status_code, 200, name)
        return response


class SharedLayoutTests(UsabilityBase):
    """Every screen has the same header, viewport tag and stylesheet."""

    def student_pages(self):
        attempt = Attempt.objects.create(student=self.student, exam=self.exam)
        return [
            ("student_dashboard", []),
            ("student_exam_list", []),
            ("exam_instructions", [self.exam.id]),
            ("attempt_page", [attempt.id]),
        ]

    def instructor_pages(self):
        return [
            ("instructor_dashboard", []),
            ("exam_list", []),
            ("exam_create", []),
            ("exam_update", [self.draft.pk]),
            ("exam_delete", [self.draft.pk]),
            ("question_list", []),
            ("question_create", []),
            ("question_update", [self.question.pk]),
            ("question_delete", [self.question.pk]),
        ]

    def assert_layout(self, html, name, username):
        self.assertIn('name="viewport"', html, name)
        self.assertIn('width=device-width', html, name)
        self.assertIn("--tap", html, f"{name}: shared stylesheet missing")
        self.assertEqual(html.count("<main"), 1, f"{name}: nested <main>")
        self.assertIn(f'<span class="user-name">{username}</span>', html, name)
        self.assertRegex(
            html,
            r'(?s)<form method="post" action="/logout/">.*?Logout</button>',
            name,
        )
        self.assertNotIn("<style>", html.split("</head>")[1], name)

    def test_student_screens_show_user_name_and_logout(self):
        self.client.force_login(self.student)
        for name, args in self.student_pages():
            html = self.get(name, *args).content.decode()
            self.assert_layout(html, name, "stu_ui")

    def test_instructor_screens_show_user_name_and_logout(self):
        self.client.force_login(self.instructor)
        for name, args in self.instructor_pages():
            html = self.get(name, *args).content.decode()
            self.assert_layout(html, name, "ins_ui")

    def test_login_and_register_have_viewport_and_styles_but_no_logout(self):
        for name in ("login", "register"):
            html = self.get(name).content.decode()
            self.assertIn('name="viewport"', html)
            self.assertIn("--tap", html)
            self.assertEqual(html.count("<main"), 1)
            self.assertNotIn("Logout", html)

    def test_navigation_matches_role(self):
        self.client.force_login(self.student)
        html = self.get("student_dashboard").content.decode()
        self.assertIn(reverse("student_exam_list"), html)
        self.assertNotIn(reverse("question_list"), html)
        self.client.force_login(self.instructor)
        html = self.get("instructor_dashboard").content.decode()
        self.assertIn(reverse("exam_list"), html)
        self.assertIn(reverse("question_list"), html)

    def test_attempt_page_hides_navigation_but_keeps_logout(self):
        attempt = Attempt.objects.create(student=self.student, exam=self.exam)
        self.client.force_login(self.student)
        html = self.get("attempt_page", attempt.id).content.decode()
        self.assertNotIn('class="main-nav"', html)
        self.assertIn("Logout", html)

    def test_no_legacy_table_attributes_or_inline_page_styles(self):
        templates = list(Path(settings.BASE_DIR).rglob("templates/**/*.html"))
        self.assertGreater(len(templates), 10)
        for path in templates:
            text = path.read_text()
            self.assertNotIn('border="1"', text, path.name)
            self.assertNotIn("cellpadding", text, path.name)
            if path.name != "styles.html":
                self.assertNotIn("<style>", text, path.name)

    def test_every_page_template_uses_the_shared_layout(self):
        for path in Path(settings.BASE_DIR).rglob("templates/**/*.html"):
            if path.parent.name == "partials" or path.name in (
                "base.html", "403.html"
            ):
                continue
            self.assertIn(
                '{% extends "base.html" %}', path.read_text(), path.name
            )


class ResponsiveTableTests(UsabilityBase):
    """UT_41: tables become stacked cards on a phone; each cell is labelled."""

    def assert_stackable(self, html, name):
        self.assertIn('class="responsive"', html, name)
        self.assertIn('class="table-wrap"', html, name)
        body = html.split("<tbody>")[1].split("</tbody>")[0]
        cells = re.findall(r"<td([^>]*)>", body)
        self.assertTrue(cells, name)
        for attrs in cells:
            self.assertIn("data-label=", attrs, f"{name}: unlabelled cell")

    def test_tables_can_stack_on_a_phone(self):
        self.client.force_login(self.student)
        for name in ("student_dashboard", "student_exam_list"):
            self.assert_stackable(self.get(name).content.decode(), name)
        self.client.force_login(self.instructor)
        for name in ("exam_list", "question_list"):
            self.assert_stackable(self.get(name).content.decode(), name)

    def test_stylesheet_has_phone_rules(self):
        html = self.get("login").content.decode()
        self.assertIn("@media (max-width: 40rem)", html)
        self.assertIn("overflow-x: auto", html)
        self.assertIn("--tap: 44px", html)
        self.assertIn("font-size: 1rem", html)  # 16 px: no zoom on focus


class ThreeClickTests(UsabilityBase):
    """UT_42: login -> dashboard -> exam -> start, at most 3 clicks."""

    def test_student_reaches_the_attempt_page_within_3_clicks(self):
        clicks = 0
        # Logging in is not counted: the form already lands on the dashboard.
        response = self.client.post(
            reverse("login"),
            {"username": self.student.email, "password": PASSWORD},
            follow=True,
        )
        self.assertEqual(response.redirect_chain[-1][0],
                         reverse("student_dashboard"))
        html = response.content.decode()

        # Click 1: "Start exam" on the dashboard row of the open exam.
        link = re.search(
            r'<a class="btn" href="(/exam/\d+/instructions/)">Start exam</a>',
            html,
        )
        self.assertIsNotNone(link, "no Start exam link on the dashboard")
        clicks += 1
        html = self.client.get(link.group(1)).content.decode()

        # Click 2: "Start exam" button on the instructions page.
        form = re.search(
            r'<form method="post" action="(/exam/\d+/start/)">', html
        )
        self.assertIsNotNone(form, "no Start exam button on instructions")
        clicks += 1
        response = self.client.post(form.group(1), follow=True)

        self.assertRegex(response.redirect_chain[-1][0], r"^/attempt/\d+/$")
        self.assertContains(response, "Time left")
        self.assertLessEqual(clicks, 3)
        self.assertEqual(clicks, 2)


class FieldErrorPlacementTests(UsabilityBase):
    """UT_43: a validation error appears next to the field it belongs to."""

    def block_for(self, html, input_id):
        for block in field_blocks(html):
            if f'id="{input_id}"' in block:
                return block
        self.fail(f"no field block for {input_id}")

    def test_registration_errors_are_next_to_their_fields(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "not-an-email",
            "password1": "Passw0rd!x", "password2": "different",
        })
        html = response.content.decode()
        self.assertIn("field-error", self.block_for(html, "id_email"))
        self.assertIn("Passwords do not match.",
                      self.block_for(html, "id_password2"))
        self.assertNotIn("field-error", self.block_for(html, "id_username"))
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_question_form_error_is_next_to_the_blank_question_text(self):
        self.client.force_login(self.instructor)
        data = {
            "question_text": "",
            "options-TOTAL_FORMS": "4", "options-INITIAL_FORMS": "0",
            "options-MIN_NUM_FORMS": "4", "options-MAX_NUM_FORMS": "4",
            "options-0-option_text": "a", "options-0-is_correct": "on",
            "options-1-option_text": "b", "options-2-option_text": "c",
            "options-3-option_text": "d",
        }
        html = self.client.post(
            reverse("question_create"), data
        ).content.decode()
        block = self.block_for(html, "id_question_text")
        self.assertIn("field-error", block)
        self.assertIn("This field is required.", block)

    def test_exam_form_errors_are_next_to_the_missing_fields(self):
        self.client.force_login(self.instructor)
        html = self.client.post(
            reverse("exam_create"), {"title": ""}
        ).content.decode()
        self.assertIn("field-error", self.block_for(html, "id_title"))
        self.assertIn("field-error", self.block_for(html, "id_start_time"))
        self.assertIn("field-error", self.block_for(html, "id_duration_minutes"))

    def test_every_input_has_a_label(self):
        self.client.force_login(self.instructor)
        for name, args in (("login", []), ("register", []),
                           ("exam_create", []), ("question_create", [])):
            if name in ("exam_create", "question_create"):
                self.client.force_login(self.instructor)
            else:
                self.client.logout()
            html = self.get(name, *args).content.decode()
            ids = re.findall(
                r'<(?:input|select|textarea)[^>]*\bid="(id_[^"]+)"', html
            )
            self.assertTrue(ids, name)
            for input_id in ids:
                if re.search(rf'<input[^>]*type="hidden"[^>]*id="{input_id}"',
                             html):
                    continue
                self.assertIn(f'for="{input_id}"', html,
                              f"{name}: {input_id} has no label")


class MessageConsistencyTests(UsabilityBase):
    """UT_43: errors and confirmations look and read the same on every screen."""

    def test_invalid_login_message_is_generic_and_identical(self):
        wrong_password = self.client.post(
            reverse("login"),
            {"username": self.student.email, "password": "wrong-password"},
        ).content.decode()
        unknown_email = self.client.post(
            reverse("login"),
            {"username": "nobody@example.com", "password": "wrong-password"},
        ).content.decode()
        for html in (wrong_password, unknown_email):
            self.assertIn("Invalid email or password.", html)
            self.assertIn('class="message message-error"', html)
            self.assertNotIn("Please enter a correct", html)
        pick = lambda h: re.search(
            r'<div class="message message-error".*?</div>', h, re.S
        ).group(0)
        self.assertEqual(pick(wrong_password), pick(unknown_email))

    def test_messages_render_with_one_component_and_level_roles(self):
        html = self.client.post(
            reverse("register"),
            {"username": "fresh_user", "email": "fresh@example.com",
             "password1": PASSWORD, "password2": PASSWORD},
            follow=True,
        ).content.decode()
        self.assertIn('class="message message-success"', html)
        self.assertIn('role="status"', html)
        self.assertIn("Account created successfully. You can now log in.", html)

    def test_confirmations_follow_one_wording_pattern(self):
        self.client.force_login(self.instructor)
        collected = []
        collected += rendered_messages(self.client.post(
            reverse("question_create"),
            {
                "question_text": "New question?",
                "options-TOTAL_FORMS": "4", "options-INITIAL_FORMS": "0",
                "options-MIN_NUM_FORMS": "4", "options-MAX_NUM_FORMS": "4",
                "options-0-option_text": "a", "options-0-is_correct": "on",
                "options-1-option_text": "b", "options-2-option_text": "c",
                "options-3-option_text": "d",
            },
            follow=True,
        ), "success")
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=2)
        collected += rendered_messages(self.client.post(
            reverse("exam_create"),
            {
                "title": "Another exam", "description": "",
                "start_time": start.strftime("%Y-%m-%dT%H:%M"),
                "end_time": end.strftime("%Y-%m-%dT%H:%M"),
                "duration_minutes": 30, "questions": [self.question.pk],
            },
            follow=True,
        ), "success")
        collected += rendered_messages(self.client.post(
            reverse("exam_publish", args=[self.draft.pk]), follow=True
        ), "success")
        collected += rendered_messages(self.client.post(
            reverse("exam_delete", args=[self.draft.pk]), follow=True
        ), "success")
        self.assertEqual(len(collected), 4, collected)
        for text in collected:
            self.assertRegex(text, r"^[A-Z][A-Za-z ]+ successfully\.$", text)
        self.assertIn("Question created successfully.", collected)

    def test_error_messages_are_full_sentences_ending_in_a_period(self):
        self.client.force_login(self.instructor)
        # Edit and delete are refused once an exam has attempts.
        Attempt.objects.create(student=self.student, exam=self.exam)
        errors = []
        for name, pk in (("exam_update", self.exam.pk),
                         ("exam_delete", self.exam.pk),
                         ("question_update", self.question.pk),
                         ("question_delete", self.question.pk)):
            response = self.client.get(reverse(name, args=[pk]), follow=True)
            found = rendered_messages(response, "error")
            self.assertEqual(len(found), 1, (name, found))
            errors += found
        for text in errors:
            self.assertRegex(text, r"^[A-Z].*\.$", text)
            self.assertNotRegex(text, r"!|^Error", text)

    def test_form_level_errors_use_the_same_style_as_messages(self):
        html = self.client.post(
            reverse("login"),
            {"username": self.student.email, "password": "nope"},
        ).content.decode()
        self.assertIn('class="message message-error" role="alert"', html)


class ResultScreenTests(UsabilityBase):
    """FR-6 and FR-7 screens follow the same layout, tables and messages."""

    def setUp(self):
        now = timezone.now()
        self.closed = Exam.objects.create(
            title="Closed exam", created_by=self.instructor,
            is_published=True, duration_minutes=30,
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=1),
        )
        self.closed_eq = ExamQuestion.objects.create(
            exam=self.closed, question=self.question, order=1, marks=1
        )
        self.done_closed = self.submitted(self.closed)
        self.done_open = self.submitted(self.exam)

    def submitted(self, exam):
        from attempts.models import Response
        attempt = Attempt.objects.create(student=self.student, exam=exam)
        Attempt.objects.filter(pk=attempt.pk).update(
            submitted_at=timezone.now(), score=1, percentage="100.00"
        )
        Response.objects.create(
            attempt=attempt,
            exam_question=exam.exam_questions.get(),
            selected_option=self.question.options.get(is_correct=True),
            is_correct=True,
        )
        return attempt

    def test_student_result_screens_use_the_shared_layout(self):
        in_progress = Attempt.objects.create(
            student=self.student, exam=self.upcoming
        )
        self.client.force_login(self.student)
        pages = [
            ("attempt_result", [self.done_closed.id]),
            ("student_history", []),
            ("question_review", [self.done_closed.id]),   # exam closed
            ("question_review", [self.done_open.id]),     # review unavailable
            ("attempt_submit", [in_progress.id]),         # confirmation page
        ]
        for name, args in pages:
            html = self.get(name, *args).content.decode()
            SharedLayoutTests.assert_layout(
                self, html, f"{name}{args}", "stu_ui"
            )
            self.assertIn("<h1", html, name)

    def test_instructor_report_uses_the_shared_layout(self):
        self.client.force_login(self.instructor)
        html = self.get("instructor_exam_report", self.exam.pk).content.decode()
        SharedLayoutTests.assert_layout(self, html, "report", "ins_ui")
        self.assertIn("<h1", html)

    def test_result_tables_can_stack_on_a_phone(self):
        self.client.force_login(self.student)
        html = self.get("student_history").content.decode()
        ResponsiveTableTests.assert_stackable(self, html, "student_history")
        self.client.force_login(self.instructor)
        html = self.get(
            "instructor_exam_report", self.exam.pk
        ).content.decode()
        ResponsiveTableTests.assert_stackable(self, html, "report")

    def test_result_page_shows_pass_as_a_labelled_badge(self):
        self.client.force_login(self.student)
        html = self.get("attempt_result", self.done_closed.id).content.decode()
        self.assertRegex(html, r'<span class="badge badge-pass">Pass</span>')
        self.assertIn("1 / 1", html)

    def test_attempt_screens_use_the_same_message_wording(self):
        """Submit confirmation and refusals read like the other screens."""
        from attempts.models import Attempt as A
        self.client.force_login(self.student)
        fresh = A.objects.create(student=self.student, exam=self.upcoming)
        ok = self.client.post(
            reverse("attempt_submit", args=[fresh.id]), follow=True
        )
        self.assertEqual(
            rendered_messages(ok, "success"), ["Exam submitted successfully."]
        )
        refused = self.client.post(
            reverse("exam_start", args=[self.closed.id]), follow=True
        )
        for text in rendered_messages(refused, "error"):
            self.assertRegex(text, r"^[A-Z].*\.$", text)
        self.assertEqual(len(rendered_messages(refused, "error")), 1)
