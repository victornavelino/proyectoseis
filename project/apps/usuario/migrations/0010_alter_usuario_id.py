# Generated by Django 3.2.4 on 2022-05-05 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuario', '0009_auto_20220504_0750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
