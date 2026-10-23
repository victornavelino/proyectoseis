from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from empleado.models import Sucursal
from promocion.models import DiasSemana, Promocion


@pytest.mark.django_db
def test_fecha_inicio_posterior_a_fecha_fin_se_rechaza():
    # Antes no había ninguna validación de esto: una promoción cargada con las fechas al revés
    # se guardaba igual, y simplemente nunca quedaba "vigente" ningún día (ver
    # venta.utils.get_promociones_activas), lo que confundía más que un error claro al guardar.
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    dias_semana = DiasSemana.objects.create(lunes=True)

    with pytest.raises(ValidationError):
        Promocion.objects.create(
            nombre='Promo invertida',
            fecha_inicio=date.today(),
            fecha_fin=date.today() - timedelta(days=1),
            es_por_precio=False,
            porcentaje_todos=Decimal('10.00'),
            dias_semana=dias_semana,
            habilitada=True,
            prioridad=1,
            sucursal=sucursal,
        )


@pytest.mark.django_db
def test_fechas_en_orden_correcto_se_acepta():
    sucursal = Sucursal.objects.create(nombre='Casa Central', domicilio='Calle Falsa 123')
    dias_semana = DiasSemana.objects.create(lunes=True)

    promocion = Promocion.objects.create(
        nombre='Promo valida',
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=1),
        es_por_precio=False,
        porcentaje_todos=Decimal('10.00'),
        dias_semana=dias_semana,
        habilitada=True,
        prioridad=1,
        sucursal=sucursal,
    )

    assert promocion.pk is not None
