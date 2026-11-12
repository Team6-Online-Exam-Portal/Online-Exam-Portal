# Unit Test Report — Online Exam Portal

## 1. Report information

| Field | Value |
|---|---|
| Project | Online Exam Portal |
| Test level | Unit / application test suite |
| Framework | Django test framework |
| Execution environment | Local development environment, macOS |
| Report status | Executed |
| Result | **PASS — 114 tests passed, 0 failures, 0 errors** |

## 2. Objective

To verify the correctness of the implemented Django application components and their expected behaviour through automated tests.

## 3. Execution

The following command was executed from `Source-Code/`:

```bash
python manage.py test accounts exams attempts results
```

## 4. Recorded result

The terminal output reported:

```text
Found 114 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...
Ran 114 tests in 6.921s

OK
Destroying test database for alias 'default'...
```

| Metric | Result |
|---|---:|
| Tests discovered | 114 |
| Passed | 114 |
| Failed | 0 |
| Errors | 0 |
| Execution time | 6.921 seconds |
| Django system check | No issues |

## 5. Application areas included

The test command explicitly included the following Django applications:

- `accounts`
- `exams`
- `attempts`
- `results`

The `attempts` application was also run separately and reported 89 tests passing.

## 6. Conclusion

**PASS.** All 114 tests discovered across the four specified applications passed in the recorded execution. This establishes that the automated test suite passed at the time of execution.

This result does not, by itself, prove that every possible user workflow, deployment configuration, or production environment has been validated.

## 7. Evidence to retain

Attach or commit a terminal screenshot/log showing the command and the final `Ran 114 tests ... OK` output. Record the exact commit hash and execution date when this report is finalized.
