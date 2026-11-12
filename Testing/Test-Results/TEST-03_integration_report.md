# TEST-03: Integration Test Report - Online Exam Portal

**GitHub Issue**: #14 (TEST-03: Integration Testing)  
**Execution Date**: 2026-11-12  
**Tester Role**: Independent Verification & Testing  
**Source Baseline**: Results recorded in `Testing/Test-Results/TEST-02_execution_report.md`  

---

## 1. Executive Summary

This integration testing report evaluates the interaction and data flow between integrated subsystems of the Online Exam Portal:
- Authentication & User Management (`accounts` app)
- Question Bank & Exam Scheduling (`exams` app)
- Exam Taking, Answer Submission & Autosave (`attempts` app)
- Automated Evaluation, Scoring & Reporting (`results` app)

All 12 Integration Test cases (`IT_01` through `IT_12`) defined in the Test Plan were evaluated against the actual execution results recorded in `TEST-02_execution_report.md`.

- **Total Integration Cases Evaluated**: 12
- **Passed**: 12 (100%)
- **Failed**: 0 (0%)
- **Blocked**: 0 (0%)

The overall test plan baseline recorded in `TEST-02_execution_report.md` stands at 83 total cases: 77 Pass, 6 Fail, 0 Blocked (92.8% pass rate).

While all 12 specific `IT_` test cases passed under their designed test data, system-level acceptance criteria are qualified where underlying component defects impact the integrated user journey (specifically, public instructor registration and custom question marks).

---

## 2. Integration Acceptance Criteria Evaluation

The integration test suite was assessed against the 6 acceptance criteria for Issue #14:

