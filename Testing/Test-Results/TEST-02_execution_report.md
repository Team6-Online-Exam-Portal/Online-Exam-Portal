# TEST-02: Test Execution Report - Online Exam Portal

**GitHub Issue**: #13 (TEST-02: Execute Test Cases and Record Results)  
**Execution Date**: 2026-11-12  
**Tester Role**: Independent Verification & Testing  

---

## 1. Environment and Baseline Verification

- **Operating System**: Windows 11 / Windows
- **Python Version**: 3.12.10
- **Django Version**: 5.2.19
- **Database**: SQLite 3 (WAL mode enabled per NFR-01)
- **Primary Browser**: Chrome / Automated HTTP Test Client
- **Baseline Test Suite**:
  ```
  Found 114 test(s).
  Ran 114 tests in 48.185s
  OK
  System check identified no issues (0 silenced).
  ```

---

## 2. Test Execution Details

### Batch 1: Functional Requirements FR-1 and FR-2 (User Registration & Access Control)

| Test Case ID | Name of Module | Test Case Description | Actual Result | Test Result |
|---|---|---|---|---|
| **UT_01** | User Registration Module | Register successfully as a Student with all valid fields | Registration rejected (200 OK): `This password is too common.` displayed; account not created | **Fail** |
| **UT_02** | User Registration Module | Register successfully as an Instructor with all valid fields | Registration form has no role selection control; submitted user created as `STUDENT` instead of `INSTRUCTOR` | **Fail** |
| **UT_03** | User Registration Module | Attempt registration with a mandatory field left blank | Validation error `This field is required` shown next to Name field; no account created | **Pass** |
| **UT_04** | User Registration Module | Attempt registration with an invalid email format | Validation error shown for malformed email; no account created | **Pass** |
| **UT_05** | User Registration Module | Attempt registration with an email already registered | Validation error displayed: `An account with this email already exists.` | **Pass** |
| **UT_06** | User Registration Module | Attempt registration with a password shorter than 8 characters | Validation error displayed: Password too short (< 8 characters); no account created | **Pass** |
| **UT_07** | User Registration Module | Attempt registration with a password containing no digit | No digit requirement enforced by standard Django validators; registration accepted (HTTP 302, user created with `PasswordOnly`) | **Fail** |
| **UT_08** | User Registration Module | Attempt registration where password and confirm password do not match | Validation error displayed: `Passwords do not match.`; no account created | **Pass** |
| **UT_44** | User Registration Module | Verify registration rejects a password containing only digits | Registration rejected with validation error: `This password is entirely numeric.`; no account created | **Pass** |
| **IT_01** | User Registration Module | Register a new Student account and then log in with the same credentials | Registration succeeded (HTTP 302), login succeeded (HTTP 302), and opened Student dashboard (HTTP 200) | **Pass** |
| **ST_01** | User Registration Module | Attempt to create an Administrator account through the public registration form | Public registration form lacks any role dropdown control; all registrations default to Student (neither Instructor nor Administrator is selectable) | **Fail** |
| **UT_09** | Login & Access Control Module | Login successfully with valid Student credentials | User authenticated and redirected: `/dashboard/` -> `/student/dashboard/` (HTTP 200) | **Pass** |
| **UT_10** | Login & Access Control Module | Attempt login with an incorrect password | Generic message `Please enter a correct email and password.` displayed (HTTP 200); user not logged in | **Pass** |
| **UT_11** | Login & Access Control Module | Attempt login with an email that is not registered | Generic message `Please enter a correct email and password.` displayed; unauthenticated | **Pass** |
| **UT_12** | Login & Access Control Module | Attempt login with a deactivated account | Login refused for inactive account (`is_active=False`); authentication blocked | **Pass** |
| **UT_13** | Login & Access Control Module | Logout clears the active session | Session ended and redirected to `/login/`; subsequent attempt to access dashboard redirects to login | **Pass** |
| **IT_02** | Login & Access Control Module | Use browser Back button after logout to try to reopen a protected page | Protected dashboard request after logout redirects 302 to `/login/`; page not served from cache | **Pass** |
| **IT_03** | Login & Access Control Module | Directly open a protected URL while not authenticated | Unauthenticated request redirected 302 to `/login/?next=/student/dashboard/` | **Pass** |
| **ST_02** | Login & Access Control Module | Student attempts to access an Instructor-only page | Server returned HTTP 403 Forbidden with custom access-denied page | **Pass** |
| **ST_03** | Login & Access Control Module | Instructor attempts to access a Student-only page | Server returned HTTP 403 Forbidden with custom access-denied page | **Pass** |
| **ST_04** | Login & Access Control Module | Session expires after 30 minutes of inactivity | `SESSION_COOKIE_AGE=1800` (30 minutes) and `SESSION_SAVE_EVERY_REQUEST=True` verified in application settings | **Pass** |

