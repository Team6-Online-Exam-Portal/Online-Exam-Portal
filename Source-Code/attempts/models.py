
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from exams.models import Exam, ExamQuestion, Option


class Attempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_attempts",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam"],
                name="one_attempt_per_student_exam",
            )
        ]

    def __str__(self):
        return f"{self.student.email} - {self.exam.title}"

    @property
    def deadline(self):
        """Earlier of (start + duration) and the end of the exam window."""
        by_duration = self.started_at + timedelta(
            minutes=self.exam.duration_minutes
        )
        return min(by_duration, self.exam.end_time)

    @property
    def is_submitted(self):
        return self.submitted_at is not None

    @property
    def status(self):
        return "SUBMITTED" if self.is_submitted else "IN_PROGRESS"

    def seconds_remaining(self, now=None):
        now = now or timezone.now()
        return max(0, int((self.deadline - now).total_seconds()))


class Response(models.Model):
    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    exam_question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    selected_option = models.ForeignKey(
        Option,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "exam_question"],
                name="unique_response_per_question_attempt",
            )
        ]

    def __str__(self):
        return f"Response {self.pk} - Attempt {self.attempt_id}"
