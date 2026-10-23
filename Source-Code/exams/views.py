
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from attempts.models import Attempt
from .forms import ExamForm
from .models import Exam, ExamQuestion


def instructor_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.INSTRUCTOR:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


def exam_has_attempts(exam):
    return Attempt.objects.filter(exam=exam).exists()


@instructor_required
def exam_list(request):
    exams = Exam.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    return render(request, "exams/exam_list.html", {"exams": exams})


@instructor_required
def exam_create(request):
    if request.method == "POST":
        form = ExamForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                exam = form.save(commit=False)
                exam.created_by = request.user
                exam.is_published = False
                exam.save()

                for order, question in enumerate(
                    form.cleaned_data["questions"], start=1
                ):
                    ExamQuestion.objects.create(
                        exam=exam,
                        question=question,
                        order=order,
                        marks=1,
                    )

            messages.success(
                request, "Exam saved as a draft successfully."
            )
            return redirect("exam_list")
    else:
        form = ExamForm(user=request.user)

    return render(
        request, "exams/exam_form.html", {"form": form}
    )


@instructor_required
def exam_update(request, pk):
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)

    if exam_has_attempts(exam):
        messages.error(
            request, "An exam with attempts cannot be edited."
        )
        return redirect("exam_list")

    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                form.save()
                exam.exam_questions.all().delete()

                for order, question in enumerate(
                    form.cleaned_data["questions"], start=1
                ):
                    ExamQuestion.objects.create(
                        exam=exam,
                        question=question,
                        order=order,
                        marks=1,
                    )

            messages.success(request, "Exam updated successfully.")
            return redirect("exam_list")
    else:
        form = ExamForm(instance=exam, user=request.user)

    return render(
        request,
        "exams/exam_form.html",
        {"form": form, "exam": exam},
    )


@instructor_required
def exam_publish(request, pk):
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)

    if request.method != "POST":
        return redirect("exam_list")

    if not exam.exam_questions.exists():
        messages.error(request, "Add at least one question before publishing.")
    elif exam.start_time <= timezone.now():
        messages.error(request, "The exam start time must be in the future.")
    elif exam.end_time <= exam.start_time:
        messages.error(request, "The exam end time must follow the start time.")
    else:
        exam.is_published = True
        exam.save(update_fields=["is_published"])
        messages.success(request, "Exam published successfully.")

    return redirect("exam_list")


@instructor_required
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk, created_by=request.user)

    if exam_has_attempts(exam):
        messages.error(
            request, "An exam with attempts cannot be deleted."
        )
        return redirect("exam_list")

    if request.method == "POST":
        exam.delete()
        messages.success(request, "Exam deleted successfully.")
        return redirect("exam_list")

    return render(
        request, "exams/exam_confirm_delete.html", {"exam": exam}
    )


@login_required
def student_exam_list(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied

    now = timezone.now()
    exams = Exam.objects.filter(
        is_published=True,
        start_time__gt=now,
    ).order_by("start_time")

    return render(
        request, "exams/student_exam_list.html", {"exams": exams}
    )
