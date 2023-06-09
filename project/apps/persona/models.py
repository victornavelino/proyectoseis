from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

#from usuario.models import Usuario


class Persona(models.Model):
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['-id']

    nombre = models.CharField(max_length=30, verbose_name='Nombre')
    apellido = models.CharField(max_length=30, verbose_name='Apellido')
    documento_identidad = models.CharField(max_length=12, verbose_name='Documento Identidad', unique=True)
    telefono = models.CharField(max_length=30, verbose_name='Teléfono', blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True, verbose_name='Correo Electrónico')
    domicilio = models.CharField(max_length=100, verbose_name='Domicilio')
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento', blank=True, null=True)

    @staticmethod
    def autocomplete_search_fields():
        return 'nombre', 'apellido'

    def __str__(self):
        return self.obtener_nombre_completo()

    def obtener_nombre_completo(self):
        nombre_completo = f'{self.apellido}, {self.nombre}'
        return nombre_completo.strip()

    obtener_nombre_completo.short_description = 'Nombre Completo'


