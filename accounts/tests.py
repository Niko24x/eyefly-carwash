from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )

    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear cuenta')

    def test_register_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'nuevo',
                'first_name': 'Nuevo',
                'last_name': 'Cliente',
                'email': 'nuevo@example.com',
                'password1': 'strong-password-123',
                'password2': 'strong-password-123',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))
        self.assertTrue(User.objects.filter(username='nuevo').exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='nuevo').id)

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar sesión')

    def test_login_redirects_to_appointment_list(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'cliente',
                'password': 'password123',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))

    def test_login_accepts_email_address(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'cliente@example.com',
                'password': 'password123',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))

    def test_logout_redirects_to_login(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))

    def test_account_profile_requires_login(self):
        response = self.client.get(reverse('account_profile'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response['Location'])

    def test_account_profile_shows_user_information(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('account_profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mi cuenta')
        self.assertContains(response, 'cliente')
        self.assertContains(response, 'cliente@example.com')
        self.assertContains(response, 'Editar perfil')

    def test_account_profile_edit_updates_user_and_phone(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.post(
            reverse('account_profile_edit'),
            {
                'first_name': 'Cliente',
                'last_name': 'Actualizado',
                'email': 'nuevo@example.com',
                'phone_country_code': '502',
                'phone_local_number': '55512345',
            },
        )

        self.assertRedirects(response, reverse('account_profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'Actualizado')
        self.assertEqual(self.user.email, 'nuevo@example.com')
        self.assertEqual(self.user.profile.phone_country_code, '502')
        self.assertEqual(self.user.profile.phone_number, '55512345')

    def test_account_profile_edit_requires_login(self):
        response = self.client.get(reverse('account_profile_edit'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response['Location'])

    def test_user_list_requires_staff_user(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('user_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_staff_user_can_view_user_list(self):
        staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True,
        )
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('user_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_staff_user_can_update_user(self):
        User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True,
        )
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('user_update', args=[self.user.id]),
            {
                'username': 'cliente',
                'first_name': 'Cliente',
                'last_name': 'Actualizado',
                'email': 'cliente@example.com',
                'is_active': True,
                'is_staff': False,
            },
        )

        self.assertRedirects(response, reverse('user_list'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'Actualizado')
