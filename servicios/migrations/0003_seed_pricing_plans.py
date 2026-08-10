from django.db import migrations


SEED_SERVICES = [
    {
        'name': 'Básico',
        'badge': 'POPULAR',
        'price': 75,
        'duration_minutes': 30,
        'description': 'Lavado exterior completo con ventanas, llantas y secado manual.',
        'accent': 'blue',
        'is_featured': False,
        'display_order': 1,
        'features': (
            'Lavado exterior completo\n'
            'Limpieza de ventanas\n'
            'Lavado de llantas\n'
            'Secado manual\n'
            '!Interior\n'
            '!Encerado\n'
            '!Motor'
        ),
    },
    {
        'name': 'Completo',
        'badge': 'MÁS VENDIDO',
        'price': 150,
        'duration_minutes': 45,
        'description': 'Todo lo del Básico más interior aspirado, tablero, asientos y fragancia.',
        'accent': 'red',
        'is_featured': True,
        'display_order': 2,
        'features': (
            'Todo lo del plan Básico\n'
            'Aspirado de interior\n'
            'Limpieza de tablero\n'
            'Limpieza de asientos\n'
            'Fragancia\n'
            '!Encerado\n'
            '!Motor'
        ),
    },
    {
        'name': 'Premium Detail',
        'badge': 'PREMIUM',
        'price': 299,
        'duration_minutes': 90,
        'description': 'Detail completo con encerado profesional, motor, plásticos y garantía.',
        'accent': 'dark',
        'is_featured': False,
        'display_order': 3,
        'features': (
            'Todo lo del plan Completo\n'
            'Detail completo\n'
            'Encerado profesional\n'
            'Limpieza de motor\n'
            'Tratamiento de plásticos\n'
            'Garantía de satisfacción'
        ),
    },
]


def seed_services(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    if Service.objects.exists():
        return
    for data in SEED_SERVICES:
        Service.objects.create(**data)


def unseed_services(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    names = [data['name'] for data in SEED_SERVICES]
    Service.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0002_alter_service_options_service_accent_service_badge_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_services, unseed_services),
    ]
