# Generated by Django 3.2.4 on 2022-04-21 02:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0003_alter_persona_id'),
        ('usuario', '0003_auto_20220420_1114'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='empleado',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='persona.empleado', verbose_name='Empleado'),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
