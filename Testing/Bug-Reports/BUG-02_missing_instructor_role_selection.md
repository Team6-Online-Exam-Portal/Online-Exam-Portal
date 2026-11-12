# Bug Report: BUG-02 - Registration Form Lacks Role Selection for Instructor

- **Bug ID**: BUG-02
- **Linked Test Case IDs**: UT_02, ST_01
- **Requirement**: FR-1 (User Registration)
- **Severity**: Medium (SRS Section 5.1.3 defines Instructor self-registration as a High priority requirement under FR-1; Deviations.md records no deviation for omitting role selection. Mitigated to Medium as instructors can be provisioned via Django admin or management commands).
- **Responsible App**: accounts

## Description
SRS Section 5.1.3 (FR-1) explicitly requires that the public registration form allows a user to register as either a Student or an Instructor, with `role` being a mandatory selectable field, while preventing Administrator registration. However, `RegistrationForm` has no `role` field, the template renders no role selection control, and `register()` hardcodes `role=User.Role.STUDENT`. As a result, Instructor self-registration is impossible (UT_02 fails), and the role choice options (Student vs Instructor) cannot be selected (ST_01 fails).

## Steps to Reproduce
1. Navigate to `/register/`.
2. Inspect the form controls for a Role selection field (Student vs Instructor).
3. Attempt to submit registration with Instructor details (`Name: Chathurth R`, `Email: chathurth.r@test.com`, `Role: Instructor`).

## Expected vs Actual
- **Expected**: Registration form provides options to select Student or Instructor (excluding Administrator). Selecting Instructor creates an account with `role=INSTRUCTOR` and redirects to `/login/`.
- **Actual**: No role field exists on the form or in `RegistrationForm`. All submitted registrations default to `role=STUDENT`. Instructor self-registration cannot be completed.

## Suspected Location
`Source-Code/accounts/views.py` (lines 18-30 `RegistrationForm` missing role field, line 69 hardcoding `role=User.Role.STUDENT`).
