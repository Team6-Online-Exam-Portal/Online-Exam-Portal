from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from accounts import views as account_views


urlpatterns = [
    path("admin/", admin.site.urls),

    # Homepage
    path("", lambda request: redirect("login")),

    # Authentication
    path("register/", account_views.register, name="register"),
    path("login/", account_views.login_view, name="login"),
    path("logout/", account_views.logout_view, name="logout"),

    # Dashboards
    path("dashboard/", account_views.dashboard, name="dashboard"),
    path(
        "student/dashboard/",
        account_views.student_dashboard,
        name="student_dashboard",
    ),
    path(
        "instructor/dashboard/",
        account_views.instructor_dashboard,
        name="instructor_dashboard",
    ),

    # Questions and Exam Management
    path("", include("exams.urls")),

    # Exam Attempts
    path("", include("attempts.urls")),
    path("", include("results.urls")),
]