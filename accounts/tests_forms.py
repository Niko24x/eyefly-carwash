from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import (
    LoginForm,
    ProfileEditForm,
    RegisterForm,
    StaffUserCreationForm,
    UserForm,
)
from .models import UserProfile


User = get_user_model()


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )

    def test_valid_credentials(self):
        form = LoginForm(data={'username': 'cliente', 'password': 'password123'})

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_password(self):
        form = LoginForm(data={'username': 'cliente', 'password': 'incorrecta'})

        self.assertFalse(form.is_valid())

    def test_missing_fields(self):
        form = LoginForm(data={'username': '', 'password': ''})

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)


class RegisterFormTests(TestCase):
    def _data(self, **overrides):
        data = {
            'username': 'nuevo',
            'first_name': 'Nuevo',
            'last_name': 'Cliente',
            'email': 'nuevo@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        }
        data.update(overrides)
        return data

    def test_valid_registration_creates_user(self):
        form = RegisterForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'nuevo@example.com')
        self.assertEqual(user.first_name, 'Nuevo')
        self.assertEqual(user.last_name, 'Cliente')
        self.assertTrue(user.check_password('strong-password-123'))

    def test_password_mismatch(self):
        form = RegisterForm(data=self._data(password2='otra-password'))

        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_username(self):
        User.objects.create_user(username='nuevo', password='password123')
        form = RegisterForm(data=self._data())

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_email_required(self):
        form = RegisterForm(data=self._data(email=''))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProfileEditFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def _data(self, **overrides):
        data = {
            'first_name': 'Cliente',
            'last_name': 'Actualizado',
            'email': 'nuevo@example.com',
            'phone_country_code': '502',
            'phone_local_number': '55512345',
        }
        data.update(overrides)
        return data

    def test_valid_updates_user_and_profile(self):
        form = ProfileEditForm(data=self._data(), user=self.user, profile=self.profile)

        self.assertTrue(form.is_valid(), form.errors)
        form.save(self.user, self.profile)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.last_name, 'Actualizado')
        self.assertEqual(self.user.email, 'nuevo@example.com')
        self.assertEqual(self.profile.phone_country_code, '502')
        self.assertEqual(self.profile.phone_number, '55512345')

    def test_phone_number_is_optional(self):
        form = ProfileEditForm(
            data=self._data(phone_local_number=''),
            user=self.user,
            profile=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_phone_longer_than_country_allows(self):
        form = ProfileEditForm(
            data=self._data(phone_local_number='5551234567890'),
            user=self.user,
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('phone_local_number', form.errors)


class UserFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )

    def _data(self, **overrides):
        data = {
            'username': 'cliente',
            'first_name': 'Cliente',
            'last_name': 'Editado',
            'email': 'cliente@example.com',
            'is_active': True,
            'is_staff': False,
        }
        data.update(overrides)
        return data

    def test_valid_update(self):
        form = UserForm(data=self._data(), instance=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username='otro', password='password123')
        form = UserForm(data=self._data(username='otro'), instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class StaffUserCreationFormTests(TestCase):
    def _data(self, **overrides):
        data = {
            'username': 'staff',
            'first_name': 'Staff',
            'last_name': 'User',
            'email': 'staff@example.com',
            'is_active': True,
            'is_staff': True,
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        }
        data.update(overrides)
        return data

    def test_valid_creates_staff_user(self):
        form = StaffUserCreationForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_staff)
        self.assertEqual(user.email, 'staff@example.com')
        self.assertTrue(user.check_password('strong-password-123'))

    def test_password_mismatch(self):
        form = StaffUserCreationForm(data=self._data(password2='diferente'))

        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
