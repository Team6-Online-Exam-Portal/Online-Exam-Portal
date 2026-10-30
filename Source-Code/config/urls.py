
from django.contrib import admin
from django.urls import include, path
from accounts import views as account_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Account URLs
    path("register/", account_views.register, name="register"),
    path("login/", account_views.login_view, name="login"),
    path("logout/", account_views.logout_view, name="logout"),

    # Dashboard URLs
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

    # FR-3 and FR-4: Question and Exam Management
    path("", include("exams.urls")),
]
