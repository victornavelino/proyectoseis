# Generated by Django 3.2.4 on 2022-06-27 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0024_auto_20220626_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuentacorriente',
            name='observaciones',
            field=models.CharField(max_length=100, verbose_name='Observaciones'),
        ),
    ]
