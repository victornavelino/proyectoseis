# Generated by Django 3.2.4 on 2022-04-30 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venta', '0005_auto_20220421_0752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ventaarticulo',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
