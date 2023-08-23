"""settings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
from oauth2_provider.urls import base_urlpatterns
from django.urls import path, include

from caja.views import planes_tarjeta, cobrar_ticket, cerrar_caja, imprimir_cierre_caja, imprimir_cierre_caja_pdf
from cuentacorriente.views import get_cc_cliente
from inventario.views import recepcionar_movimiento_ingreso

from project.apps.articulo.views import get_precio_articulo, copiar_precios, copiar_precios_proceso,get_listas_precio_sucursal
from project.apps.venta.views import get_listaprecio, imprimir_ticket
from project.router import router
from promocion.views import copiar_promos, copiar_promociones, get_promociones_sucursal
from usuario.api import RegistroUsuarioAPIView
from django.conf import settings

from venta.forms import form_dialog_pago
from venta.views import get_valores, get_articulos, get_articulos_todos, get_clientes, guardar_venta, \
    nuevo_pago_efectivo, listar_ventas, get_ventas, cobrar_venta, mostrar_dialog, form_test, get_tarjetas, \
    verificar_cumpleanios

admin.site.site_header = getattr(settings, 'PROJECT_NAME_HEADER')
admin.site.site_title = getattr(settings, 'PROJECT_NAME_TITLE')

urlpatterns = [
                  path(
                      '',
                      RedirectView.as_view(
                          url=f'{settings.FORCE_SCRIPT_NAME}/admin/' if settings.FORCE_SCRIPT_NAME else '/admin/'
                      )
                  ),
                  url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
                  path('admin/venta/guardar_venta/', guardar_venta, name='guardar_venta'),
                  path('admin/venta/articulo/<str:articulo_codigo>/<int:cliente_pk>', get_valores, name='get_valores'),
                  path('admin/venta/articulos/<str:articulo>', get_articulos, name='articulos'),
                  path('admin/venta/articulos_todos/', get_articulos_todos, name='articulo_todos'),
                  path('admin/venta/clientes/', get_clientes, name='clientes'),
                  path('admin/venta/clientes/<int:pk_cliente>', verificar_cumpleanios, name='verificar_cumpleanios'),
                  path('admin/venta/clientes/get_listaprecio/<int:pk_cliente>', get_listaprecio, name='get_listaprecio'),
                  path('admin/caja/tarjetas_de_credito/', get_tarjetas, name='tarjetas'),
                  path('admin/caja/planes_tarjeta/<int:pk_tarjeta>', planes_tarjeta, name='planes_tarjeta'),
                  path('admin/venta/venta/nuevo_pago_efectivo/', nuevo_pago_efectivo, name='nuevo_pago_efectivo'),
                  path('admin/venta/venta/listado_de_ventas/', listar_ventas, name='listar_ventas'),
                  path('admin/venta/venta/listado_de_ventas/', get_ventas, name='get_ventas'),
                  path('admin/venta/venta/cobrar_venta/<int:numero_ticket>', cobrar_venta, name='cobrar_venta'),
                  path('admin/venta/venta/cobrar_venta/', cobrar_ticket, name='cobrar_ticket'),
                  path('admin/venta/venta/cobrar_venta/', mostrar_dialog, name='nuevo_pago'),
                  path('admin/venta/venta/<int:numero_ticket>', imprimir_ticket, name='imprimir_ticket'),
                  path('admin/promocion/promocion/copiar_promociones/', copiar_promociones, name='copiar_promociones'),
                  path('admin/articulo/precio/copiar_precios/', copiar_precios, name='copiar_precios'),
                  path('admin/articulo/precio/copiar_precios_proceso/', copiar_precios_proceso, name='copiar_precios_proceso'),
                  path('admin/articulo/precio/listas_precio/<int:pk_sucursal>', get_listas_precio_sucursal,
                       name='get_listas_precio_sucursal'),
                  path('admin/promocion/promocion/copiar_promos/', copiar_promos, name='copiar_promos'),
                  path('admin/promocion/promocion/get_promociones_sucursal/<int:pk_sucursal>', get_promociones_sucursal, name='get_promociones_sucursal'),
                  path('admin/precio/precio_articulo/<int:id_articulo>', get_precio_articulo, name='precio_articulo'),
                  path('admin/inventario/movimientointerno/<int:numero_lote>', recepcionar_movimiento_ingreso, name='recepcionar_movimiento'),
                  path('admin/cuentacorriente/<int:cliente_id>', get_cc_cliente, name='get_cc_cliente'),
                  path('admin/caja/caja/cerrar_caja/', cerrar_caja, name='cerrar_caja'),
                  path('admin/caja/imprimir_cierre_caja/<int:id_caja>', imprimir_cierre_caja,
                       name='imprimir_cierre_caja'),
                  path('admin/caja/imprimir/<int:id_caja>', imprimir_cierre_caja_pdf, name='imprimir_cierre_caja_pdf'),
                  path('admin/', admin.site.urls),
                  path('oauth2/', include((base_urlpatterns, 'oauth2_provider'), namespace='oauth2_provider')),
                  path('auth/', include('rest_framework_social_oauth2.urls')),
                  path('api/v1/usuario/registro/', RegistroUsuarioAPIView.as_view(), name='registro_usuario'),
                  path('api/v1/', include(router.urls)),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ACTIVAR_HERRAMIENTAS_DEBUGGING:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