| # | Acceptance Criterion | Test Case IDs | Criterion Status | Evidence & Test Results |
|---|---|---|---|---|
| **1** | **Registration and login work with the user database** | `IT_01`, `IT_02`, `IT_03` *(referenced: `UT_01`, `UT_02`, `UT_07`, `ST_01`)* | **Partially Verified** | • `IT_01` **Pass**: Student registered (`newstudent@test.com`), credentials verified against SQLite database, logged in (302), and session opened Student dashboard (200 OK).<br>• `IT_02` **Pass**: Logout terminated session; subsequent browser back navigation to protected dashboard redirected 302 to `/login/`.<br>• `IT_03` **Pass**: Direct unauthenticated GET to `/student/dashboard/` redirected 302 to `/login/?next=/student/dashboard/`.<br>• **Defect Limitation**: Public registration form only creates Student accounts; Instructor self-registration fails (`UT_02`, `ST_01`, logged in [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md)). Registration also rejects passwords flagged as common (`UT_01`, logged in [BUG-01](../Bug-Reports/BUG-01_common_password_rejection.md)) and permits passwords without digits (`UT_07`, logged in [BUG-03](../Bug-Reports/BUG-03_password_without_digit_accepted.md)). |
| **2** | **Exam creation and MCQ management work together** | `IT_04`, `IT_05`, `IT_06`, `IT_07` *(referenced: `UT_19`, `UT_21`, `UT_25`, `UT_20`, `UT_45`)* | **Partially Verified** | • `IT_04` **Pass**: Editing an existing question updated the question text (`Capital city of France?`) across question bank and related exam models.<br>• `IT_05` **Pass**: Cross-tenant isolation verified; Instructor A attempting to edit Instructor B's question received HTTP 404.<br>• `IT_06` **Pass**: Draft exam containing questions remained hidden from Student dashboard until Instructor published it, immediately becoming visible.<br>• `IT_07` **Pass**: Direct access by Instructor A to Instructor B's exam was denied (HTTP 404).<br>• **Defect Limitation**: `QuestionForm` lacks a `marks` field (`UT_20`, `UT_45`, logged in [BUG-04](../Bug-Reports/BUG-04_question_custom_marks_ignored.md) and [BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md)); questions integrate into exams with default `marks=1` only, ignoring custom mark values submitted via UI. |
| **3** | **Students access scheduled exams and submit answers** | `IT_08`, `IT_09`, `IT_10`, `IT_11` *(referenced: `UT_27`, `UT_28`, `UT_31`, `UT_32`, `ST_08`, `ST_09`, `ST_10`)* | **Verified** | • `IT_08` **Pass**: Instructions page accurately fetched and rendered duration (30 min), question count (3), and total marks (6) from integrated exam and question models.<br>• `IT_09` **Pass**: Dynamic timer calculation verified; attempt deadline correctly capped at earlier of window end and duration.<br>• `IT_10` **Pass**: Automated background finalization and evaluation triggered when expired in-progress attempt was accessed at timer expiration.<br>• `IT_11` **Pass**: Manual submit workflow seamlessly redirected student from confirmation page directly to results page (`/results/<attempt_id>/`) without intermediate navigation. |
| **4** | **Submitted answers are evaluated and results generated correctly** | `IT_10`, `IT_11`, `IT_12` *(referenced: `UT_34`, `UT_35`, `UT_36`, `UT_39`, `ST_11`, `ST_12`)* | **Verified** | • `IT_10` & `IT_11` **Pass**: Auto-submitted and manually submitted attempts evaluated accurately against stored correct options.<br>• `IT_12` **Pass**: Instructor class report (`/instructor/exam/<id>/report/`) aggregated all submitted student attempts, displaying student name, email, score, percentage, and submission timestamps.<br>• Evaluated scores matched expected non-negative scoring logic (`UT_34`), score and percentage were persisted immutably at submission (`UT_35`), and concurrent submissions evaluated independently (`ST_11`). |
| **5** | **Role-based restrictions work across the app** | `IT_02`, `IT_03`, `IT_05`, `IT_07` *(referenced: `ST_02`, `ST_03`, `ST_13`, `ST_14`, `ST_19`)* | **Verified** | • `IT_02` & `IT_03` **Pass**: Unauthenticated and logged-out users are strictly prohibited from viewing student or instructor dashboards.<br>• `IT_05` & `IT_07` **Pass**: Instructors cannot view, edit, or delete questions or exams created by other instructors (multi-tenant isolation enforced via queries returning HTTP 404).<br>• Cross-role checks verified in system tests: Students attempting instructor routes (`ST_02`) and Instructors attempting student routes (`ST_03`) received HTTP 403 Forbidden. Server-side decorators enforce access control independently of UI links (`ST_19`). |
| **6** | **Integration defects are recorded, referencing relevant BUG files** | All IT_ and related UT_/ST_ cases | **Verified** | All discovered defects impacting component boundaries and end-to-end data flows have been logged as formal bug reports with root-cause locations and reproduction steps: [BUG-01](../Bug-Reports/BUG-01_common_password_rejection.md), [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md), [BUG-03](../Bug-Reports/BUG-03_password_without_digit_accepted.md), [BUG-04](../Bug-Reports/BUG-04_question_custom_marks_ignored.md), and [BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md). |

---

## 3. Detailed IT_ Test Case Results

