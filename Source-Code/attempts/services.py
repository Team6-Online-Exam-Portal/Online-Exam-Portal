"""Business logic for exam attempts (FR-5).

Views stay thin; everything that decides "can this student do X now?" lives
here so it can be unit-tested without HTTP.
"""
from django.db.models import Sum
from django.utils import timezone

from exams.models import Exam

from .models import Attempt

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
        if not existing.is_submitted and now < existing.deadline:
            return existing  # reload / returning to a running attempt
        raise StartRefused("You have already attempted this exam.")
    if now < exam.start_time:
        raise StartRefused("This exam has not started yet.")
    if now > exam.end_time:
        raise StartRefused("This exam is closed.")
    if question_count(exam) == 0:
        raise StartRefused("This exam has no questions yet.")
    return None
