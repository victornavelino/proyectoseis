from django.db import models

# Create your models here.
from articulo.models import ListaPrecio
from persona.models import Persona


class Cliente(models.Model):
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-id']

    RESPONSABLE_INSCRIPTO = 'ri'
    RESPONSABLE_NO_INSCRIPTO = 'rn'
    EXENTO = 'ex'
    MONOTRIBUTO = 'mo'
    CONSUMIDOR_FINAL = 'cf'

    CONDICIONES_IVA = (
        (RESPONSABLE_INSCRIPTO, 'Responsable inscripto'),
        (RESPONSABLE_NO_INSCRIPTO, 'Responsable no inscripto'),
        (EXENTO, 'Exento'),
        (MONOTRIBUTO, 'Monotributo'),
        (CONSUMIDOR_FINAL, 'Consumidor final')
    )

    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, editable=True)

    condicion_iva = models.CharField(max_length=30, choices=CONDICIONES_IVA, verbose_name='Condición frente al IVA')

    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, null=True, verbose_name='Lista de Precios')

    # Un único descuento manual por cliente (ej. "Gastronómicos", "EMPLEADOS"), aplicado como %
    # sobre el precio de lista_precio al cobrar — ver venta.utils.calcular_precio_venta_articulo.
    # "CUMPLEAÑOS" queda aparte como caso automático (depende de la fecha, no tiene sentido
    # asignarlo a mano acá).
    descuento = models.ForeignKey(
        'promocion.Descuento', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Descuento',
    )

    fecha_alta = models.DateField(auto_now=True)

    def __str__(self):
        return self.persona.obtener_nombre_completo()


