from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


class TranslateDjangoValidationErrorMixin:
    """Varios modelos de este proyecto validan reglas de negocio en
    `Model.clean()`, invocado desde el propio `Model.save()` vía
    `full_clean()` (no sólo desde un `ModelForm` de Django Admin) — por
    ejemplo `promocion.Promocion`. Sin este mixin esa regla se sigue
    aplicando igual, pero el `django.core.exceptions.ValidationError` que
    lanza escapa del manejo de errores de DRF y termina en un 500 en vez de
    un 400 con el detalle. Usarlo en cualquier `ModelViewSet` cuyo modelo
    valide reglas propias en `save()`, para no tener que duplicar esa
    lógica en el serializer.
    """

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except DjangoValidationError as exc:
            raise DRFValidationError(self._as_error_detail(exc))

    def perform_update(self, serializer):
        try:
            super().perform_update(serializer)
        except DjangoValidationError as exc:
            raise DRFValidationError(self._as_error_detail(exc))

    @staticmethod
    def _as_error_detail(exc):
        if hasattr(exc, 'message_dict'):
            return exc.message_dict
        return exc.messages
