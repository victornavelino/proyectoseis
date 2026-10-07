from django.db import migrations, models
import django.db.models.deletion


def poblar_bancos_desde_texto(apps, schema_editor):
    """Crea un `Banco` por cada texto distinto ya cargado en `PagoTransferencia.banco` (texto
    libre hasta esta migración) y liga cada fila al `Banco` correspondiente vía el campo nuevo
    `banco_fk` -- sin esto, convertir la columna a FK más abajo perdería el dato ya cargado en
    las 3 bases de producción (el deploy corre `migrate --noinput` sin supervisión)."""
    Banco = apps.get_model('caja', 'Banco')
    PagoTransferencia = apps.get_model('caja', 'PagoTransferencia')

    cache = {}
    pagos = PagoTransferencia.objects.exclude(banco__isnull=True).exclude(banco__exact='')
    for pago in pagos:
        nombre = pago.banco.strip()
        if not nombre:
            continue
        banco = cache.get(nombre.lower())
        if banco is None:
            banco, _ = Banco.objects.get_or_create(nombre=nombre)
            cache[nombre.lower()] = banco
        pago.banco_fk = banco
        pago.save(update_fields=['banco_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0039_caja_arqueo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=60, unique=True, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Banco',
                'verbose_name_plural': 'Bancos',
                'ordering': ['nombre'],
            },
        ),
        migrations.AddField(
            model_name='pagotransferencia',
            name='banco_fk',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='caja.banco',
                verbose_name='Banco',
            ),
        ),
        migrations.RunPython(poblar_bancos_desde_texto, migrations.RunPython.noop),
        migrations.RemoveField(model_name='pagotransferencia', name='banco'),
        migrations.RenameField(model_name='pagotransferencia', old_name='banco_fk', new_name='banco'),
        migrations.CreateModel(
            name='PagoQr',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('importe', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Importe')),
                ('nombre', models.CharField(blank=True, max_length=40, null=True, verbose_name='Nombre')),
                ('apellido', models.CharField(blank=True, max_length=30, null=True, verbose_name='Apellido')),
                ('documento_identidad', models.CharField(max_length=12, verbose_name='Documento Identidad')),
                ('fecha', models.DateTimeField(auto_now=True, verbose_name='Fecha')),
                ('observaciones', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observaciones')),
                ('banco', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='caja.banco',
                    verbose_name='Banco',
                )),
                ('venta', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='venta.venta',
                    verbose_name='Venta',
                )),
            ],
            options={
                'verbose_name': 'Pago Con QR',
                'verbose_name_plural': 'Pagos Con QR',
                'ordering': ['-id'],
            },
        ),
    ]
