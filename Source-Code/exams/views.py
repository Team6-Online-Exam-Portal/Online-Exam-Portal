
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import instructor_required
from attempts.models import Attempt
from .forms import QuestionForm, OptionFormSet
from .models import Question


def question_has_attempts(question):
    return Attempt.objects.filter(
        exam__exam_questions__question=question
    ).exists()


@instructor_required
def question_list(request):
    questions = Question.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    return render(
        request,
        "exams/question_list.html",
        {"questions": questions},
    )


@instructor_required
def question_create(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        option_formset = OptionFormSet(request.POST)

        if form.is_valid() and option_formset.is_valid():
            with transaction.atomic():
                question = form.save(commit=False)
                question.created_by = request.user
                question.save()

                option_formset.instance = question
                option_formset.save()

            messages.success(
                request, "MCQ question created successfully."
            )
            return redirect("question_list")
    else:
        form = QuestionForm()
        option_formset = OptionFormSet()

    return render(
        request,
        "exams/question_form.html",
        {"form": form, "option_formset": option_formset},
    )


@instructor_required
def question_update(request, pk):
    question = get_object_or_404(
        Question, pk=pk, created_by=request.user
    )

    if question_has_attempts(question):
        messages.error(
            request,
            "This question cannot be edited because an exam using it has attempts.",
        )
        return redirect("question_list")

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        option_formset = OptionFormSet(
            request.POST, instance=question
        )

        if form.is_valid() and option_formset.is_valid():
            with transaction.atomic():
                form.save()
                option_formset.save()

            messages.success(request, "Question updated successfully.")
            return redirect("question_list")
    else:
        form = QuestionForm(instance=question)
        option_formset = OptionFormSet(instance=question)

    return render(
        request,
        "exams/question_form.html",
        {"form": form, "option_formset": option_formset},
    )


@instructor_required
def question_delete(request, pk):
    question = get_object_or_404(
        Question, pk=pk, created_by=request.user
    )

    if question_has_attempts(question):
        messages.error(
            request,
            "This question cannot be deleted because an exam using it has attempts.",
        )
        return redirect("question_list")

    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect("question_list")

    return render(
        request,
        "exams/question_confirm_delete.html",
        {"question": question},
    )
