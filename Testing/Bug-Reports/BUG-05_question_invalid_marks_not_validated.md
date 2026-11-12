# Bug Report: BUG-05 - Invalid Question Marks Cannot Be Validated Through Question Form

- **Bug ID**: BUG-05
- **Linked Test Case ID**: UT_45
- **Requirement**: FR-3 (MCQ Question Management)
- **Severity**: Low
- **Responsible App**: exams

## Description
Test case UT_45 requires verifying that invalid marks values (0, -2, 1.5) entered into the question creation form are rejected with appropriate validation error messages. Because `QuestionForm` does not expose or include the `marks` field, marks inputs cannot be supplied via the question creation UI, and corresponding form validation errors are not triggered.

## Steps to Reproduce
1. Log in as an Instructor.
2. Navigate to `/questions/create/`.
3. Fill valid question text and 4 distinct options (1 correct).
4. Attempt to enter 0, -2, or 1.5 into the form's marks field and submit.

## Expected vs Actual
- **Expected**: Form displays validation errors rejecting 0, negative, and decimal marks; no invalid question is saved.
- **Actual**: `QuestionForm` does not expose a marks field; marks cannot be entered or validated through the question form.

## Suspected Location
`Source-Code/exams/forms.py` (lines 113-116: `QuestionForm.Meta.fields = ["question_text"]` missing `marks` field and validators).
