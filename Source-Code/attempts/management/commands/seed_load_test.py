"""Create data for the NFR-01 load test (Testing/performance/load_test.py).

    python manage.py seed_load_test --students 10 --questions 50

Creates one instructor, N students (password set) and one published exam
that is open right now, with 4 options per question and exactly one correct.
Safe to run again: it rebuilds the load-test exam and its attempts.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from exams.models import Exam, ExamQuestion, Option, Question

PASSWORD = "LoadTest123!"
EXAM_TITLE = "Load Test Exam"


class Command(BaseCommand):
    help = "Create students and a 50-question open exam for load testing"

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=10)
        parser.add_argument("--questions", type=int, default=50)
        parser.add_argument("--duration", type=int, default=60)

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        students = options["students"]
        n_questions = options["questions"]

        instructor, _ = User.objects.get_or_create(
            email="loadtest.instructor@example.com",
            defaults={"username": "loadtest_instructor", "role": "INSTRUCTOR"},
        )
        instructor.set_password(PASSWORD)
        instructor.save()

        # Rebuild from scratch so repeated runs give comparable numbers.
        Exam.objects.filter(title=EXAM_TITLE).delete()
        Question.objects.filter(
            created_by=instructor,
        ).delete()

        for number in range(1, students + 1):
            student, _ = User.objects.get_or_create(
                email=f"loadtest{number}@example.com",
                defaults={"username": f"loadtest{number}", "role": "STUDENT"},
            )
            student.set_password(PASSWORD)
            student.save()

        now = timezone.now()
        exam = Exam.objects.create(
            title=EXAM_TITLE,
            description="Created by seed_load_test",
            created_by=instructor,
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(hours=4),
            duration_minutes=options["duration"],
            is_published=True,
        )
        for order in range(1, n_questions + 1):
            question = Question.objects.create(
                question_text=f"Load test question {order}?",
                marks=1,
                created_by=instructor,
            )
            Option.objects.bulk_create(
                [
                    Option(
                        question=question,
                        option_text=f"Option {letter}",
                        is_correct=(letter == "A"),
                    )
                    for letter in "ABCD"
                ]
            )
            ExamQuestion.objects.create(
                exam=exam, question=question, order=order, marks=1
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Load test data ready: {students} students "
                f"(loadtestN@example.com / {PASSWORD}), exam id {exam.id} "
                f"with {n_questions} questions."
            )
        )
