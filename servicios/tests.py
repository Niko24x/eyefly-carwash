from django.contrib.auth import get_user_model

from django.test import TestCase

from django.urls import reverse



from .models import Service





User = get_user_model()





class ServicePageTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(

            username='cliente',

            email='cliente@example.com',

            password='password123',

        )

        self.staff_user = User.objects.create_user(

            username='admin',

            email='admin@example.com',

            password='password123',

            is_staff=True,

        )

        self.service = Service.objects.create(

            name='Lavado completo',

            description='Lavado exterior e interior.',

        )



    def test_service_list_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(reverse('service_list'))



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_service_list_shows_registered_services_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.get(reverse('service_list'))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.service.name)



    def test_service_create_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(reverse('service_create'))



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_service_create_page_renders_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.get(reverse('service_create'))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Registrar servicio')



    def test_service_create_saves_new_service_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.post(

            reverse('service_create'),

            {

                'name': 'Encerado premium',

                'description': 'Encerado y pulido.',

                'price': '120',

                'duration_minutes': 45,

                'badge': '',

                'features': '',

                'accent': 'blue',

                'display_order': 0,

                'is_active': True,

            },

        )



        self.assertRedirects(response, reverse('service_list'))

        created = Service.objects.get(name='Encerado premium')

        self.assertTrue(created.is_active)



    def test_service_update_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(

            reverse('service_update', args=[self.service.id])

        )



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_service_update_updates_service_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.post(

            reverse('service_update', args=[self.service.id]),

            {

                'name': 'Lavado premium',

                'description': 'Servicio actualizado.',

                'price': '95',

                'duration_minutes': 30,

                'badge': '',

                'features': '',

                'accent': 'blue',

                'display_order': 0,

                'is_active': True,

            },

        )



        self.assertRedirects(response, reverse('service_list'))

        self.service.refresh_from_db()

        self.assertEqual(self.service.name, 'Lavado premium')


