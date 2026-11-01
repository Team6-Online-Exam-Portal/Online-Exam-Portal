# NFR-04 Usability and Compatibility: test results

SRS reference: NFR-4 (section 6.4). Issue #11. Test Plan cases UT_40 to UT_43. Branch `feature/NFR-04-usability` (built on `feature/NFR-01-performance`).

| SRS 6.4 requirement | Test Plan | Result | Status |
|---|---|---|---|
| Works in current Chrome and Firefox with no plugins | UT_40 | Chromium 153: 82 of 82 browser checks pass, no JavaScript errors. Firefox 157.0: 82 of 82 browser checks pass, no JavaScript errors. Tested on 01-Nov-2026 by Prakash. | Met |
| Layouts usable from 360 px width upward | UT_41 | Every screen checked at 360, 768 and 1280 px: no sideways scrolling, nothing sticking out, touch targets 44 px or more, typed-text fields 16 px or more | Met |
| A Student can open and start an available exam within 3 clicks of logging in | UT_42 | 2 clicks (Start exam on the dashboard, Start exam on the instructions page) | Met |
| Error and confirmation messages use a consistent style and wording on every screen | UT_43 | One message component for every screen; one wording pattern; same message for wrong password and unknown email | Met |

## How it was checked

1. **Django tests** (`Source-Code/config/test_usability.py`, 24 tests, run with `python manage.py test`): every screen uses the shared layout (viewport tag, one stylesheet, header with user name and Logout, role-based navigation), tables can stack on a phone and every cell is labelled, validation errors sit inside the field they belong to, every input has a label, messages use one component and one wording pattern, the student reaches the attempt page in 2 clicks. FR-6 and FR-7 screens (submit confirmation, result, history, answer review, instructor report) are included.
2. **Real browser check** (`Testing/usability/responsive_check.py`, Playwright): logs in as an instructor and a student, opens every screen at 360, 768 and 1280 px and measures it, then runs the exam flow (timer counts down, answers save, Next/Previous/navigator work, the answer survives a reload), submits, and opens the result, history, review and report. Output: `NFR-04-browser-results.json` and 360 px screenshots in `NFR-04-screenshots/`.

Run (from `Source-Code`):

```
pip install playwright
playwright install chromium firefox
python manage.py migrate
python manage.py seed_load_test --students 2 --questions 5
python manage.py runserver 8000
python ../Testing/usability/responsive_check.py                    # Chrome engine
python ../Testing/usability/responsive_check.py --browser firefox  # Firefox
```

The check exits with code 0 when everything passes. Run it on a freshly seeded database (`seed_load_test` again) each time, because it submits the exam.

## What was built

- One shared layout (`templates/base.html`) and one stylesheet (`templates/partials/styles.html`), mobile first: the base rules are the 360 px layout and wider screens add to it. Plain CSS, no framework, no vendor prefixes.
- Header on every signed-in screen with the user name, role and a Logout button (login and register show the title only); a navigation bar by role (hidden during an exam).
- Tables turn into labelled cards on phones; forms use one field component with the error next to the field (with a warning sign, so it is not shown by colour alone); buttons and links are at least 44 px high; text fields use 16 px so phones do not zoom in.
- Status and result labels (Open, Upcoming, Pass, Fail, Correct, Incorrect) are badges with text, not colour only.
- Messages: one component, `role="status"` for confirmations and `role="alert"` for errors; wording pattern "<Thing> <verb> successfully." for confirmations, full sentences for errors.
- Login shows exactly "Invalid email or password." for a wrong password and for an unknown email.

Deviations 15 to 18 are logged in `Deviations.md`.

## Notes

1. The browser check switches off the browser's own required-field check on the forms it submits empty, so that the server's error messages are what gets tested. Normal users still get the browser's check first.
2. The 16 px rule is checked for fields where text is typed or chosen (text, email, password, number, date, select, textarea). Checkboxes and radio buttons contain no text; their size is covered by the 44 px target rule.
3. "3 clicks" is counted after logging in; the login form already lands on the dashboard.
4. During this work the check script was found to click the header's Logout button instead of the form's own button once the shared header existed. It now clicks the button inside `main`; the Django tests and the 82 browser checks above were run after that fix.

## Firefox check (completed, UT_40)

Firefox 157.0 was installed and tested using Playwright. Ran `python ../Testing/usability/responsive_check.py --browser firefox` from `Source-Code`.

**Result: 82 of 82 browser checks passed.** All screens passed at 360, 768 and 1280 px. Login, registration, student and instructor screens, exam flow, submission, results and navigation passed with no JavaScript errors.

Tested on 01-Nov-2026 by Prakash.

## Known limits

Screen-reader and keyboard-only use were designed for (labels on every input, skip link, visible focus, roles on messages) but not tested with assistive technology.
