# Bug Report: BUG-03 - Password Lacking Digits Is Accepted by Registration

- **Bug ID**: BUG-03
- **Linked Test Case ID**: UT_07
- **Requirement**: FR-1 (User Registration)
- **Severity**: Low
- **Responsible App**: accounts

## Description
SRS Section 5.1.3 (FR-1) states that "The password must have at least 8 characters with at least one letter and one digit." When registering with a password containing only letters (e.g. `PasswordOnly`), the registration is accepted without validation errors, because no digit requirement validator is configured in Django authentication settings.

## Steps to Reproduce
1. Navigate to `/register/`.
2. Fill Name: `No Digit`.
3. Fill Email: `nodigit@test.com`.
4. Fill Password: `PasswordOnly`.
5. Fill Confirm Password: `PasswordOnly`.
6. Submit the registration form.

## Expected vs Actual
- **Expected**: Validation error is shown next to the Password field stating that at least one digit is required; no user account is created.
- **Actual**: Form validation passes with HTTP 302 redirect to `/login/`, and a user account is created with `PasswordOnly`.

## Suspected Location
`Source-Code/config/settings.py` (AUTH_PASSWORD_VALIDATORS lacks a custom or regex validator enforcing digits) / `Source-Code/accounts/views.py` (`clean()` method in `RegistrationForm`).