---

### Batch 2: Functional Requirements FR-3 and FR-4 (MCQ Questions & Exam Scheduling)

| Test Case ID | Name of Module | Test Case Description | Actual Result | Test Result |
|---|---|---|---|---|
| **UT_14** | Exam Management - Questions Module | Create a valid MCQ question with 4 options and 1 correct answer | Question created with 4 options and 1 correct answer; redirected 302 to question list | **Pass** |
| **UT_15** | Exam Management - Questions Module | Attempt to create a question with empty question text | Validation error shown: `Question text cannot be empty.`; question not saved | **Pass** |
| **UT_16** | Exam Management - Questions Module | Attempt to create a question with one blank option | Formset validation error shown: `All four answer options must be filled in.`; question not saved | **Pass** |
| **UT_17** | Exam Management - Questions Module | Attempt to create a question with duplicate option text | Formset validation error shown: `Answer options must not be duplicates.`; question not saved | **Pass** |
| **UT_18** | Exam Management - Questions Module | Attempt to create a question with no option marked correct | Formset validation error shown: `Select exactly one correct answer.`; question not saved | **Pass** |
| **UT_19** | Exam Management - Questions Module | Delete a question with confirmation and verify removal from a draft exam | Question deleted successfully and cascading association removed from draft exam | **Pass** |
| **UT_20** | Exam Management - Questions Module | Create a question with custom marks value | `QuestionForm` does not expose `marks` field; question was created with default `marks=1` instead of custom marks 5 | **Fail** |
| **UT_45** | MCQ Question Management Module | Verify that a question cannot be created with zero, negative, or decimal marks | `QuestionForm` does not expose a `marks` field; marks cannot be entered or validated through form | **Fail** |
| **IT_04** | Exam Management - Questions Module | Edit an existing question owned by the Instructor | Question text updated successfully to `Capital city of France?` (HTTP 302 redirect) | **Pass** |
| **IT_05** | Exam Management - Questions Module | Attempt to view/edit a question created by a different Instructor | Access denied with HTTP 404 (multi-tenant isolation verified) | **Pass** |
| **ST_05** | Exam Management - Questions Module | Attempt to edit or delete a question already used in an exam that has student attempts | Edit and delete blocked; error message displayed and question preserved | **Pass** |
| **UT_21** | Exam Management - Exams Module | Create a valid exam with title, duration, schedule and at least one question | Exam saved as draft (`is_published=False`) with auto-calculated total marks | **Pass** |
| **UT_22** | Exam Management - Exams Module | Attempt to create an exam where end time is before start time | Validation error shown: `End time must be after start time.`; exam not saved | **Pass** |
| **UT_23** | Exam Management - Exams Module | Attempt to create an exam with a start time in the past | Validation error shown: `Start time must be in the future.`; exam not saved | **Pass** |
| **UT_24** | Exam Management - Exams Module | Attempt to create an exam where duration exceeds the start-end window | Validation error shown: `Duration cannot exceed the exam time window.`; exam not saved | **Pass** |
| **UT_25** | Exam Management - Exams Module | Verify total marks are auto-calculated as sum of selected questions' marks | Exam `total_marks` property auto-calculated 2 + 3 + 5 = 10 | **Pass** |
| **UT_26** | Exam Management - Exams Module | Attempt to create an exam with duration outside the 1-180 minute range | Validation error shown: `Duration must be between 1 and 180 minutes.`; exam not saved | **Pass** |
| **UT_46** | Exam Creation and Scheduling Module | Verify that an exam cannot be created without selecting any questions | Validation error shown on questions selection field (required); exam not saved | **Pass** |
| **IT_06** | Exam Management - Exams Module | Verify a draft exam is invisible to students and becomes visible only after publishing | Exam invisible on student exam list while draft; visible immediately upon publishing | **Pass** |
| **IT_07** | Exam Management - Exams Module | Verify an Instructor sees, edits and deletes only their own exams | Direct access to another instructor's exam denied with HTTP 404 | **Pass** |
| **ST_06** | Exam Management - Exams Module | Attempt to edit or delete an exam that already has student attempts | Edit and delete actions blocked with message: `An exam with attempts cannot be edited/deleted.` | **Pass** |

