from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0038_remove_pagotransferencia_cliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='caja',
            name='arqueo',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Arqueo de caja'
            ),
        ),
    ]
