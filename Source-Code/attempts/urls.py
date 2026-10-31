from django.urls import path

from . import views

urlpatterns = [
    path(
        "exam/<int:exam_id>/instructions/",
        views.exam_instructions,
        name="exam_instructions",
    ),
    path("exam/<int:exam_id>/start/", views.exam_start, name="exam_start"),
    path("attempt/<int:attempt_id>/", views.attempt_page, name="attempt_page"),
    path(
        "attempt/<int:attempt_id>/answer/",
        views.save_answer,
        name="attempt_answer",
    ),
    path(
        "attempt/<int:attempt_id>/submit/",
        views.attempt_submit,
        name="attempt_submit",
    ),
    path(
        "results/<int:attempt_id>/",
        views.attempt_result,
        name="attempt_result",
    ),
]
