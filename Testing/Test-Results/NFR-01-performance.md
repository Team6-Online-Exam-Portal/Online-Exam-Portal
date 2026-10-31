# NFR-01 Performance: test results

SRS reference: NFR-1 (section 6.1). Issue #8. Branch `feature/NFR-01-performance`.

| SRS limit | Result | Status |
|---|---|---|
| Normal pages load within 3 seconds | Slowest page 1.06 s (10 students at once) | Met |
| Evaluation + result page within 2 seconds for up to 50 questions | Slowest 0.32 s (10 students submitting 50 questions at once) | Met |
| At least 10 students at the same time | 10 students, 500 answers saved, 0 errors | Met |
| Login with 10 students logging in at the same instant | 3.8 s | Not met on the test machine (see note 2) |

## How it was measured

- Seed: `python manage.py seed_load_test --students 10 --questions 50`
- Server: `python manage.py runserver 8000`
- Load: `python ../Testing/performance/load_test.py --students 10` (all students act at the same instant), and with `--login-stagger 1` (students log in one second apart).
- Every student: login, dashboard, instructions, start, attempt page, save 50 answers, and (when FR-6 is present) submit and open the result page.
- Machine: cloud container with 2 vCPU, Python 3.13, Django 5.2, SQLite, `DEBUG=True`. The load script runs on the same machine and competes for the same CPUs, so these numbers are pessimistic. Re-run on the demonstration machine before the final demo.

## Before and after (10 students, all logging in at the same instant)

| Step | Before avg / max (s) | After avg / max (s) |
|---|---|---|
| Whole run | 30.4 | 9.1 |
| Dashboard | 0.093 / 0.130 | 0.067 / 0.083 |
| Instructions | 0.114 / 0.143 | 0.078 / 0.099 |
| Start exam | 0.291 / 0.417 | 0.538 / 0.622 |
| Attempt page (50 questions) | 0.313 / 0.647 | 0.272 / 0.450 |
| Save one answer (500 saves) | 0.496 / 0.976 | 0.084 / 1.304 |
| Login | 3.952 / 4.006 | 3.287 / 3.323 |

"Start exam" got slower on average because writers now queue for the SQLite write lock instead of racing; it is still far below 3 s. The slowest single answer save (1.3 s) is a write waiting for that lock.

## With logins one second apart (the realistic case)

Measured on the branch after merging `main` (FR-3 to FR-7 all present), 10 students, 50 questions, 500 answers saved.

| Step | avg / max (s) |
|---|---|
| Login | 0.731 / 1.031 |
| Dashboard | 0.081 / 0.100 |
| Instructions | 0.092 / 0.124 |
| Start exam | 0.272 / 0.353 |
| Attempt page (50 questions) | 0.248 / 0.370 |
| Save one answer | 0.107 / 1.913 |
| Submit + result page (evaluation) | 0.187 / 0.307 |

Every SRS limit is met in this run. The slowest single answer save (1.9 s) is one write waiting for the SQLite write lock while the others save; it is well inside the 3 s page limit.

## Same instant (worst case), after merging main

| Step | avg / max (s) |
|---|---|
| Login | 3.706 / 3.772 |
| Dashboard | 0.076 / 0.086 |
| Attempt page | 0.403 / 1.061 |
| Save one answer | 0.096 / 1.530 |
| Submit + result page (evaluation) | 0.219 / 0.317 |

## Query counts (what grows with data)

| Page | Before | After |
|---|---|---|
| Student dashboard | 9 with 1 exam, 39 with 16 exams (2 more per exam) | 7, whatever the number of exams |
| Instructor exam list | 7 with 1 exam, 22 with 16 | constant |
| Instructor question list | 7 with 1 question, 37 with 16 | constant |
| Save one answer | 15 | 10 |
| Student history (FR-7) | 7 with 1 attempt, 22 with 16 | constant |
| Instructor exam report (FR-7) | 9 with 1 attempt, 24 with 16 | constant |
| Answer review (FR-7), 3 vs 50 questions | 12 and 59 | constant |

Guarded by `attempts/test_performance.py` (13 tests): each builds a small and a large data set and requires the same number of queries.

## What changed

1. Dashboard: question count and total marks come from the exam query (annotate) instead of two queries per exam.
2. Instructor exam list: `has_attempts` is computed in the same query (was one query per exam).
3. Question list: options are loaded with `prefetch_related` (was one query per question).
4. Save answer: one UPDATE in the common case instead of `update_or_create`.
5. FR-7 pages (`results/views.py`): the exam history and the instructor report loaded `exam.total_marks` once per row, and the answer review looked up the correct option once per question. They now read prefetched data, so the query count no longer depends on the number of rows. Output is unchanged. (These lines are in the FR-7 author's file; small change, covered by the FR-7 tests and the new query tests.)
6. SQLite: WAL journal, 20 s busy timeout and IMMEDIATE transactions, so concurrent writers wait instead of failing with "database is locked". This needs Django 5.1 or newer, so `requirements.txt` now says `Django>=5.1,<6.0`.

## Notes and limits

1. Evaluation (FR-6) is in `main` and was measured directly on this branch after merging `main`; no temporary merge was needed.
2. Login time is CPU time for password hashing: one check takes about 0.64 s on this machine (Django's PBKDF2, 1,000,000 iterations). With 2 CPUs, 10 checks at the same instant cannot finish in under about 3.2 s. NFR-3 requires Django's default salted hashing, so this was not weakened. Students do not normally log in in the same instant, and with logins one second apart the slowest login is 1.3 s. A faster demonstration machine, or more CPUs, also removes the problem. Decision for the team: keep the default hashing (recommended).
3. SQLite allows one writer at a time. 10 students is fine; this design is not meant for hundreds.
