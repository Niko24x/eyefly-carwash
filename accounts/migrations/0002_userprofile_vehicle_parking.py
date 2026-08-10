from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='car_brand',
            field=models.CharField(blank=True, max_length=80, verbose_name='marca del auto'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='car_model',
            field=models.CharField(blank=True, max_length=80, verbose_name='modelo'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='car_color',
            field=models.CharField(blank=True, max_length=40, verbose_name='color'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='car_plate',
            field=models.CharField(blank=True, max_length=20, verbose_name='placa'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='parking_level',
            field=models.CharField(blank=True, max_length=40, verbose_name='sótano'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='parking_number',
            field=models.CharField(blank=True, max_length=40, verbose_name='número de parqueo'),
        ),
    ]
