from django.urls import path
from . import views

urlpatterns = [
    path("instructor/exams/", views.exam_list, name="exam_list"),
    path("instructor/exams/create/", views.exam_create, name="exam_create"),
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
    path("student/exams/", views.student_exam_list, name="student_exam_list"),
]