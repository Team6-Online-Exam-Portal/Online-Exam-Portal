
from django import forms
from django.utils import timezone
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Exam, Question, Option


# ==================================================
# FR-4: Exam Management Form
# ==================================================

class ExamForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select at least one question for this exam.",
    )

    class Meta:
        model = Exam
        fields = [
            "title",
            "description",
            "start_time",
            "end_time",
            "duration_minutes",
            "questions",
        ]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "duration_minutes": forms.NumberInput(
                attrs={"min": 1, "max": 180}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user is not None:
            self.fields["questions"].queryset = Question.objects.filter(
                created_by=user
            ).order_by("-created_at")

        if self.instance.pk:
            self.fields["questions"].initial = (
                self.instance.exam_questions.values_list(
                    "question_id", flat=True
                )
            )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if not title:
            raise forms.ValidationError(
                "Exam title cannot be empty."
            )

        return title

    def clean_duration_minutes(self):
        duration = self.cleaned_data["duration_minutes"]

        if not 1 <= duration <= 180:
            raise forms.ValidationError(
                "Duration must be between 1 and 180 minutes."
            )

        return duration

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        duration = cleaned.get("duration_minutes")

        if start and not self.instance.pk and start <= timezone.now():
            self.add_error(
                "start_time",
                "Start time must be in the future.",
            )

        if start and end and end <= start:
            self.add_error(
                "end_time",
                "End time must be after start time.",
            )
        elif start and end and duration:
            window_minutes = (end - start).total_seconds() / 60

            if duration > window_minutes:
                self.add_error(
                    "duration_minutes",
                    "Duration cannot exceed the exam time window.",
                )

        return cleaned


# ==================================================
# FR-3: MCQ Question Management Form
# ==================================================

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text"]
        labels = {
            "question_text": "Question",
        }
        widgets = {
            "question_text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Enter your MCQ question",
                }
            ),
        }

    def clean_question_text(self):
        question_text = self.cleaned_data["question_text"].strip()

        if not question_text:
            raise forms.ValidationError(
                "Question text cannot be empty."
            )

        return question_text


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ["option_text", "is_correct"]
        labels = {
            "option_text": "Answer option",
            "is_correct": "Is this the correct answer?",
        }

    def clean_option_text(self):
        option_text = self.cleaned_data["option_text"].strip()

        if not option_text:
            raise forms.ValidationError(
                "Answer option cannot be empty."
            )

        return option_text


class BaseOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        options = []
        correct_count = 0

        for form in self.forms:
            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE", False):
                continue

            option_text = form.cleaned_data.get(
                "option_text", ""
            ).strip()

            if not option_text:
                raise forms.ValidationError(
                    "All four answer options must be filled in."
                )

            options.append(option_text.casefold())

            if form.cleaned_data.get("is_correct", False):
                correct_count += 1

        if len(options) != 4:
            raise forms.ValidationError(
                "You must provide exactly four answer options."
            )

        if len(set(options)) != 4:
            raise forms.ValidationError(
                "Answer options must not be duplicates."
            )

        if correct_count != 1:
            raise forms.ValidationError(
                "Select exactly one correct answer."
            )


OptionFormSet = inlineformset_factory(
    Question,
    Option,
    form=OptionForm,
    formset=BaseOptionFormSet,
    extra=4,
    min_num=4,
    validate_min=True,
    max_num=4,
    validate_max=True,
    can_delete=False,
)
