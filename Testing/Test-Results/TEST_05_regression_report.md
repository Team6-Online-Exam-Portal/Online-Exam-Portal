# TEST-05 Regression Report (Issue #16)

**Execution Date:** 2026-11-12

**Scope:** Re-execution of the 54 eligible UT_/IT_ test cases (FR-1 to FR-7) against an isolated regression database. No source code changes were made; this is a **BASELINE regression run**.

---

## Executive Summary

- **Total cases executed:** 54
- **Pass:** 49
- **Fail:** 5
- **Changed vs. Run 1:** 0
- **Known defects (BUG-01 to BUG-05) remain unchanged** — referenced where relevant.
- **Limitations:**
  - **IT-02** — server correctly invalidates the session and redirects, but browser back-forward cache (bfcache) cannot be verified programmatically.
  - **UT-28** — start-exam flow creates the attempt and delivers the first question and countdown-timer data; the live JavaScript tick-down is not exercised.
  - **UT-31** — navigator elements are present in the DOM, but client-side question navigation relies on JavaScript.
  - **IT-09** — server-side deadline calculations are verified; the UI countdown display is not verified.

---

## Acceptance Criteria

### 1. Registration and login work with the user database

| Acceptance Sub-criterion | Test Case IDs | Run 1 Result | Run 2 Result | Changed? |
|--------------------------|--------------|--------------|--------------|----------|
| Registration form validates and persists user accounts (FR-1) | UT_01, UT_02, UT_03, UT_04, UT_05, UT_06, UT_07, UT_08, UT_44 | Fail, Fail, Pass, Pass, Pass, Pass, Fail, Pass, Pass | Fail, Fail, Pass, Pass, Pass, Pass, Fail, Pass, Pass | No |
| Login authenticates against user database; inactive/unknown accounts rejected (FR-2) | UT_09, UT_10, UT_11, UT_12, UT_13 | Pass, Pass, Pass, Pass, Pass | Pass, Pass, Pass, Pass, Pass | No |
| End-to-end: register then immediately log in (FR-1 + FR-2) | IT_01 | Pass | Pass | No |

> [!NOTE] UT_01 (BUG-01: common password) and UT_02 (BUG-02: no role field) fail in both runs. UT_07 (BUG-03: no digit validator) also fails in both runs. These defects are unresolved.

---

### 2. Exam creation and MCQ management work together

| Acceptance Sub-criterion | Test Case IDs | Run 1 Result | Run 2 Result | Changed? |
|--------------------------|--------------|--------------|--------------|----------|
| MCQ questions can be created, edited, and deleted with correct validation (FR-3) | UT_14, UT_15, UT_16, UT_17, UT_18, UT_19, UT_20, UT_45, IT_04, IT_05 | Pass, Pass, Pass, Pass, Pass, Pass, Fail, Fail, Pass, Pass | Pass, Pass, Pass, Pass, Pass, Pass, Fail, Fail, Pass, Pass | No |
| Exams can be created with scheduling constraints and linked to questions (FR-4) | UT_21, UT_22, UT_23, UT_24, UT_25, UT_26, UT_46, IT_06, IT_07 | Pass, Pass, Pass, Pass, Pass, Pass, Pass, Pass, Pass | Pass, Pass, Pass, Pass, Pass, Pass, Pass, Pass, Pass | No |

> [!NOTE] UT_20 (BUG-04) and UT_45 (BUG-05) fail in both runs: `QuestionForm` omits the `marks` field, so custom and invalid mark values are silently ignored.

---

### 3. Students access scheduled exams and submit answers

| Acceptance Sub-criterion | Test Case IDs | Run 1 Result | Run 2 Result | Changed? |
|--------------------------|--------------|--------------|--------------|----------|
| Student dashboard shows published exams with correct status labels (FR-5) | UT_27 | Pass | Pass | No |
| Instructions page shows duration, question count, and total marks (FR-5) | IT_08 | Pass | Pass | No |
| Student can start an open exam; attempt is created and first question is rendered (FR-5) | UT_28 | Pass | Pass | No |
| Exams outside the open window cannot be started (FR-5) | UT_29, UT_30 | Pass, Pass | Pass, Pass | No |
| Countdown deadline is the earlier of duration or window end (FR-5) | IT_09 | Pass | Pass | No |
| All questions and navigator controls are delivered to the student (FR-5) | UT_31 | Pass | Pass | No |
| Student can change a selected answer before submitting (FR-5) | UT_32 | Pass | Pass | No |

