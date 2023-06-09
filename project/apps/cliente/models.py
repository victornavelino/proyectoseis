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

    fecha_alta = models.DateField(auto_now=True)

    fidelizado = models.BooleanField(default=False)

    def __str__(self):
        return self.persona.obtener_nombre_completo()


