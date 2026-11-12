# Bug Report: BUG-04 - Question Creation Form Does Not Support Custom Marks

- **Bug ID**: BUG-04
- **Linked Test Case ID**: UT_20
- **Requirement**: FR-3 (MCQ Question Management)
- **Severity**: Low
- **Responsible App**: exams

## Description
SRS Section 5.2.3 (FR-3) states that "A question has text, exactly 4 options, exactly 1 correct option, and marks (a positive integer, default 1)." The Question model supports custom marks (`marks = models.PositiveIntegerField(default=1)`), but `QuestionForm` only exposes `question_text` in its `fields` list. Any custom marks value submitted via the question creation UI is ignored, and all created questions default to 1 mark.

## Steps to Reproduce
1. Log in as an Instructor.
2. Navigate to `/questions/create/`.
3. Fill valid question text and 4 answer options (marking 1 correct).
4. Attempt to specify custom marks (e.g. `marks = 5`).
5. Save the question.

## Expected vs Actual
- **Expected**: Question is saved with the specified custom marks value (e.g. 5).
- **Actual**: `QuestionForm` lacks a `marks` input field; submitting custom marks is ignored, and the saved question has default `marks=1`.

## Suspected Location
`Source-Code/exams/forms.py` (lines 113-116: `QuestionForm.Meta.fields = ["question_text"]` excludes `marks`).
