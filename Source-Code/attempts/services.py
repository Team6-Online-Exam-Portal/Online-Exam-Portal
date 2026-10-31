"""Business logic for exam attempts (FR-5).

Views stay thin; everything that decides "can this student do X now?" lives
here so it can be unit-tested without HTTP.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from exams.models import Exam

from .models import Attempt, Response

PASS_PERCENTAGE = Decimal("40")

UPCOMING = "Upcoming"
OPEN = "Open"
CLOSED = "Closed"
COMPLETED = "Completed"


def total_marks(exam):
    """Total marks is the sum of the marks of the exam's questions."""
    return exam.exam_questions.aggregate(total=Sum("marks"))["total"] or 0


def question_count(exam):
    return exam.exam_questions.count()


def exam_status(exam, attempt=None, now=None):
    """Return Upcoming, Open, Closed or Completed for one student."""
    now = now or timezone.now()
    if attempt is not None:
        if attempt.is_submitted:
            return COMPLETED
        if now < attempt.deadline:
            return OPEN  # attempt still running: student can resume
        return CLOSED
    if now < exam.start_time:
        return UPCOMING
    if now <= exam.end_time:
        return OPEN
    return CLOSED


def dashboard_rows(student, now=None):
    """Published exams for the student dashboard, soonest first."""
    now = now or timezone.now()
    finalize_expired_attempts(
        Attempt.objects.filter(student=student), now
    )
    exams = list(
        Exam.objects.filter(is_published=True).order_by("start_time", "id")
    )
    attempts = {
        a.exam_id: a
        for a in Attempt.objects.filter(student=student, exam__in=exams)
        .select_related("exam")
    }
    rows = []
    for exam in exams:
        attempt = attempts.get(exam.id)
        status = exam_status(exam, attempt, now)
        rows.append(
            {
                "exam": exam,
                "attempt": attempt,
                "status": status,
                "total_marks": total_marks(exam),
                "question_count": question_count(exam),
                "can_start": status == OPEN,
            }
        )
    return rows


class StartRefused(Exception):
    """Raised with a student-facing message when an exam cannot be started."""


def check_can_start(exam, student, now=None):
    """Return an existing resumable attempt, or None if a new one may start.

    Raises StartRefused if the exam cannot be started.
    """
    now = now or timezone.now()
    existing = Attempt.objects.filter(student=student, exam=exam).first()
    if existing is not None:
        existing = finalize_if_expired(existing, now)
        if not existing.is_submitted:
            return existing  # reload / returning to a running attempt
        raise StartRefused("You have already attempted this exam.")
    if now < exam.start_time:
        raise StartRefused("This exam has not started yet.")
    if now > exam.end_time:
        raise StartRefused("This exam is closed.")
    if question_count(exam) == 0:
        raise StartRefused("This exam has no questions yet.")
    return None


# ---------------------------------------------------------------- FR-6 ----

def calculate_percentage(score, total):
    """Percentage to 2 decimals; 0 when the exam has no marks."""
    if not total:
        return Decimal("0.00")
    return (Decimal(score) * 100 / Decimal(total)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def is_pass(percentage):
    return Decimal(percentage) >= PASS_PERCENTAGE


def unanswered_count(attempt):
    answered = attempt.responses.filter(selected_option__isnull=False).count()
    return max(0, question_count(attempt.exam) - answered)


def evaluate_and_submit(attempt, now=None):
    """Lock, score and store an attempt. Safe to call more than once.

    Everything happens in one transaction: if saving fails nothing is
    written and the attempt stays In Progress, so the student can retry.
    Each correct answer earns the question's full marks; wrong and
    unanswered earn zero. Score and percentage are written exactly once,
    because an already-submitted attempt is returned untouched.
    """
    now = now or timezone.now()
    with transaction.atomic():
        locked = (
            Attempt.objects.select_for_update()
            .select_related("exam")
            .get(pk=attempt.pk)
        )
        if locked.is_submitted:
            return locked

        score = 0
        changed = []
        responses = locked.responses.select_related(
            "selected_option", "exam_question"
        )
        for response in responses:
            option = response.selected_option
            correct = bool(
                option is not None
                and option.is_correct
                and option.question_id == response.exam_question.question_id
            )
            if correct:
                score += response.exam_question.marks
            if response.is_correct != correct:
                response.is_correct = correct
                changed.append(response)
        if changed:
            Response.objects.bulk_update(changed, ["is_correct"])

        locked.score = score
        locked.percentage = calculate_percentage(
            score, total_marks(locked.exam)
        )
        # Never later than the deadline, even if the request arrived late.
        locked.submitted_at = min(now, locked.deadline)
        locked.save(update_fields=["score", "percentage", "submitted_at"])
        return locked


def finalize_if_expired(attempt, now=None):
    """Submit an In Progress attempt whose time is over (deviation 3).

    The browser timer cannot fire when the tab is closed, so the server
    scores such attempts the next time anything touches them.
    """
    now = now or timezone.now()
    if not attempt.is_submitted and now >= attempt.deadline:
        return evaluate_and_submit(attempt, now)
    return attempt


def finalize_expired_attempts(attempts, now=None):
    """Finalize every expired In Progress attempt in a queryset."""
    now = now or timezone.now()
    for attempt in attempts.filter(submitted_at__isnull=True).select_related(
        "exam"
    ):
        finalize_if_expired(attempt, now)
