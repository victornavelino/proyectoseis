# Generated by Django 3.2.4 on 2023-08-25 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0033_auto_20230823_1848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plantarjetadecredito',
            name='nombre_plan',
            field=models.CharField(max_length=75, verbose_name='Nombre del Plan'),
        ),
    ]
