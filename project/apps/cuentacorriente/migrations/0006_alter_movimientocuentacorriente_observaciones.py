# Generated by Django 3.2.4 on 2023-08-27 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuentacorriente', '0005_alter_movimientocuentacorriente_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimientocuentacorriente',
            name='observaciones',
            field=models.CharField(max_length=40, null=True, verbose_name='Observaciones'),
        ),
    ]
