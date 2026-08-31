from rest_framework.routers import DefaultRouter

from articulo import api as api_articulo
from caja import api as api_caja
from cliente import api as api_cliente
from cuentacorriente import api as api_cuentacorriente
from empleado import api as api_empleado
from persona import api as api_persona
from promocion import api as api_promocion
from usuario import api as api_usuario
from venta import api as api_venta


router = DefaultRouter()

router.register('persona', api_persona.PersonaViewSet, basename='persona')
router.register('usuario', api_usuario.UsuarioViewSet, basename='usuario')
router.register('cliente', api_cliente.ClienteViewSet, basename='cliente')
router.register('diassemana', api_promocion.DiasSemanaViewSet, basename='diassemana')
router.register('promocion', api_promocion.PromocionViewSet, basename='promocion')
router.register('promocionarticulo', api_promocion.PromocionArticuloViewSet, basename='promocionarticulo')
router.register('descuento', api_promocion.DescuentoViewSet, basename='descuento')
router.register('cuentacorriente', api_cuentacorriente.CuentaCorrienteViewSet, basename='cuentacorriente')
router.register(
    'movimientocuentacorriente',
    api_cuentacorriente.MovimientoCuentaCorrienteViewSet,
    basename='movimientocuentacorriente',
)
router.register('venta', api_venta.VentaViewSet, basename='venta')
router.register('sucursal', api_empleado.SucursalViewSet, basename='sucursal')
router.register('empleado', api_empleado.EmpleadoViewSet, basename='empleado')
router.register('caja', api_caja.CajaViewSet, basename='caja')
router.register('tarjetadecredito', api_caja.TarjetaDeCreditoViewSet, basename='tarjetadecredito')
router.register('plantarjetadecredito', api_caja.PlanTarjetaDeCreditoViewSet, basename='plantarjetadecredito')
router.register('cuponpagotarjeta', api_caja.CuponPagoTarjetaViewSet, basename='cuponpagotarjeta')
router.register('pagotransferencia', api_caja.PagoTransferenciaViewSet, basename='pagotransferencia')
router.register('tipoiva', api_articulo.TipoIvaViewSet, basename='tipoiva')
router.register('unidadmedida', api_articulo.UnidadMedidaViewSet, basename='unidadmedida')
router.register('categoria', api_articulo.CategoriaViewSet, basename='categoria')
router.register('listaprecio', api_articulo.ListaPrecioViewSet, basename='listaprecio')
router.register('articulo', api_articulo.ArticuloViewSet, basename='articulo')
router.register('precio', api_articulo.PrecioViewSet, basename='precio')
