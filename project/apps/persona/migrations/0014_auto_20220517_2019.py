# Generated by Django 3.1.3 on 2022-05-17 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0013_alter_persona_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persona',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
