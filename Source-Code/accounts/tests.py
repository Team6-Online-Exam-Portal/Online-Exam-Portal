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