> [!NOTE] UT_28 and UT_31 are subject to documented JS limitations (see Executive Summary).

---

### 4. Submitted answers are evaluated and results generated correctly

| Acceptance Sub-criterion | Test Case IDs | Run 1 Result | Run 2 Result | Changed? |
|--------------------------|--------------|--------------|--------------|----------|
| Manual submission shows unanswered count; triggers evaluation (FR-6) | UT_33, UT_34 | Pass, Pass | Pass, Pass | No |
| Exam window expiry triggers automatic submission (FR-6) | IT_10 | Pass | Pass | No |
| Result page loads immediately after submission (FR-6) | IT_11 | Pass | Pass | No |
| Score and percentage are immutable after the first evaluation (FR-6) | UT_35 | Pass | Pass | No |
| Student result page shows score, total, percentage, and Pass/Fail (FR-7) | UT_36 | Pass | Pass | No |
| Student history lists all past attempts with dates and scores (FR-7) | UT_37 | Pass | Pass | No |
| No result is shown for an unsubmitted attempt (FR-7) | UT_38 | Pass | Pass | No |
| Instructor class report lists per-student scores, percentages, and submission times (FR-7) | IT_12 | Pass | Pass | No |
| Class report shows attempt count, average, highest, and lowest scores (FR-7) | UT_39 | Pass | Pass | No |

---

### 5. Role-based restrictions work across the app

| Acceptance Sub-criterion | Test Case IDs | Run 1 Result | Run 2 Result | Changed? |
|--------------------------|--------------|--------------|--------------|----------|
| Unauthenticated users are redirected to Login for protected URLs (FR-2) | IT_02, IT_03 | Pass, Pass | Pass, Pass | No |
| Logout invalidates the session; protected pages are no longer accessible (FR-2) | UT_13 | Pass | Pass | No |
| Instructor A cannot view or edit Instructor B's questions (FR-3) | IT_05 | Pass | Pass | No |
| Instructor A cannot view or edit Instructor B's exams (FR-4) | IT_07 | Pass | Pass | No |
| Instructor can view class report only for their own exam (FR-7) | IT_12 | Pass | Pass | No |

> [!NOTE] Instructor self-registration (BUG-02) is blocked by the missing role field in the registration form. This is a known, unresolved defect.

---

### 6. Integration defects are recorded, referencing relevant BUG files

| Defect Description | Bug File | Affected Cases | Run 1 | Run 2 |
|--------------------|----------|---------------|-------|-------|
| `Pass1234` rejected by CommonPasswordValidator; student cannot register with that password | BUG-01 | UT_01 | Fail | Fail |
| No role selector on registration form; instructor self-registration is impossible | BUG-02 | UT_02 | Fail | Fail |
| No digit requirement in password validators; `PasswordOnly` accepted | BUG-03 | UT_07 | Fail | Fail |
| `QuestionForm` omits `marks` field; custom mark values are silently ignored | BUG-04 | UT_20 | Fail | Fail |
| `marks` field absent from form; invalid values (0, -2, 1.5) are not rejected | BUG-05 | UT_45 | Fail | Fail |

---

## Detailed Results (All 54 Cases)

