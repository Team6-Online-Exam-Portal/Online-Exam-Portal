from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from exams.models import Question, Option, Exam, ExamQuestion


class Command(BaseCommand):
    help = "Create demo instructor, students, questions, and a published exam"

    def handle(self, *args, **options):
        User = get_user_model()

        instructor, _ = User.objects.get_or_create(
            email="instructor@example.com",
            defaults={
                "username": "instructor",
                "role": "INSTRUCTOR",
            },
        )
        instructor.is_staff = True
        instructor.set_password("DemoPass123!")
        instructor.save()

        for number in range(1, 3):
            User.objects.get_or_create(
                email=f"student{number}@example.com",
                defaults={
                    "username": f"student{number}",
                    "role": "STUDENT",
                },
            )

        for number in range(1, 11):
            question, _ = Question.objects.get_or_create(
                question_text=f"Demo question {number}?",
                defaults={"created_by": instructor},
            )
            Option.objects.get_or_create(
                question=question,
                option_text="Option A",
                defaults={"is_correct": True},
            )
            Option.objects.get_or_create(
                question=question,
                option_text="Option B",
                defaults={"is_correct": False},
            )

        now = timezone.now()

        exam, _ = Exam.objects.get_or_create(
            title="Demo Exam",
            defaults={
                "description": "Demo exam for development",
                "created_by": instructor,
                "is_published": True,
                "duration_minutes": 30,
                "start_time": now,
                "end_time": now + timedelta(minutes=30),
            },
        )

        for number, question in enumerate(
            Question.objects.order_by("id")[:10], start=1
        ):
            ExamQuestion.objects.get_or_create(
                exam=exam,
                question=question,
                defaults={"order": number, "marks": 1},
            )

        self.stdout.write(
            self.style.SUCCESS("Demo data created successfully.")
        )