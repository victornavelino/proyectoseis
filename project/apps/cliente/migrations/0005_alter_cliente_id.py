# Generated by Django 3.2.4 on 2022-04-30 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0004_auto_20220421_0752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
