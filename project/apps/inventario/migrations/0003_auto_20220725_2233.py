# Generated by Django 3.2.4 on 2022-07-26 01:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_auto_20220725_2111'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientointerno',
            name='movimiento_relacionado',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='inventario.movimientointerno'),
        ),
        migrations.AlterField(
            model_name='movimientointerno',
            name='principal',
            field=models.BooleanField(default=True, verbose_name='¿Es Principal?'),
        ),
    ]
