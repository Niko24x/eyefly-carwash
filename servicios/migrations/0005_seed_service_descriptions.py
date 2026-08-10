from django.db import migrations


SERVICE_DESCRIPTIONS = {
    'Básico': (
        'Lavado exterior completo con ventanas, llantas y secado manual.'
    ),
    'Completo': (
        'Todo lo del Básico más interior aspirado, tablero, asientos y fragancia.'
    ),
    'Premium Detail': (
        'Detail completo con encerado profesional, motor, plásticos y garantía.'
    ),
    'Lavado general': (
        'Servicio estándar de lavado para tu vehículo.'
    ),
    'Lavado Nuevo': (
        'Servicio de lavado para tu vehículo.'
    ),
}


def seed_service_descriptions(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    for name, description in SERVICE_DESCRIPTIONS.items():
        Service.objects.filter(name=name, description='').update(description=description)


def unseed_service_descriptions(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    for name in SERVICE_DESCRIPTIONS:
        Service.objects.filter(name=name, description=SERVICE_DESCRIPTIONS[name]).update(
            description='',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0004_update_basico_badge'),
    ]

    operations = [
        migrations.RunPython(seed_service_descriptions, unseed_service_descriptions),
    ]
