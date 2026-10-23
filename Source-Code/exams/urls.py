from django.urls import path
from . import views

urlpatterns = [
    path("questions/", views.question_list, name="question_list"),
    path("questions/create/", views.question_create, name="question_create"),
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