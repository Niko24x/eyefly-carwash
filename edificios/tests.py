from django.contrib.auth import get_user_model

from django.test import TestCase

from django.urls import reverse



from .models import Building





User = get_user_model()





class BuildingPageTests(TestCase):

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

        self.other_user = User.objects.create_user(

            username='otro',

            email='otro@example.com',

            password='password123',

        )

        self.admin_user = User.objects.create_user(

            username='adminedificio',

            email='adminedificio@example.com',

            password='password123',

        )

        self.building = Building.objects.create(

            created_by=self.user,

            name='Torre Central',

            address='Av. Principal 123',

            contact_name='Ana Lopez',

            phone_number='5551234567',

            email='ana@example.com',

            notes='Entrada por estacionamiento.',

        )

        self.building.admins.add(self.user)

        self.other_building = Building.objects.create(

            created_by=self.other_user,

            name='Edificio Privado',

            address='Calle Cerrada 99',

            contact_name='Carlos Ruiz',

            phone_number='5557654321',

            email='carlos@example.com',

        )

        self.other_building.admins.add(self.other_user)



    def test_building_list_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(reverse('building_list'))



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_building_list_shows_all_buildings_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.get(reverse('building_list'))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.building.name)

        self.assertContains(response, 'Edificio Privado')



    def test_building_create_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(reverse('building_create'))



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_building_create_page_renders_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.get(reverse('building_create'))



        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Registrar edificio')



    def test_building_create_assigns_logged_in_staff_user(self):

        self.client.login(username='admin', password='password123')



        response = self.client.post(

            reverse('building_create'),

            {

                'name': 'Residencial Norte',

                'address': 'Calle Norte 456',

                'contact_name': 'Maria Diaz',

                'phone_number': '5551112222',

                'email': 'maria@example.com',

                'autos_por_turno': 2,

                'admins': [self.admin_user.id],

                'notes': 'Coordinar con administracion.',

            },

        )



        self.assertRedirects(response, reverse('building_list'))

        created = Building.objects.get(name='Residencial Norte')

        self.assertEqual(created.created_by, self.staff_user)

        self.assertIn(self.staff_user, created.admins.all())

        self.assertIn(self.admin_user, created.admins.all())



    def test_building_update_requires_staff(self):

        self.client.login(username='cliente', password='password123')



        response = self.client.get(

            reverse('building_update', args=[self.building.id])

        )



        self.assertEqual(response.status_code, 302)

        self.assertIn('/admin/login/', response['Location'])



    def test_building_update_updates_building_for_staff(self):

        self.client.login(username='admin', password='password123')



        response = self.client.post(

            reverse('building_update', args=[self.building.id]),

            {

                'name': 'Torre Renovada',

                'address': 'Av. Principal 123',

                'contact_name': 'Ana Lopez',

                'phone_number': '5551234567',

                'email': 'ana@example.com',

                'autos_por_turno': 2,

                'admins': [self.user.id],

                'notes': 'Entrada por estacionamiento.',

            },

        )



        self.assertRedirects(response, reverse('building_list'))

        self.building.refresh_from_db()

        self.assertEqual(self.building.name, 'Torre Renovada')

    def test_building_list_shows_schedule_and_toggle_actions(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('building_list'))

        self.assertContains(response, 'Horario')
        self.assertContains(response, 'Desactivar citas')
        self.assertContains(
            response,
            reverse('configuracion:building_schedule_edit', args=[self.building.id]),
        )

    def test_staff_can_deactivate_building_for_new_appointments(self):
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('building_toggle_appointments', args=[self.building.id])
        )

        self.assertRedirects(response, reverse('building_list'))
        self.building.refresh_from_db()
        self.assertFalse(self.building.accepts_appointments)

    def test_staff_can_reactivate_building_for_appointments(self):
        self.building.accepts_appointments = False
        self.building.save(update_fields=['accepts_appointments'])
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('building_toggle_appointments', args=[self.building.id])
        )

        self.assertRedirects(response, reverse('building_list'))
        self.building.refresh_from_db()
        self.assertTrue(self.building.accepts_appointments)
