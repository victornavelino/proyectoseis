# Generated by Django 3.2.4 on 2022-11-08 11:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('articulo', '0019_articulo_borrado'),
        ('venta', '0020_alter_cierreventas_sucursal'),
    ]

    operations = [
        migrations.AddField(
            model_name='ventaarticulo',
            name='articulo',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='articulo.articulo', verbose_name='Articulo'),
        ),
    ]
