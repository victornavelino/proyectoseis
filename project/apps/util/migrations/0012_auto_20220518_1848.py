# Generated by Django 3.1.3 on 2022-05-18 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('util', '0011_alter_telefono_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telefono',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
