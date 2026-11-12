# Bug Report: BUG-01 - Registration Rejects Test Data Password as Too Common

- **Bug ID**: BUG-01
- **Linked Test Case ID**: UT_01
- **Requirement**: FR-1 (User Registration)
- **Severity**: Low
- **Responsible App**: accounts

## Description
Registration fails when using the valid test data password `Pass1234` specified in the Test Plan, because Django's built-in `CommonPasswordValidator` flags it as a commonly used password.

## Steps to Reproduce
1. Navigate to `/register/`.
2. Enter Name: `Arati R`.
3. Enter Email: `arati.r@test.com`.
4. Enter Password: `Pass1234`.
5. Enter Confirm Password: `Pass1234`.
6. Click Register.

## Expected vs Actual
- **Expected**: Account is created successfully; user is redirected to `/login/` with a confirmation message.
- **Actual**: Registration form returns HTTP 200 with validation error `This password is too common.` displayed on the password field; no user account is created.

## Suspected Location
`Source-Code/config/settings.py` (AUTH_PASSWORD_VALIDATORS: CommonPasswordValidator) / `Source-Code/accounts/views.py` (RegistrationForm.clean).
