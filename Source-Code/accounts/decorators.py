
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(required_role):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.role != required_role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


student_required = role_required("STUDENT")
instructor_required = role_required("INSTRUCTOR")
