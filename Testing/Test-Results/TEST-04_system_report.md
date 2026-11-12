# TEST-04: System Test Report - Online Exam Portal

**GitHub Issue**: #15 (TEST-04: System Testing)  
**Execution Date**: 2026-11-12  
**Tester Role**: Independent Verification & Testing  
**Source Baseline**: Results recorded in `Testing/Test-Results/TEST-02_execution_report.md`  

---

## 1. Executive Summary

This system testing report evaluates the complete, end-to-end functionality, security controls, data integrity, and compliance of the Online Exam Portal against the SRS requirements (FR-1 through FR-7 and NFR-1 through NFR-4).

The evaluation is based on all 21 System Test cases (`ST_01` through `ST_21`), supplemented by relevant Unit, Integration, and Performance test cases from the test plan:
- **Total System Test (ST_) Cases**: 21
  - **Passed**: 20 (95.2%)
  - **Failed**: 1 (4.8% — `ST_01`)
  - **Blocked**: 0 (0%)
- **Supplemental Test Cases Referenced**: 62 (`UT_01`–`UT_47`, `IT_01`–`IT_12`, `PT_01`–`PT_03`)
- **Overall Test Plan Baseline**: 83 total cases: 77 Pass, 6 Fail, 0 Blocked (92.8% pass rate), reflecting the completed manual verification of usability cases `UT_40`–`UT_43`.

Two system criteria are classified as **Partially Verified** due to defects in instructor self-registration, password validation, and question mark configuration.

---

## 2. System Acceptance Criteria Evaluation

The system test results were evaluated against the 6 core criteria defined for Issue #15:

