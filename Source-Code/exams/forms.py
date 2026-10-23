
from django import forms
from django.utils import timezone

from .models import Exam, Question


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
            raise forms.ValidationError("Exam title cannot be empty.")
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
                "start_time", "Start time must be in the future."
            )

        if start and end and end <= start:
            self.add_error(
                "end_time", "End time must be after start time."
            )
        elif start and end and duration:
            window_minutes = (end - start).total_seconds() / 60
            if duration > window_minutes:
                self.add_error(
                    "duration_minutes",
                    "Duration cannot exceed the exam time window.",
                )

        return cleaned
