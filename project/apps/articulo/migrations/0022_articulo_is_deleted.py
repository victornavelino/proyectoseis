# Generated by Django 3.2.4 on 2022-11-10 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articulo', '0021_remove_articulo_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='articulo',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
