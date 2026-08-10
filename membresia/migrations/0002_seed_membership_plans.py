from django.db import migrations


def seed_membership_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('membresia', 'MembershipPlan')
    Service = apps.get_model('servicios', 'Service')

    if MembershipPlan.objects.exists():
        return

    basico = Service.objects.filter(name='Básico').first()
    completo = Service.objects.filter(name='Completo').first()
    premium_detail = Service.objects.filter(name='Premium Detail').first()
    all_services = list(Service.objects.all())

    silver = MembershipPlan.objects.create(
        name='Silver',
        tier_label='Silver',
        emoji='🥈',
        accent='blue',
        monthly_price=249,
        savings_label='Ahorra Q51/mes vs precio regular',
        monthly_wash_limit=4,
        display_order=1,
        features=(
            '4 lavados Básicos al mes\n'
            'Reserva prioritaria\n'
            'Sin cita de última hora\n'
            'Soporte vía WhatsApp'
        ),
    )
    if basico:
        silver.services.add(basico)

    gold = MembershipPlan.objects.create(
        name='Gold',
        tier_label='Gold',
        emoji='🥇',
        accent='red',
        monthly_price=449,
        savings_label='Ahorra Q151/mes vs precio regular',
        monthly_wash_limit=8,
        is_featured=True,
        featured_banner='★ MÁS POPULAR ★',
        display_order=2,
        features=(
            '8 lavados al mes\n'
            'Incluye Básico y Completo\n'
            'Reserva máxima prioridad\n'
            'Soporte VIP WhatsApp\n'
            'Notificaciones anticipadas'
        ),
    )
    for service in (basico, completo):
        if service:
            gold.services.add(service)

    premium = MembershipPlan.objects.create(
        name='Premium',
        tier_label='Premium',
        emoji='💎',
        accent='midnight',
        monthly_price=699,
        savings_label='Lavados ilimitados — máximo ahorro',
        monthly_wash_limit=None,
        covers_all_services=True,
        display_order=3,
        features=(
            'Lavados Básicos ilimitados\n'
            'Cualquier servicio incluido\n'
            'Máxima prioridad de reserva\n'
            'Soporte VIP dedicado\n'
            'Beneficios exclusivos'
        ),
    )
    if all_services:
        premium.services.set(all_services)


def unseed_membership_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('membresia', 'MembershipPlan')
    MembershipPlan.objects.filter(name__in=['Silver', 'Gold', 'Premium']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('membresia', '0001_initial'),
        ('servicios', '0004_update_basico_badge'),
    ]

    operations = [
        migrations.RunPython(seed_membership_plans, unseed_membership_plans),
    ]