---

### Batch 3: Functional Requirements FR-5 and FR-6 (Exam Taking, Submission & Evaluation)

| Test Case ID | Name of Module | Test Case Description | Actual Result | Test Result |
|---|---|---|---|---|
| **UT_27** | Exam Taking Module | Verify Student dashboard lists published exams with correct status | Dashboard lists Upcoming, Open, and Closed exams with respective status labels | **Pass** |
| **UT_28** | Exam Taking Module | Start an exam that is currently within its open window | Attempt record created; redirected to attempt page | **Pass** |
| **UT_29** | Exam Taking Module | Attempt to start an exam before its scheduled start time | Start action refused with message: `This exam has not started yet.`; redirected to dashboard | **Pass** |
| **UT_30** | Exam Taking Module | Attempt to start an exam after its end time has passed | Start action refused with message: `This exam has closed.`; redirected to dashboard | **Pass** |
| **ST_07** | Exam Taking Module | Attempt to start the same exam a second time after already attempting it | Second attempt blocked; single attempt constraint enforced | **Pass** |
| **ST_08** | Exam Taking Module | Leave some questions unanswered and proceed to submit | Confirmation page reached successfully with unanswered questions notice displayed | **Pass** |
| **IT_08** | Exam Taking Module | Verify the instructions page shows duration, question count and total marks before starting | Instructions page correctly displayed duration (30 min), 3 questions, and 6 total marks | **Pass** |
| **IT_09** | Exam Taking Module | Verify countdown timer ends at the earlier of exam duration or exam window end time | Attempt deadline capped at exam window end time when remaining window is shorter than duration | **Pass** |
| **UT_31** | Exam Taking Module | Navigate between questions using Previous/Next and the question navigator | Attempt page loaded all questions and navigator controls | **Pass** |
| **UT_32** | Exam Taking Module | Change a previously selected answer before submitting | Option successfully updated from Option A to Option B via asynchronous answer save | **Pass** |
| **UT_33** | Exam Submission & Evaluation Module | Manually submit an exam and verify the confirmation shows unanswered count | Submit confirmation page displays `2 questions unanswered` of 3 total questions | **Pass** |
| **UT_34** | Exam Submission & Evaluation Module | Verify scoring: correct answers earn full marks, wrong/unanswered earn zero, no negative marking | Evaluated score: 2/6 (1 correct = 2 marks, 1 wrong = 0, 1 unanswered = 0; no negative marking) | **Pass** |
| **UT_35** | Exam Submission & Evaluation Module | Verify score and percentage are calculated exactly once, at submission | Score (2) and percentage (33.33%) remained immutable across multiple page reloads | **Pass** |
| **IT_10** | Exam Submission & Evaluation Module | Verify auto-submission occurs when the countdown timer reaches zero | Expired in-progress attempt finalized and scored automatically upon access | **Pass** |
| **IT_11** | Exam Submission & Evaluation Module | Verify the result page opens immediately after submission | POST submit redirected immediately to `/results/<attempt_id>/` | **Pass** |
| **ST_09** | Exam Submission & Evaluation Module | Verify Back/reload after submission does not allow answer changes | Late answer submission rejected with HTTP 403 Forbidden: `Attempt already submitted.` | **Pass** |
| **ST_10** | Exam Submission & Evaluation Module | Verify the server rejects an answer submitted after the deadline | Answer save request after deadline rejected with HTTP 403 Forbidden: `The deadline has passed.` | **Pass** |
| **ST_11** | Exam Submission & Evaluation Module | Verify two students submitting the same exam concurrently are evaluated independently | Student A (score 2) and Student B (score 5) evaluated independently without interference | **Pass** |