| # | Acceptance Criterion | Test Case IDs | Criterion Status | Evidence & Test Results |
|---|---|---|---|---|
| **1** | **Full student flow** (Register, log in, view available exams, take exam under timer, answer questions, submit, and view results) | `IT_01`, `UT_09`, `UT_27`, `UT_28`, `IT_08`, `UT_31`, `UT_32`, `ST_08`, `UT_33`, `IT_11`, `UT_34`, `UT_35`, `UT_36`, `UT_37`, `ST_12` | **Verified** | • **Registration & Login**: Student registered successfully via `/register/` and authenticated via `/login/` (`IT_01`, `UT_09`). *(Note: Password must be sufficiently complex to avoid common password validator, per [BUG-01](../Bug-Reports/BUG-01_common_password_rejection.md)).*<br>• **Discovery & Launch**: Dashboard listed Open, Upcoming, and Closed exams (`UT_27`); instructions page presented duration, question count, and marks (`IT_08`); open exam launched with attempt creation and countdown timer initiation (`UT_28`).<br>• **Taking & Navigation**: Student navigated between questions (`UT_31`), updated previously selected options with real-time saving (`UT_32`), and proceeded to submit with unanswered questions warning (`ST_08`, `UT_33`).<br>• **Submission & Results**: Immediate redirect upon submit to result page (`IT_11`); accurate scoring (2/6, 33.33%, Fail) displayed immediately (`UT_34`, `UT_36`); past attempts listed with timestamps and scores in student history (`UT_37`); detailed question review unlocked after exam window closed (`ST_12`). |
| **2** | **Full instructor flow** (Register, log in, create/manage MCQs, create and publish scheduled exams, monitor class results) | `UT_02`, `ST_01`, `UT_14`, `IT_04`, `UT_19`, `UT_20`, `UT_45`, `UT_21`, `IT_06`, `IT_12`, `UT_39` | **Partially Verified** | • **Registration Failure**: Instructor self-registration fails completely (`UT_02`, `ST_01`, [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md)); registration form lacks a role selector and hardcodes `role=STUDENT`. Instructor accounts must be provisioned out-of-band via admin or database seeding.<br>• **Authenticated Operations (Pass)**: Logged-in instructor successfully created valid MCQs (`UT_14`), edited existing questions (`IT_04`), deleted questions with cascade cleanup (`UT_19`), created draft exams with auto-calculated total marks (`UT_21`), published exams making them visible to students (`IT_06`), and accessed detailed class reports with summary statistics (average, high, low) (`IT_12`, `UT_39`).<br>• **Marks Limitation**: `QuestionForm` omits the `marks` field (`UT_20`, `UT_45`, [BUG-04](../Bug-Reports/BUG-04_question_custom_marks_ignored.md), [BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md)); questions cannot be created with custom marks through the UI and always default to 1. |
| **3** | **Students cannot access instructor-only features** (Strict role isolation between student and instructor portals) | `ST_02`, `ST_03`, `ST_13`, `ST_14`, `ST_19`, `IT_05`, `IT_07` | **Verified** | • **Role Boundary**: Direct URL requests by Students to Instructor endpoints (e.g. `/instructor/exams/create/`, exam lists, class reports) returned HTTP 403 Forbidden (`ST_02`, `ST_19`).<br>• **Reverse Boundary**: Direct requests by Instructors to Student-only endpoints (e.g. `/student/dashboard/`) returned HTTP 403 Forbidden (`ST_03`).<br>• **Peer Privacy**: Direct access by Student A to Student B's attempt result returned HTTP 403 Forbidden (`ST_13`). Direct access by Instructor A to Instructor B's questions, exams, or reports returned HTTP 404 (`IT_05`, `IT_07`, `ST_14`).<br>• **Server-Side Enforcement**: Role decorators enforce checks independently of UI links (`ST_19`). |
| **4** | **Answers evaluated and scores calculated correctly** (Scoring accuracy, deadline enforcement, autosave, and multi-user isolation) | `UT_34`, `UT_35`, `IT_10`, `ST_09`, `ST_10`, `ST_11`, `PT_02` | **Verified** | • **Scoring Engine**: Evaluated score awarded full marks for correct answers and zero for wrong or unanswered questions, with no negative marking (`UT_34`). Score and percentage remained immutable across reloads (`UT_35`).<br>• **Deadline & Autosubmit**: Answers submitted after the deadline were rejected with HTTP 403 Forbidden (`ST_10`); expired in-progress attempts were automatically finalized and evaluated on next access (`IT_10`). Submissions locked against post-submit tampering (`ST_09`).<br>• **Concurrent Evaluation**: Two students submitting simultaneously were graded independently without cross-contamination (`ST_11`). Evaluation for 50 questions completed in 0.436s, well within the 2.0s NFR-1 limit (`PT_02`). |
| **5** | **Invalid inputs and unauthorized actions handled** (Form validation, CSRF, input boundaries, scheduling conflicts, state protection) | `UT_03`–`UT_08`, `UT_44`, `UT_15`–`UT_18`, `UT_20`, `UT_45`, `UT_22`–`UT_24`, `UT_26`, `UT_46`, `UT_29`, `UT_30`, `ST_04`, `ST_05`, `ST_06`, `ST_07`, `ST_16`, `ST_17`, `ST_18`, `ST_20`, `ST_21` | **Partially Verified** | • **Input Validation Passed**: Rejection of blank required fields (`UT_03`), malformed email (`UT_04`), duplicate email (`UT_05`), short password (`UT_06`), mismatched passwords (`UT_08`), all-numeric passwords (`UT_44`), empty question text (`UT_15`), blank options (`UT_16`), duplicate options (`UT_17`), no correct option marked (`UT_18`), end time before start time (`UT_22`), past start time (`UT_23`), duration exceeding window (`UT_24`), duration out of 1–180 min range (`UT_26`), empty question set on exam (`UT_46`).<br>• **State Protection Passed**: Starting upcoming or closed exams blocked (`UT_29`, `UT_30`); second attempt on same exam refused (`ST_07`); editing/deleting questions or exams with existing attempts blocked (`ST_05`, `ST_06`); submitted attempts cannot be edited or deleted (`ST_16`); simulated DB failure kept attempt open for retry (`ST_17`); CSRF enforced (`ST_21`); passwords stored as salted PBKDF2 hashes (`ST_18`); correct answers hidden from in-progress exam source (`ST_20`).<br>• **Evidence Limitations**: `ST_04` idle session timeout was verified via Django settings (`SESSION_COOKIE_AGE=1800`, `SESSION_SAVE_EVERY_REQUEST=True`), not by waiting 31 minutes of real wall-clock idle time. `ST_15` attempt persistence was checked via database row persistence in SQLite `db.sqlite3` only, without an actual server restart.<br>• **Validation Failures**: Password lacking digits (`PasswordOnly`) accepted (`UT_07`, [BUG-03](../Bug-Reports/BUG-03_password_without_digit_accepted.md)); marks validation missing from form (`UT_45`, [BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md)); role choice dropdown absent (`ST_01`, [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md)). |
| **6** | **Results recorded and defects reported** (Test results documentation, defect logging, traceability, and plan reproduction) | All cases; `BUG-01` through `BUG-05` | **Verified** | • All 83 test cases recorded with factual observations and final outcomes (77 Pass, 6 Fail, 0 Blocked; 92.8% pass rate) in `TEST-02_execution_report.md`.<br>• Reproducible spreadsheet copies generated in both Excel (`TEST-02_Test_Plan_results.xlsx`) and CSV (`TEST-02_Test_Plan_results.csv`).<br>• Five formal bug reports filed in `Testing/Bug-Reports/` (`BUG-01` to `BUG-05`) documenting steps to reproduce, expected vs actual behavior, severity, and suspected file locations. No unauthorized fixes or code alterations were attempted. |

