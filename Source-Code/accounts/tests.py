
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")

    def test_registration_creates_student(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "student1",
                "email": "student@example.com",
                "password1": "Strong-Password-927!",
                "password2": "Strong-Password-927!",
            },
        )
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(email="student@example.com")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password("Strong-Password-927!"))

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="student@example.com",
            password="Strong-Password-927!",
        )
        response = self.client.post(
            reverse("register"),
            {
                "username": "another",
                "email": "student@example.com",
                "password1": "Strong-Password-927!",
                "password2": "Strong-Password-927!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.filter(email="student@example.com").count(),
            1,
        )

    def test_password_mismatch_is_rejected(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "student2",
                "email": "student2@example.com",
                "password1": "Strong-Password-927!",
                "password2": "Different-Password-927!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(email="student2@example.com").exists()
        )


class AuthenticationTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="Strong-Password-927!",
            role=User.Role.STUDENT,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)


    def test_login_with_email_and_password(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "student@example.com",
                "password": "Strong-Password-927!",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))

        # Verify that the login session was created.
        self.assertIn("_auth_user_id", self.client.session)


    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "student@example.com",
                "password": "wrong-password",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )

    def test_logout(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="Strong-Password-927!",
            role=User.Role.STUDENT,
        )
        self.instructor = User.objects.create_user(
            username="instructor",
            email="instructor@example.com",
            password="Strong-Password-927!",
            role=User.Role.INSTRUCTOR,
        )

    def test_student_can_access_student_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_instructor_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("instructor_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_instructor_can_access_instructor_dashboard(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("instructor_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_instructor_cannot_access_student_dashboard(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_redirects_student_to_student_dashboard(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response,
            reverse("student_dashboard"),
        )

    def test_dashboard_redirects_instructor_to_instructor_dashboard(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response,
            reverse("instructor_dashboard"),
        )
