
from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Question, Option


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
            raise forms.ValidationError("Question text cannot be empty.")

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
            raise forms.ValidationError("Answer option cannot be empty.")

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

            option_text = form.cleaned_data.get("option_text", "").strip()

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
