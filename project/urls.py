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
from pathlib import Path

from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from oauth2_provider.urls import base_urlpatterns
from django.urls import path, include, re_path

from caja.views import planes_tarjeta, cobrar_ticket, cerrar_caja, imprimir_cierre_caja, plan_tarjeta, imprimir_cierre_caja_pdf
from cuentacorriente.views import get_cc_cliente
from inventario.views import recepcionar_movimiento_ingreso

from project.apps.articulo.views import get_precio_articulo, copiar_precios, copiar_precios_proceso,get_listas_precio_sucursal
from project.apps.venta.views import exportar_ventas, get_listaprecio, imprimir_ticket
from project.router import router
from promocion.views import copiar_promos, copiar_promociones, get_promociones_sucursal
from usuario.api import RegistroUsuarioAPIView
from django.conf import settings

from venta.forms import form_dialog_pago
from venta.views import get_valores, get_articulos, get_articulos_todos, get_clientes, guardar_venta, \
    nuevo_pago_efectivo, listar_ventas, get_ventas, cobrar_venta, mostrar_dialog, form_test, get_tarjetas, \
    verificar_cumpleanios, get_empleados

admin.site.site_header = getattr(settings, 'PROJECT_NAME_HEADER')
admin.site.site_title = getattr(settings, 'PROJECT_NAME_TITLE')

# Build de producción del frontend React (DEC-009: mismo dominio que la API — ver
# docs/modernizacion/DECISIONES.md). El Dockerfile lo copia a project/assets/frontend/ en un
# stage de Node antes de collectstatic, así que WhiteNoise ya sirve sus JS/CSS con hash bajo
# /static/frontend/ (ver STATICFILES_DIRS en settings/base.py y `base` en frontend/vite.config.ts).
# El index.html en sí no es un asset con hash: se lee y devuelve tal cual en `frontend_index`.
FRONTEND_INDEX_HTML = Path(__file__).resolve().parent / 'assets' / 'frontend' / 'index.html'


def frontend_index(request, *args, **kwargs):
    try:
        contenido = FRONTEND_INDEX_HTML.read_text(encoding='utf-8')
    except FileNotFoundError:
        # En desarrollo local no se corre el build (se usa `npm run dev` en :5173) — este mensaje
        # sólo debería verse si faltó el build en un despliegue de producción.
        return HttpResponse(
            'Frontend no compilado. Corré el build de frontend/ (ver Dockerfile) o usá '
            '`npm run dev` en desarrollo.',
            status=501,
        )
    return HttpResponse(contenido)


urlpatterns = [
                  path('admin/venta/guardar_venta/', guardar_venta, name='guardar_venta'),
                  path('admin/venta/articulo/<str:articulo_codigo>/<int:cliente_pk>', get_valores, name='get_valores'),
                  path('admin/venta/articulos/<str:articulo>', get_articulos, name='articulos'),
                  path('admin/venta/articulos_todos/', get_articulos_todos, name='articulo_todos'),
                  path('admin/venta/clientes/', get_clientes, name='clientes'),
                  path('admin/venta/empleados/', get_empleados, name='empleados'),
                  path('admin/venta/clientes/<int:pk_cliente>', verificar_cumpleanios, name='verificar_cumpleanios'),
                  path('admin/venta/clientes/get_listaprecio/<int:pk_cliente>', get_listaprecio, name='get_listaprecio'),
                  path('admin/caja/tarjetas_de_credito/', get_tarjetas, name='tarjetas'),
                  path('admin/caja/planes_tarjeta/<int:pk_tarjeta>', planes_tarjeta, name='planes_tarjeta'),
                  path('admin/caja/plan_tarjeta/<int:id_plan_tarjeta>', plan_tarjeta, name='plan_tarjeta'),
                  path('admin/venta/venta/nuevo_pago_efectivo/', nuevo_pago_efectivo, name='nuevo_pago_efectivo'),
                  path('admin/venta/venta/listado_de_ventas/', listar_ventas, name='listar_ventas'),
                  path('admin/venta/venta/listado_de_ventas/', get_ventas, name='get_ventas'),
                  path('admin/venta/venta/cobrar_venta/<int:numero_ticket>', cobrar_venta, name='cobrar_venta'),
                  path('admin/venta/venta/cobrar_venta/', cobrar_ticket, name='cobrar_ticket'),
                  path('admin/venta/venta/cobrar_venta/', mostrar_dialog, name='nuevo_pago'),
                  path('admin/venta/venta/exportar_ventas', exportar_ventas, name='exportar_ventas'),
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
                  # Login genérico (cualquier Usuario activo, no sólo staff — a diferencia de
                  # /admin/login/) usado como LOGIN_URL por el flujo OAuth2 del frontend SPA.
                  # Ver docs/modernizacion/DECISIONES.md DEC-002.
                  path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
                  path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
                  path('oauth2/', include((base_urlpatterns, 'oauth2_provider'), namespace='oauth2_provider')),
                  # /auth/callback es la redirect_uri del flujo Authorization Code + PKCE del
                  # frontend SPA (VITE_OAUTH_REDIRECT_URI / OAUTH2_SPA_REDIRECT_URIS) — la procesa
                  # React Router del lado del cliente, no Django. Cae bajo el mismo prefijo
                  # `auth/` que reserva drf_social_oauth2 (línea de abajo), así que hay que
                  # explicitarla ANTES de ese include para que sirva el index.html del SPA en vez
                  # de intentar resolverla como una URL de drf_social_oauth2/social_django (donde
                  # no existe, y sin esto termina cayendo en el catch-all de static() al final de
                  # este archivo devolviendo un 404 crudo de archivo no encontrado).
                  path('auth/callback', frontend_index, name='oauth_callback'),
                  path('auth/callback/', frontend_index),
                  path('auth/', include('drf_social_oauth2.urls')),
                  path('api/v1/usuario/registro/', RegistroUsuarioAPIView.as_view(), name='registro_usuario'),
                  path('api/v1/', include(router.urls)),

                  # Catch-all del frontend React (DEC-009): sirve el mismo index.html para "/" y
                  # para cualquier ruta de React Router (ej. /articulos, /ventas/nueva) — así un
                  # refresh de página no da 404, el ruteo lo resuelve el cliente. Va al final y
                  # excluye explícitamente los prefijos de Django para no taparle un 404 real a
                  # la API/admin (Django reintenta el siguiente patrón top-level cuando un
                  # include() no matchea nada adentro).
                  re_path(
                      r'^(?!admin/|api/|oauth2/|auth/|login/|logout/|media/|static/).*$',
                      frontend_index,
                      name='frontend_index',
                  ),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ACTIVAR_HERRAMIENTAS_DEBUGGING:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
