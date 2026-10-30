
from django.urls import path
from . import views

urlpatterns = [
    # FR-4: Exam Management and Scheduling
    path("instructor/exams/", views.exam_list, name="exam_list"),
    path(
        "instructor/exams/create/",
        views.exam_create,
        name="exam_create",
    ),
    path(
        "instructor/exams/<int:pk>/edit/",
        views.exam_update,
        name="exam_update",
    ),
    path(
        "instructor/exams/<int:pk>/publish/",
        views.exam_publish,
        name="exam_publish",
    ),
    path(
        "instructor/exams/<int:pk>/delete/",
        views.exam_delete,
        name="exam_delete",
    ),
    path(
        "student/exams/",
        views.student_exam_list,
        name="student_exam_list",
    ),

    # FR-3: MCQ Question Management
    path("questions/", views.question_list, name="question_list"),
    path(
        "questions/create/",
        views.question_create,
        name="question_create",
    ),
    path(
        "questions/<int:pk>/edit/",
        views.question_update,
        name="question_update",
    ),
    path(
        "questions/<int:pk>/delete/",
        views.question_delete,
        name="question_delete",
    ),
]
