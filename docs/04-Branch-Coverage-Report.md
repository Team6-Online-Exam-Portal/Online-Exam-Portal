# Branch Coverage Report — Online Exam Portal

## 1. Report information

| Field | Value |
|---|---|
| Project | Online Exam Portal |
| Coverage tool | Coverage.py |
| Coverage type | Branch / decision coverage |
| Test command | `coverage run --branch --source=accounts,exams,attempts,results manage.py test accounts exams attempts results` |
| Result | **88% total coverage with branch measurement enabled** |

## 2. Objective

To measure how thoroughly automated tests exercise conditional decision paths in the selected application packages.

## 3. Recorded results

Coverage.py printed the following TOTAL row:

| Metric | Result |
|---|---:|
| Statements | 1,649 |
| Missed statements | 166 |
| Branch opportunities | 236 |
| Partial branches (`BrPart`) | 24 |
| Total coverage printed by Coverage.py | **88%** |
| Tests discovered | 114 |
| Tests passed | 114 |
| Failures / errors | 0 / 0 |

The **88%** is the exact total shown in the supplied Coverage.py branch-enabled report. It is not a separately calculated branch-only percentage. The report's `Branch` and `BrPart` columns provide the branch measurement details.

## 4. Notable observations

- `accounts/decorators.py`: 100% coverage.
- `attempts/services.py`: 96% coverage, with one partial branch.
- `attempts/views.py`: 95% coverage, with one partial branch.
- `exams/forms.py`: 83% coverage, with 11 partial branches.
- `exams/views.py`: 30% coverage, with one partial branch.
- `results/views.py`: 89% coverage, with two partial branches.
- `attempts/management/commands/seed_load_test.py`: 0% coverage; its command paths were not exercised by this test run.

## 5. Reproduction commands

Run from `Source-Code/` with the project virtual environment activated:

```bash
coverage erase
coverage run --branch --source=accounts,exams,attempts,results manage.py test accounts exams attempts results
coverage report -m
coverage html
```

The HTML report is generated at `htmlcov/index.html`. Run the branch-enabled command before generating the HTML report if you want the HTML output to show branch details.

## 6. Conclusion

**PASS — 88% total coverage in the branch-enabled Coverage.py report.** The run discovered and passed 114 tests. Some conditional paths remain partially covered; the module-level report identifies areas for additional test cases. Retain the terminal output and HTML report as supporting evidence.
