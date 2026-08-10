from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('edificios', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='building',
            old_name='user',
            new_name='created_by',
        ),
        migrations.AlterField(
            model_name='building',
            name='created_by',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_buildings',
                to=settings.AUTH_USER_MODEL,
                verbose_name='registrado por',
            ),
        ),
        migrations.AddField(
            model_name='building',
            name='admins',
            field=models.ManyToManyField(
                blank=True,
                related_name='admin_buildings',
                to=settings.AUTH_USER_MODEL,
                verbose_name='administradores',
            ),
        ),
    ]
