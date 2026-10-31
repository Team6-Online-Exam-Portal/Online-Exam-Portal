from django.urls import path

from . import views

urlpatterns = [
    path(
        "student/history/",
        views.student_history,
        name="student_history",
    ),
    path(
        "student/attempt/<int:attempt_id>/review/",
        views.question_review,
        name="question_review",
    ),
    path(
        "instructor/exam/<int:exam_id>/report/",
        views.instructor_exam_report,
        name="instructor_exam_report",
    ),
]