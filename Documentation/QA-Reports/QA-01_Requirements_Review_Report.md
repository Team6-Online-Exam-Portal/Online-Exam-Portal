# QA-01 — Requirements and Acceptance Criteria Review Report

**Project:** Online Exam Portal  
**Issue:** #18 — QA-01: Review Requirements and Acceptance Criteria  
**Status:** Review findings prepared; team confirmation pending  
**References:** SRS Sections 5 and 6, Appendix C; GitHub requirement issues #1–#11; Test Plan

## 1. Objective

Review all seven functional requirements (FR-1–FR-7) and four non-functional requirements (NFR-1–NFR-4) for clarity, consistency, measurability, and testability. Check alignment between the SRS, GitHub acceptance criteria, and documented test cases.

This is a requirements-documentation review. It does not certify that the application has passed functional, integration, system, performance, or security testing.

## 2. Review Summary

- Requirements in scope: 11 (7 functional, 4 non-functional).
- All 11 have corresponding GitHub issues with acceptance criteria.
- The Test Plan documents 83 test cases, with IDs mapped in the Summary and SRS Appendix C.
- The requirement issues generally agree with the SRS at a high level.
- Several functional requirement issues use broad acceptance criteria and omit measurable constraints already specified in the SRS.
- Findings below are documentation clarification recommendations, not confirmed software defects.

## 3. Requirement-by-Requirement Review

| Requirement | Review finding | Recommendation | Classification |
|---|---|---|---|
| FR-1 — User Registration | GitHub criteria mention required details, validation, and secure storage but do not state exact password and role rules. | Reference the SRS fields, unique-email rule, password minimum of eight characters including a letter and digit, and restriction on public admin registration. | Clarification |
| FR-2 — Login, Logout and RBAC | Criteria cover basic authentication and access restrictions but omit specific session and error behaviors. | Explicitly reference deactivated-account handling, 30-minute idle timeout, generic invalid-login feedback, and forbidden cross-role access. | Clarification |
| FR-3 — MCQ Management | “Multiple answer options” does not express the exact SRS validation rules. | Specify exactly four distinct nonblank options, one correct answer, positive integer marks, ownership, and restrictions on editing questions already used in attempts. | Clarification |
| FR-4 — Exam Scheduling | Criteria do not state detailed time, duration, and question-count constraints. | Reference the 1–180 minute duration, valid future scheduling window, at least one question, draft/published states, and editing restrictions after attempts. | Clarification |
| FR-5 — Exam Attempt | Criteria cover the basic exam flow but omit some attempt and timer restrictions. | Explicitly reference one attempt per student, question navigation, server-enforced time cutoff, and answer changes before submission. | Clarification |
| FR-6 — Submission and Evaluation | Criteria cover scoring and submission but leave several evaluation rules implicit. | Reference unanswered-question confirmation, automatic submission on timeout, prevention of duplicate submission, score calculation once, and full-or-zero marking. | Clarification |
| FR-7 — Results | Criteria cover result display and privacy but omit several detailed result conditions. | Reference score, percentage, 40% pass threshold, post-window question review, and instructor reporting/statistics. | Clarification |
| NFR-1 — Performance | Numeric targets are provided, including page loading, evaluation time, and concurrency. | Retain the thresholds and record the demonstration environment and measurement method when performance tests are executed. | Measurement evidence pending |
| NFR-2 — Data Protection | Criteria cover saved submissions, immutability, deletion restrictions, recovery, and restart persistence. | Define how failed-save retry and persistence checks will be demonstrated during testing. | Test-method clarification |
| NFR-3 — Security | Criteria cover salted password hashing, server-side authorization, CSRF, ORM use, answer protection, and sessions. | Record the planned evidence for code-review checks and runtime authorization tests. | Test-method clarification |
| NFR-4 — Usability and Compatibility | Criteria include Chrome/Firefox, minimum 360px width, three-click exam access, and message consistency. | Specify supported browser versions and representative screen sizes when executing compatibility checks. | Test-method clarification |

## 4. Traceability Review

The updated Test Plan contains 83 uniquely identified test cases. Its Summary sheet lists requirement-level test IDs for FR-1–FR-7 and NFR-1–NFR-4. The SRS Appendix C includes the corresponding requirement-to-test-case mappings.

**Result:** Requirement-level ID traceability is documented for all 11 requirements.

**Limitation:** Presence of an ID mapping does not independently establish that every detailed acceptance criterion is fully covered. Detailed scenario adequacy and execution results should be verified in the relevant testing tasks.

## 5. Findings and Recommendations

**Finding QA-01-F01 — Functional acceptance criteria are sometimes less specific than the SRS.**  
Affected: FR-1–FR-7.  
Recommendation: Expand or cross-reference GitHub acceptance criteria to include the measurable validation rules and edge cases already defined in the SRS.  
Type: Documentation clarification; no confirmed requirement conflict.

**Finding QA-01-F02 — Non-functional test evidence needs to be specified.**  
Affected: NFR-1–NFR-4.  
Recommendation: During subsequent testing, document the environment, test method, actual results, and evidence for performance, reliability, security, and compatibility checks.  
Type: Test-planning clarification.

**Finding QA-01-F03 — Traceability exists, but detailed coverage still needs execution and review.**  
Affected: FR-1–FR-7 and NFR-1–NFR-4.  
Recommendation: Maintain the existing RTM and Test Plan mappings, and record actual outcomes under the relevant testing issues.  
Type: Follow-up verification.

## 6. Conclusion

All 11 requirements have been reviewed against their GitHub acceptance criteria and the documented SRS scope. The current documentation provides a usable basis for testing, with the clarification recommendations listed above.

No confirmed contradiction requiring an immediate change to the SRS has been established in this review. The team should review the recommendations and decide whether GitHub acceptance-criteria wording needs updating.

**QA-01 disposition:** Review findings documented; recommendations awaiting team acknowledgement. Do not treat this report as evidence that the application has passed its tests.

## 7. Follow-Up

- Share the review report with the project manager and development team through a pull request.
- Record any agreed acceptance-criteria corrections in the relevant GitHub issues or project documentation.
- Leave test execution and Pass/Fail results to TEST-02 and the subsequent testing issues.
- Close QA-01 after the report has been reviewed and accepted.
