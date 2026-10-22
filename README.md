# Online Exam Portal

A web-based system where instructors create multiple-choice exams and students take them within a timed window. The system grades attempts automatically and shows results.

Team 6, PES University, RR Campus. Mini-project for Software Engineering.

## Team

| Name | USN | Role |
|---|---|---|
| Chathurth R | PES1UG24CS563 | Project manager, repo owner, accounts app |
| Arati | PES1UG24CS558 | Developer: scaffold, exams and results apps |
| Prakash N Heroor | PES1UG24CS595 | Developer: attempts app |
| Darshana S | PES1UG24CS913 | Testing and documentation |

Contact: <team email here>

## Tech stack

Python 3.11+, Django 5.x, HTML / CSS / JavaScript, SQLite.

## Repository structure

```
Online-Exam-Portal/
├── README.md
├── Deviations.md
├── Documentation/
│   ├── SRS/
│   ├── SAD/
│   └── Test-Plan/
├── Diagrams/
├── Source-Code/          Django project (apps: accounts, exams, attempts, results)
├── Testing/
│   ├── Test-Results/
│   └── Bug-Reports/
├── Demo/                 Sprint demo videos
└── .github/              CI workflow and PR template
```

## Documents

- Software Requirements Specification: `Documentation/SRS/`
- Software Architecture and Design: `Documentation/SAD/`
- Test Plan (78 test cases): `Documentation/Test-Plan/`

## Running the project locally

Available once the scaffold (SETUP-01) is merged.

```
cd Source-Code
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Run the tests with `python manage.py test`.

## How we work

- One branch per issue: `feature/<ISSUE-ID>-short-name`. Never push to `main`.
- Every PR says `Closes #<issue>`, passes CI and is reviewed by the repo owner before merging.
- Deviations from the SRS, SAD or Test Plan are logged in `Deviations.md`.
- Work is tracked on the GitHub Project board across two sprints.
