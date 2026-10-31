from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Max, Min, Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from accounts.decorators import instructor_required, student_required
from attempts.models import Attempt
from exams.models import Exam

@student_required
def student_history(request):
    attempts = (
        Attempt.objects
        .filter(student=request.user, submitted_at__isnull=False)
        .select_related("exam")
        .order_by("-submitted_at")
    )

    return render(
        request,
        "results/student_history.html",
        {"attempts": attempts},
    )


@student_required
def question_review(request, attempt_id):
    attempt = get_object_or_404(
        Attempt.objects.select_related("exam"),
        pk=attempt_id,
        student=request.user,
    )

    if not attempt.is_submitted:
        raise PermissionDenied

    if timezone.now() < attempt.exam.end_time:
        return render(
            request,
            "results/review_unavailable.html",
            {"exam": attempt.exam},
        )

    responses = (
        attempt.responses
        .select_related(
            "exam_question__question",
            "selected_option",
        )
        .prefetch_related(
            "exam_question__question__options"
        )
        .order_by("exam_question__order")
    )

    review_rows = []

    for response in responses:
        correct_option = response.exam_question.question.options.filter(
            is_correct=True
        ).first()

        review_rows.append({
            "question": response.exam_question.question,
            "selected_option": response.selected_option,
            "correct_option": correct_option,
            "is_correct": response.is_correct,
        })

    return render(
        request,
        "results/question_review.html",
        {
            "attempt": attempt,
            "review_rows": review_rows,
        },
    )
@instructor_required
def instructor_exam_report(request, exam_id):
    exam = get_object_or_404(
        Exam,
        pk=exam_id,
        created_by=request.user,
    )

    attempts = (
        Attempt.objects
        .filter(exam=exam, submitted_at__isnull=False)
        .select_related("student")
        .order_by("-submitted_at")
    )

    statistics = attempts.aggregate(
        total_attempts=Count("id"),
        average_score=Avg("score"),
        highest_score=Max("score"),
        lowest_score=Min("score"),
    )

    return render(
        request,
        "results/instructor_exam_report.html",
        {
            "exam": exam,
            "attempts": attempts,
            "statistics": statistics,
        },
    )