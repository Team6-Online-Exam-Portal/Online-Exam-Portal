from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from accounts import views as account_views


def login_placeholder(request):
    return HttpResponse(
        "Login page will be implemented in FR-2.",
        content_type="text/plain",
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("register/", account_views.register, name="register"),
    path("login/", login_placeholder, name="login"),
]
