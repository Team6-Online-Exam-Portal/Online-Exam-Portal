# Code Coverage Report — Online Exam Portal

## 1. Report information

| Field | Value |
|---|---|
| Project | Online Exam Portal |
| Coverage tool | Coverage.py |
| Coverage type | Statement / line coverage |
| Test command | `coverage run --source=accounts,exams,attempts,results manage.py test accounts exams attempts results` |
| Result | **90% total line coverage** |

## 2. Objective

To measure the proportion of executable statements exercised by the automated test suite.

## 3. Recorded results

Coverage.py reported the following totals:

| Metric | Result |
|---|---:|
| Statements | 1,649 |
| Missed statements | 166 |
| Covered statements | 1,483 |
| Total line coverage | **90%** |
| Tests discovered in the run | 114 |
| Test result | 114 passed, 0 failed, 0 errors |

The report includes the selected `accounts`, `exams`, `attempts` and `results` packages, including their measured supporting files such as tests and migrations.

## 4. Notable observations

- `accounts` views: 93% line coverage.
- `attempts` services: 97% line coverage.
- `attempts` views: 95% line coverage.
- `exams` forms: 89% line coverage.
- `exams` views: 37% line coverage.
- `attempts/management/commands/seed_load_test.py`: 0% line coverage because the command was not exercised by this test run.

The low coverage in `exams/views.py` and the unexecuted load-test management command are useful candidates for additional tests. Coverage of an individual module should not be confused with the overall project percentage.

## 5. Reproduction commands

Run from `Source-Code/` with the project virtual environment activated:

```bash
coverage erase
coverage run --source=accounts,exams,attempts,results manage.py test accounts exams attempts results
coverage report -m
coverage html
```

The HTML report is generated at `htmlcov/index.html`.

## 6. Conclusion

**PASS — 90% line coverage**, as reported by Coverage.py for the recorded run. The automated test suite discovered and passed 114 tests. Retain the terminal output and generated HTML report as supporting evidence.