| Test ID | Requirement | Run 1 | Run 2 | Changed? |
|---------|-------------|-------|-------|----------|
| UT_01 | Registration — common password | Fail | Fail | No |
| UT_02 | Registration — missing role field | Fail | Fail | No |
| UT_03 | Registration — blank username | Pass | Pass | No |
| UT_04 | Registration — invalid email | Pass | Pass | No |
| UT_05 | Registration — existing email | Pass | Pass | No |
| UT_06 | Registration — short password | Pass | Pass | No |
| UT_07 | Registration — no digit | Fail | Fail | No |
| UT_08 | Registration — password mismatch | Pass | Pass | No |
| UT_44 | Registration — numeric-only password | Pass | Pass | No |
| IT_01 | Register then login (Student) | Pass | Pass | No |
| UT_09 | Login — valid student credentials | Pass | Pass | No |
| UT_10 | Login — wrong password | Pass | Pass | No |
| UT_11 | Login — unknown email | Pass | Pass | No |
| UT_12 | Login — inactive account | Pass | Pass | No |
| UT_13 | Logout clears session | Pass | Pass | No |
| IT_02 | Back-button after logout (session invalidation) | Pass | Pass | No |
| IT_03 | Direct protected URL while unauthenticated | Pass | Pass | No |
| UT_14 | Create MCQ — valid | Pass | Pass | No |
| UT_15 | Create MCQ — empty question text | Pass | Pass | No |
| UT_16 | Create MCQ — blank option | Pass | Pass | No |
| UT_17 | Create MCQ — duplicate option | Pass | Pass | No |
| UT_18 | Create MCQ — no correct option | Pass | Pass | No |
| UT_19 | Delete MCQ with cascade | Pass | Pass | No |
| UT_20 | Create MCQ with custom marks | Fail | Fail | No |
| UT_45 | Create MCQ with invalid marks | Fail | Fail | No |
| IT_04 | Edit own question | Pass | Pass | No |
| IT_05 | Attempt to edit another instructor's question | Pass | Pass | No |
| UT_21 | Create draft exam | Pass | Pass | No |
| UT_22 | Exam end time before start time | Pass | Pass | No |
| UT_23 | Exam start time in the past | Pass | Pass | No |
| UT_24 | Duration exceeds window | Pass | Pass | No |
| UT_25 | Total marks auto-calculated | Pass | Pass | No |
| UT_26 | Duration outside 1-180 min | Pass | Pass | No |
| UT_46 | Exam with no questions | Pass | Pass | No |
| IT_06 | Draft invisible to student; visible after publishing | Pass | Pass | No |
| IT_07 | Instructor cannot edit another instructor's exam | Pass | Pass | No |
| UT_27 | Student dashboard — exam status labels | Pass | Pass | No |
| IT_08 | Instructions page — duration, count, total marks | Pass | Pass | No |
| UT_28 | Start open exam — attempt created, timer and question delivered | Pass | Pass | No |
| UT_29 | Attempt to start exam before window | Pass | Pass | No |
| UT_30 | Attempt to start exam after window | Pass | Pass | No |
| IT_09 | Countdown deadline — earlier of duration or window end | Pass | Pass | No |
| UT_31 | Navigate questions — DOM contains all questions and navigator | Pass | Pass | No |
| UT_32 | Change answer before submitting | Pass | Pass | No |
| UT_33 | Manual submit — unanswered count shown | Pass | Pass | No |
| UT_34 | Scoring — correct/incorrect/unanswered | Pass | Pass | No |
| IT_11 | Result page loads immediately after submission | Pass | Pass | No |
| UT_35 | Score/percentage immutable after reload | Pass | Pass | No |
| IT_10 | Auto-submission on timer expiry | Pass | Pass | No |
| UT_36 | Student views own result | Pass | Pass | No |
| UT_37 | Student history of attempts | Pass | Pass | No |
| UT_38 | No result for unsubmitted attempt | Pass | Pass | No |
| IT_12 | Instructor class report | Pass | Pass | No |
| UT_39 | Class report — count, average, high, low | Pass | Pass | No |

---

## Conclusions

No differences were detected among the 54 executed cases when compared with the Run 1 baseline (TEST-02), subject to the documented limitations (bfcache verification for IT-02; JavaScript-dependent timer and navigation checks for UT-28, UT-31, and IT-09).

The five previously recorded failures — UT_01 (BUG-01), UT_02 (BUG-02), UT_07 (BUG-03), UT_20 (BUG-04), and UT_45 (BUG-05) — persist unchanged. No bug fixes or feature changes were made between runs; this is confirmed as a BASELINE regression run. All remaining 49 cases continue to Pass.

*End of report.*