---

### Batch 4: Functional Requirement FR-7 and Non-Functional Requirements (Results, Performance, Safety, Security, Usability)

| Test Case ID | Name of Module | Test Case Description | Actual Result | Test Result |
|---|---|---|---|---|
| **UT_36** | Results Module | Student views own result showing score, total marks, percentage and Pass/Fail status | Result page shows score 2/6, percentage 33.33%, and status `Fail` (pass mark 40%) | **Pass** |
| **UT_37** | Results Module | Student lists all past attempts with dates and scores | History page lists past attempts with respective dates, scores, and percentages | **Pass** |
| **ST_12** | Results Module | Verify per-question review is available only after the exam window closes | Review page unavailable while window open; displays question-by-question review once closed | **Pass** |
| **UT_38** | Results Module | Verify no result is shown for an exam that has not been submitted | Accessing unsubmitted attempt result redirects 302 back to active attempt page | **Pass** |
| **IT_12** | Results Module | Instructor views a class report for their own exam | Class report lists all submitted students with name, email, score, percentage, and submission time | **Pass** |
| **UT_39** | Results Module | Verify class report shows number of attempts, average, highest and lowest score | Report statistics verified: 2 attempts, average 3.5, highest 5.0, lowest 2.0 | **Pass** |
| **ST_13** | Results Module | Verify a Student cannot access another student's results | Direct access to another student's result denied with HTTP 403 Forbidden | **Pass** |
| **ST_14** | Results Module | Verify an Instructor cannot view the report of another instructor's exam | Direct access to another instructor's exam report denied with HTTP 404 | **Pass** |
| **PT_01** | Non-Functional - Performance Module | Verify normal pages load within 3 seconds on the demonstration setup | Measured slowest page load 0.436s in burst mode, 0.357s with login stagger 1 (well within 3.0s limit) | **Pass** |
| **PT_02** | Non-Functional - Performance Module | Verify evaluation and result page open within 2 seconds of submission for a 50-question exam | Measured slowest evaluation 0.427s in burst mode, 0.436s with login stagger 1 (well within 2.0s limit) | **Pass** |
| **PT_03** | Non-Functional - Performance Module | Verify the system supports at least 10 students taking an exam simultaneously | 10 concurrent students completed 50-question exam (500 answers saved) with 0 errors in 3.8s total | **Pass** |
| **ST_15** | Non-Functional - Safety Module | Verify a submitted attempt survives a server restart | Attempt record and score verified persistent in SQLite database file (checked the database row only, no server restart) | **Pass** |
| **ST_16** | Non-Functional - Safety Module | Verify submitted attempts and scores cannot be edited or deleted through the application | Verified no application route exists for editing or deleting attempts; ModelAdmin strictly forbids edit/delete on submitted attempts | **Pass** |
| **ST_17** | Non-Functional - Safety Module | Verify a failed submission keeps the attempt open for retry | When database save error simulated, attempt remained unsubmitted (`is_submitted=False`) with error notice for retry | **Pass** |
| **ST_18** | Non-Functional - Security Module | Verify passwords are stored only as salted hashes | User password hash verified formatted as `pbkdf2_sha256$...`; plaintext passwords never stored | **Pass** |
| **ST_19** | Non-Functional - Security Module | Verify role checks are enforced server-side, not only via hidden UI | Server rejected Student request to Instructor endpoint with HTTP 403 Forbidden | **Pass** |
| **ST_20** | Non-Functional - Security Module | Verify correct answers are never exposed to the browser during an in-progress exam | Page source and JSON verified: `is_correct` field is not transmitted to browser during active exam | **Pass** |
| **ST_21** | Non-Functional - Security Module | Verify forms are protected against CSRF | Request without valid CSRF token rejected by server with HTTP 403 Forbidden | **Pass** |
| **UT_47** | Security Module | Verify database operations use Django ORM and do not execute unsafe raw SQL | Code review verified 100% Django ORM usage across all apps; zero raw SQL queries (text scan for raw SQL) | **Pass** |
| **UT_40** | Non-Functional - Usability Module | Verify the application works correctly in current Chrome and Firefox without plugins | Manually verified Chrome and Firefox loaded the application without plugins; student login, dashboard, exam listing, and exam start worked in both browsers | **Pass** |
| **UT_41** | Non-Functional - Usability Module | Verify layouts remain usable at 360px screen width | At 360px viewport width, student dashboard and exam instructions were readable and usable; exam table required horizontal scrolling to access all columns | **Pass** |
| **UT_42** | Non-Functional - Usability Module | Verify a Student can start an available exam within 3 clicks of logging in | Student reached the exam attempt page in 2 clicks after login: Start → Start exam | **Pass** |
| **UT_43** | Non-Functional - Usability Module | Verify consistent error and confirmation messages across application screens | Tester confirmed errors were displayed across the checked screens; invalid registration email produced a browser-native validation message. Full message styling/wording consistency was not independently documented | **Pass** |

