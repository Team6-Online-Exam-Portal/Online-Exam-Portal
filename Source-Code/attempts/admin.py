
from django.contrib import admin
from .models import Attempt, Response


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "exam",
        "started_at",
        "submitted_at",
        "percentage",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.submitted_at is not None:
            return (
                "student",
                "exam",
                "started_at",
                "submitted_at",
                "percentage",
            )
        return ()

    def has_change_permission(self, request, obj=None):
        if obj and obj.submitted_at is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.submitted_at is not None:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "attempt",
        "exam_question",
        "selected_option",
        "is_correct",
    )

    def has_change_permission(self, request, obj=None):
        if obj and obj.attempt.submitted_at is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.attempt.submitted_at is not None:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions
