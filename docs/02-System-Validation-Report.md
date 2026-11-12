# System Validation Report — Online Exam Portal

## 1. Report information

| Field | Value |
|---|---|
| Project | Online Exam Portal |
| Test level | System / user-interface validation |
| Environment | Local Django development server |
| Base URL | `http://127.0.0.1:8000/` |
| Report status | Partially executed |
| Overall assessment | Core access and dashboard checks observed working; full workflow validation remains |

## 2. Objective

To validate the integrated application from a user's perspective and check that major screens and role-based entry points are accessible.

## 3. Environment and startup checks

The application was run locally using the project's Django virtual environment and development server. The root URL was configured to redirect to the login page.

The following checks were observed during the manual session:

| ID | Validation item | Expected result | Observed result | Status |
|---|---|---|---|---|
| SV-01 | Open application root `/` | Redirect to login page | Root redirect was configured and subsequently used | PASS* |
| SV-02 | Student login | Student can authenticate | Student dashboard displayed | PASS |
| SV-03 | Student dashboard | Dashboard loads for student | Dashboard displayed | PASS |
| SV-04 | Available exams display | Exam list/status is shown | Demo Exam displayed with Closed status | PASS |
| SV-05 | Instructor account setup | Instructor account can be created for local testing | Superuser created and role changed to `INSTRUCTOR` | PASS |
| SV-06 | Instructor login/dashboard | Instructor can access instructor dashboard | User confirmed it works | PASS |

`*` The root redirect was added as a small URL configuration change. Retest it in the final environment and retain a screenshot before treating it as formally evidenced.

## 4. Remaining system validation

The following end-to-end checks were not evidenced as completed in the available test session. Execute them before marking system validation fully complete.

| ID | Scenario | Expected result | Status |
|---|---|---|---|
| SV-07 | Instructor creates a question with options and correct answer | Question is saved and visible to instructor | NOT YET VERIFIED |
| SV-08 | Instructor creates and schedules an exam | Exam details and schedule are saved | NOT YET VERIFIED |
| SV-09 | Instructor associates questions with exam | Selected questions appear in exam | NOT YET VERIFIED |
| SV-10 | Student views an open exam | Open exam is available to eligible student | NOT YET VERIFIED |
| SV-11 | Student starts exam and answers questions | Attempt is created and answers can be saved | NOT YET VERIFIED |
| SV-12 | Student submits exam | Submission is accepted and attempt is finalized | NOT YET VERIFIED |
| SV-13 | Evaluation and result generation | Score and result are calculated and stored | NOT YET VERIFIED |
| SV-14 | Student views result/history | Correct result and history are displayed | NOT YET VERIFIED |
| SV-15 | Instructor views report/question review | Report data is displayed correctly | NOT YET VERIFIED |
| SV-16 | Role-based access restrictions | Students cannot access instructor-only actions | NOT YET VERIFIED |
| SV-17 | Data persistence after server restart | Saved records remain available | NOT YET VERIFIED |

## 5. Conclusion

The recorded manual checks confirm that student authentication/dashboard access and instructor authentication/dashboard access worked in the local environment. The automated test report separately records 114 passing tests.

**System validation is not yet marked fully complete** because the available evidence does not establish that the entire instructor-to-student exam lifecycle and all access-control scenarios were manually executed. Update the remaining rows with actual results and attach screenshots or logs.