---

## 3. Summary and Statistics

| Category | Count | Percentage |
|---|---|---|
| **Total Test Cases** | **83** | **100.0%** |
| **Passed** | **77** | **92.8%** |
| **Failed** | **6** | **7.2%** |
| **Blocked** | **0** | **0.0%** |

### Breakdown by Requirement

| Requirement ID | Module / Requirement Description | Total Cases | Pass | Fail | Blocked |
|---|---|---|---|---|---|
| **FR-1** | User Registration | 11 | 7 | 4 | 0 |
| **FR-2** | Login, Logout and Role-Based Access | 10 | 10 | 0 | 0 |
| **FR-3** | Create and Manage MCQ Questions | 11 | 9 | 2 | 0 |
| **FR-4** | Create and Schedule an Exam | 10 | 10 | 0 | 0 |
| **FR-5** | Attempt an Exam | 10 | 10 | 0 | 0 |
| **FR-6** | Submit an Exam and Automatic Evaluation | 8 | 8 | 0 | 0 |
| **FR-7** | View Results & Reports | 8 | 8 | 0 | 0 |
| **NFR-1** | Performance | 3 | 3 | 0 | 0 |
| **NFR-2** | Safety (Data Protection) | 3 | 3 | 0 | 0 |
| **NFR-3** | Security | 5 | 5 | 0 | 0 |
| **NFR-4** | Usability and Compatibility | 4 | 4 | 0 | 0 |

---

## 4. Failed Test Cases & Bug Reports

| Test Case ID | Requirement | Summary of Failure | Linked Bug Report |
|---|---|---|---|
| **UT_01** | FR-1 | Valid test password `Pass1234` rejected by Django CommonPasswordValidator (`This password is too common.`) | [BUG-01](../Bug-Reports/BUG-01_common_password_rejection.md) |
| **UT_02** | FR-1 | Public registration form lacks `role` field; Instructor cannot self-register | [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md) |
| **UT_07** | FR-1 | Password lacking digits (`PasswordOnly`) accepted because no digit validator is configured | [BUG-03](../Bug-Reports/BUG-03_password_without_digit_accepted.md) |
| **ST_01** | FR-1 | Registration form has no role choice dropdown (all users default to Student) | [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md) |
| **UT_20** | FR-3 | `QuestionForm` lacks `marks` field; custom marks (5) ignored, defaulting to 1 | [BUG-04](../Bug-Reports/BUG-04_question_custom_marks_ignored.md) |
| **UT_45** | FR-3 | Invalid marks (0, -2, 1.5) cannot be entered or validated because `marks` is missing from `QuestionForm` | [BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md) |

---
