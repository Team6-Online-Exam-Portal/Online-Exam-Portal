import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from accounts.decorators import student_required
from exams.models import Exam, Option

from . import services
from .models import Attempt, Response

logger = logging.getLogger(__name__)


def _own_attempt(request, attempt_id):
    """Fetch an attempt; 403 if it belongs to another student."""
    attempt = get_object_or_404(
        Attempt.objects.select_related("exam"), pk=attempt_id
    )
    if attempt.student_id != request.user.id:
        raise PermissionDenied
    return attempt


@student_required
def exam_instructions(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, is_published=True)
    attempt = Attempt.objects.filter(student=request.user, exam=exam).first()
    if attempt is not None:
        attempt = services.finalize_if_expired(attempt)
    status = services.exam_status(exam, attempt)
    return render(
        request,
        "attempts/instructions.html",
        {
            "exam": exam,
            "status": status,
            "question_count": services.question_count(exam),
            "total_marks": services.total_marks(exam),
            "can_start": status == services.OPEN,
            "resuming": attempt is not None and not attempt.is_submitted,
        },
    )


@student_required
@require_POST
def exam_start(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, is_published=True)
    try:
        attempt = services.check_can_start(exam, request.user)
        if attempt is None:
            with transaction.atomic():
                attempt = Attempt.objects.create(
                    student=request.user, exam=exam
                )
    except services.StartRefused as refusal:
        messages.error(request, str(refusal))
        return redirect("student_dashboard")
    except IntegrityError:
        # Two start clicks raced; the unique constraint kept it to one.
        messages.error(request, "You have already attempted this exam.")
        return redirect("student_dashboard")
    return redirect("attempt_page", attempt_id=attempt.id)


@student_required
@never_cache  # Back button must reload the page, not show a stale form
def attempt_page(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    now = timezone.now()
    if not attempt.is_submitted and now >= attempt.deadline:
        attempt = services.finalize_if_expired(attempt, now)
        messages.warning(
            request, "Time is up. Your exam was submitted automatically."
        )
    if attempt.is_submitted:
        return redirect("attempt_result", attempt_id=attempt.id)

    selected = {
        r.exam_question_id: r.selected_option_id
        for r in attempt.responses.all()
    }
    questions = []
    exam_questions = attempt.exam.exam_questions.select_related(
        "question"
    ).prefetch_related("question__options")
    for number, eq in enumerate(exam_questions, start=1):
        questions.append(
            {
                "id": eq.id,
                "number": number,
                "text": eq.question.question_text,
                "marks": eq.marks,
                "selected": selected.get(eq.id),
                # Only id and text: correct answers never reach the browser.
                "options": [
                    {"id": o.id, "text": o.option_text}
                    for o in sorted(eq.question.options.all(), key=lambda o: o.id)
                ],
            }
        )

    return render(
        request,
        "attempts/attempt.html",
        {
            "attempt": attempt,
            "exam": attempt.exam,
            "questions": questions,
            "remaining_seconds": attempt.seconds_remaining(now),
            "answered_count": sum(1 for q in questions if q["selected"]),
        },
    )


@student_required
@require_POST
def save_answer(request, attempt_id):
    """Save (or clear) one answer as soon as the student selects it."""
    attempt = _own_attempt(request, attempt_id)
    if attempt.is_submitted:
        return JsonResponse({"error": "Attempt already submitted."}, status=403)
    now = timezone.now()
    if now >= attempt.deadline:
        services.finalize_if_expired(attempt, now)
        return JsonResponse({"error": "The deadline has passed."}, status=403)

    try:
        eq_id = int(request.POST.get("question", ""))
    except ValueError:
        return JsonResponse({"error": "Invalid question."}, status=400)
    exam_question = attempt.exam.exam_questions.filter(pk=eq_id).first()
    if exam_question is None:
        return JsonResponse({"error": "Invalid question."}, status=400)

    option = None
    raw_option = request.POST.get("option", "")
    if raw_option != "":
        try:
            option = Option.objects.filter(
                pk=int(raw_option), question_id=exam_question.question_id
            ).first()
        except ValueError:
            option = None
        if option is None:
            return JsonResponse({"error": "Invalid option."}, status=400)

    with transaction.atomic():
        Response.objects.update_or_create(
            attempt=attempt,
            exam_question=exam_question,
            defaults={"selected_option": option},
        )
    answered = attempt.responses.filter(selected_option__isnull=False).count()
    return JsonResponse({"ok": True, "answered": answered})


@student_required
@require_http_methods(["GET", "POST"])
def attempt_submit(request, attempt_id):
    """GET shows the confirmation page; POST submits and evaluates."""
    attempt = _own_attempt(request, attempt_id)
    now = timezone.now()
    timed_out = not attempt.is_submitted and now >= attempt.deadline

    if timed_out:
        # Timer reached zero: submit what was saved, no confirmation needed.
        attempt = services.finalize_if_expired(attempt, now)
        messages.warning(
            request, "Time is up. Your exam was submitted automatically."
        )
    if attempt.is_submitted:
        return redirect("attempt_result", attempt_id=attempt.id)

    if request.method == "GET":
        return render(
            request,
            "attempts/confirm_submit.html",
            {
                "attempt": attempt,
                "exam": attempt.exam,
                "unanswered": services.unanswered_count(attempt),
                "total_questions": services.question_count(attempt.exam),
            },
        )

    try:
        services.evaluate_and_submit(attempt, now)
    except DatabaseError:
        logger.exception("Submission failed for attempt %s", attempt.id)
        messages.error(
            request,
            "Your submission could not be saved. Your attempt is still "
            "open - please try submitting again before time runs out.",
        )
        return redirect("attempt_page", attempt_id=attempt.id)
    messages.success(request, "Your exam has been submitted.")
    return redirect("attempt_result", attempt_id=attempt.id)


@student_required
def attempt_result(request, attempt_id):
    attempt = _own_attempt(request, attempt_id)
    attempt = services.finalize_if_expired(attempt)
    if not attempt.is_submitted:
        messages.error(
            request, "No result yet: this exam has not been submitted."
        )
        return redirect("attempt_page", attempt_id=attempt.id)
    return render(
        request,
        "attempts/result.html",
        {
            "attempt": attempt,
            "exam": attempt.exam,
            "total_marks": services.total_marks(attempt.exam),
            "passed": services.is_pass(attempt.percentage),
            "pass_percentage": services.PASS_PERCENTAGE,
        },
    )
