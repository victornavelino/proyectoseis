# Generated by Django 3.2.4 on 2023-08-23 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0032_alter_cuponpagotarjeta_venta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuponpagotarjeta',
            name='lote',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Lote'),
        ),
        migrations.AlterField(
            model_name='cuponpagotarjeta',
            name='numero_cupon',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Numero de Cupon'),
        ),
        migrations.AlterField(
            model_name='cuponpagotarjeta',
            name='numero_tarjeta',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Numero de Tarjeta'),
        ),
        migrations.AlterField(
            model_name='cuponpagotarjeta',
            name='observaciones',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Observaciones'),
        ),
    ]