---

## 3. Detailed Results of All 21 System Test (ST_) Cases

| Test Case ID | Requirement | Test Case Summary | Observed Behavior | Status |
|---|---|---|---|---|
| **ST_01** | FR-1 | Attempt to create an Administrator account through public registration | Form provides no role dropdown at all; defaults to Student. Administrator is excluded, but Instructor cannot be chosen either | **Fail** |
| **ST_02** | FR-2 | Student attempts to access an Instructor-only page | Direct GET to `/instructor/exams/create/` returned HTTP 403 Forbidden with access-denied page | **Pass** |
| **ST_03** | FR-2 | Instructor attempts to access a Student-only page | Direct GET to `/student/dashboard/` returned HTTP 403 Forbidden with access-denied page | **Pass** |
| **ST_04** | FR-2 | Session expires after 30 minutes of inactivity | `SESSION_COOKIE_AGE=1800` (30 min) and `SESSION_SAVE_EVERY_REQUEST=True` verified in settings *(Note: verified via configuration inspection, not wall-clock 31-minute wait)* | **Pass** |
| **ST_05** | FR-3 | Attempt to edit or delete a question already used in an exam with student attempts | Edit and delete actions blocked; error message displayed and question preserved in database | **Pass** |
| **ST_06** | FR-4 | Attempt to edit or delete an exam that already has student attempts | Edit and delete actions blocked with message: `An exam with attempts cannot be edited/deleted.` | **Pass** |
| **ST_07** | FR-5 | Attempt to start the same exam a second time after already attempting it | Second start refused with message; database unique constraint enforces one attempt per student/exam | **Pass** |
| **ST_08** | FR-5 | Leave some questions unanswered and proceed to submit | Student successfully navigated to submit confirmation page; unanswered questions warning displayed | **Pass** |
| **ST_09** | FR-6 | Back/reload after submission does not allow answer changes | Asynchronous answer POST to submitted attempt rejected with HTTP 403 Forbidden: `Attempt already submitted.` | **Pass** |
| **ST_10** | FR-6 | Server rejects an answer submitted after the deadline | Answer save POST after deadline rejected with HTTP 403 Forbidden: `The deadline has passed.` | **Pass** |
| **ST_11** | FR-6 | Two students submitting the same exam concurrently evaluated independently | Student A (score 2) and Student B (score 5) evaluated simultaneously without cross-contamination | **Pass** |
| **ST_12** | FR-7 | Per-question review is available only after exam window closes | Question review blocked while exam window open; displays question-by-question review once closed | **Pass** |
| **ST_13** | FR-7 | Student cannot access another student's results | Direct GET to another student's result ID returned HTTP 403 Forbidden | **Pass** |
| **ST_14** | FR-7 | Instructor cannot view the report of another instructor's exam | Direct GET to another instructor's exam report returned HTTP 404 Not Found | **Pass** |
| **ST_15** | NFR-2 | Submitted attempt survives a server restart | Attempt record, score, and timestamp verified persistent in SQLite database *(Note: checked database row persistence only, no server restart)* | **Pass** |
| **ST_16** | NFR-2 | Submitted attempts and scores cannot be edited or deleted through application | No application route exists for editing or deleting attempts; ModelAdmin strictly blocks change/delete on submitted rows | **Pass** |
| **ST_17** | NFR-2 | Failed submission keeps attempt open for retry | When DatabaseError was simulated during evaluate_and_submit, attempt remained `is_submitted=False` for retry | **Pass** |
| **ST_18** | NFR-3 | Passwords are stored only as salted hashes | User password hash verified formatted as `pbkdf2_sha256$...`; plaintext passwords never stored | **Pass** |
| **ST_19** | NFR-3 | Role checks are enforced server-side, not only via hidden UI | Student POST to instructor endpoint returned HTTP 403 Forbidden via `@instructor_required` decorator | **Pass** |
| **ST_20** | NFR-3 | Correct answers are never exposed to the browser during an in-progress exam | Page source and JSON context verified: `is_correct` field is omitted from all in-progress exam views | **Pass** |
| **ST_21** | NFR-3 | Forms are protected against CSRF | Form POST submitted without valid CSRF token rejected by Django CSRF middleware with HTTP 403 Forbidden | **Pass** |