| Test Case ID | Name of Module | Test Step Summary | Expected Result | Actual Observed Result | Status |
|---|---|---|---|---|---|
| **IT_01** | User Registration Module | Register student with valid details, navigate to login, and authenticate | Registration succeeds; login succeeds and opens Student dashboard | Registration succeeded (302), login succeeded (302), and opened Student dashboard (200 OK) | **Pass** |
| **IT_02** | Login & Access Control Module | Log in, navigate to dashboard, log out, and trigger browser Back navigation | Protected page does not load from cache; user redirected to Login | Protected dashboard request after logout redirected 302 to `/login/` | **Pass** |
| **IT_03** | Login & Access Control Module | Directly enter protected dashboard URL in browser without an active session | User is redirected to Login page | Unauthenticated request redirected 302 to `/login/?next=/student/dashboard/` | **Pass** |
| **IT_04** | Exam Management - Questions Module | Open question bank, edit own question text, and save | Question updated; new text reflected in bank and draft exams | Question updated successfully to `Capital city of France?` (302 redirect) | **Pass** |
| **IT_05** | Exam Management - Questions Module | Instructor A attempts to open Instructor B's question via direct URL/ID | Question is not visible or editable; access is denied | Access denied with HTTP 404 | **Pass** |
| **IT_06** | Exam Management - Exams Module | Check Student dashboard for draft exam, publish as Instructor, re-check dashboard | Exam invisible while draft; appears on Student dashboard after publishing | Exam invisible on student exam list before publishing; visible immediately after publishing | **Pass** |
| **IT_07** | Exam Management - Exams Module | Instructor A attempts to open Instructor B's exam via direct URL/ID | Instructor A sees only own exams; direct access to Instructor B's exam is denied | Direct access to Instructor B's exam denied with HTTP 404 | **Pass** |
| **IT_08** | Exam Taking Module | Log in as Student and open instructions page of published exam before starting | Displays duration, question count, and total marks accurately | Instructions page correctly displayed duration (30 min), 3 questions, and 6 total marks | **Pass** |
| **IT_09** | Exam Taking Module | Start exam whose duration exceeds remaining window time; observe countdown end | Timer counts down to window end, not full exam duration | Attempt deadline correctly capped at window end time | **Pass** |
| **IT_10** | Exam Submission & Evaluation Module | Allow countdown timer to expire without manually submitting | Attempt automatically submitted with saved answers; result evaluated | Expired attempt finalized and scored automatically upon access | **Pass** |
| **IT_11** | Exam Submission & Evaluation Module | Click Submit on confirmation page and observe redirection | Result page loads immediately after submission without extra navigation | Submission redirected immediately to `/results/<attempt_id>/` | **Pass** |
| **IT_12** | Results Module | Log in as Instructor and open Class Report for own exam | Report lists each student's name, email, score, percentage, and submission time | Class report lists submitted students, scores, percentages, and timestamps (200 OK) | **Pass** |

---

## 4. Integration Defects & Subsystem Boundary Analysis

1. **Authentication Boundary (`accounts` app)**:
   - **Defect [BUG-02](../Bug-Reports/BUG-02_missing_instructor_role_selection.md)**: Missing role field prevents Instructor onboarding through the public web interface. Instructors must currently be provisioned via backend admin or fixtures.
   - **Defect [BUG-01](../Bug-Reports/BUG-01_common_password_rejection.md)**: Standard common password check conflicts with the test plan credentials (`Pass1234`).
   - **Defect [BUG-03](../Bug-Reports/BUG-03_password_without_digit_accepted.md)**: Incomplete validator pipeline allows passwords without digits (`PasswordOnly`).

2. **Question-Exam Boundary (`exams` app)**:
   - **Defect [BUG-04](../Bug-Reports/BUG-04_question_custom_marks_ignored.md)** & **[BUG-05](../Bug-Reports/BUG-05_question_invalid_marks_not_validated.md)**: `QuestionForm` only exposes `question_text`, ignoring `marks`. While `ExamQuestion` and `Exam.total_marks` correctly sum question marks, all questions created via the UI are locked to the default value of 1 mark.

3. **Taking-Evaluation Boundary (`attempts` to `results` apps)**:
   - The recorded tests passed for answer persistence, deadline enforcement, automatic submission, and result generation, including the tested concurrent-submission scenario.

---

## 5. Conclusion

All 12 recorded integration test cases passed, covering database access, exam scheduling, test-taking, autosave, and grading in the tested scenarios. However, Criteria 1 and 2 are marked **Partially Verified** because the public registration form does not support instructor account creation and question forms do not expose custom mark inputs. No defect fixes or subsequent retests are documented in the source execution results.