---

## 4. Analysis of Discrepancies and Residual Risks

1. **Instructor Self-Registration (`ST_01`, `UT_02`)**:
   - **SRS Requirement**: Section 5.1.3 (FR-1) explicitly states: *"The system shall allow a new user to register as a Student or an Instructor. The form contains full name, email, password, confirm password and role; all fields are mandatory."*
   - **Actual Implementation**: `RegistrationForm` in `accounts/views.py` contains only username, email, and password fields. `register()` hardcodes `role=User.Role.STUDENT`. No deviation is recorded in `Deviations.md`.
   - **Impact**: Instructors cannot self-register; they must be provisioned via Django admin or command-line seeding.

2. **Question Marks Configuration (`UT_20`, `UT_45`)**:
   - **SRS Requirement**: Section 5.2.3 (FR-3) states: *"A question has text, exactly 4 options, exactly 1 correct option, and marks (a positive integer, default 1)."*
   - **Actual Implementation**: `QuestionForm` in `exams/forms.py` exposes only `question_text`. The marks field cannot be populated or validated through the UI, defaulting to 1 for all questions.

3. **Password Validation Strictness (`UT_01`, `UT_07`)**:
   - Standard password validation in `config/settings.py` enforces Django defaults. It blocks common passwords such as `Pass1234` (`UT_01`) but does not enforce a numeric digit requirement (`UT_07`).

---

## 5. Conclusion

The Online Exam Portal successfully satisfies 20 out of 21 System Test cases (95.2%). The recorded tests support the student journey, exam security, server-side role enforcement, autosave, deadline enforcement, and automatic evaluation in the tested scenarios. However, System Acceptance Criteria 2 and 5 are marked **Partially Verified** due to the absence of public Instructor registration (`BUG-02`), question marks configuration (`BUG-04`, `BUG-05`), and password digit validation (`BUG-03`). No defect fixes or subsequent retests are documented in the source execution results.
