import type { ReactNode } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import AuthCallback from './auth/AuthCallback'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import ArticulosPage from './features/articulos/ArticulosPage'
import CategoriasPage from './features/catalogo/CategoriasPage'
import ListasPrecioPage from './features/catalogo/ListasPrecioPage'
import PreciosPage from './features/catalogo/PreciosPage'
import TiposIvaPage from './features/catalogo/TiposIvaPage'
import UnidadesMedidaPage from './features/catalogo/UnidadesMedidaPage'
import AdelantosPage from './features/caja/AdelantosPage'
import BancosPage from './features/caja/BancosPage'
import CajaPage from './features/caja/CajaPage'
import GastosPage from './features/caja/GastosPage'
import IngresosPage from './features/caja/IngresosPage'
import PlanesTarjetaPage from './features/caja/PlanesTarjetaPage'
import RetirosEfectivoPage from './features/caja/RetirosEfectivoPage'
import SueldosPage from './features/caja/SueldosPage'
import TarjetasPage from './features/caja/TarjetasPage'
import TiposGastoPage from './features/caja/TiposGastoPage'
import TiposIngresoPage from './features/caja/TiposIngresoPage'
import ClientesPage from './features/clientes/ClientesPage'
import CuentasCorrientesPage from './features/cuentacorriente/CuentasCorrientesPage'
import EmpleadosPage from './features/empleados/EmpleadosPage'
import SucursalesPage from './features/empleados/SucursalesPage'
import InicioPage from './features/inicio/InicioPage'
import DescuentosPage from './features/promociones/DescuentosPage'
import PromocionesPage from './features/promociones/PromocionesPage'
import UsuariosPage from './features/usuarios/UsuariosPage'
import CobroVentaPage from './features/ventas/CobroVentaPage'
import VentaNuevaPage from './features/ventas/VentaNuevaPage'
import VentasListPage from './features/ventas/VentasListPage'

function Privada({
  children,
  requierePermiso,
  fallbackSiSinAcceso,
}: {
  children: ReactNode
  requierePermiso?: string
  fallbackSiSinAcceso?: string
}) {
  return (
    <ProtectedRoute requierePermiso={requierePermiso} fallbackSiSinAcceso={fallbackSiSinAcceso}>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  )
}

// Mismos gates que components/AppLayout.tsx (NAV) — permisos dedicados por sección (ver
// usuario.models.Usuario.Meta.permissions). Duplicados a propósito en vez de importados: este
// archivo no debería depender del menú para saber qué rutas proteger, y viceversa.
const GATE_DASHBOARD = 'usuario.ver_seccion_dashboard'
const GATE_CATALOGO = 'usuario.ver_seccion_catalogo'
const GATE_PERSONAL = 'usuario.ver_seccion_personal'
const GATE_PROMOCIONES = 'usuario.ver_seccion_promociones'
const GATE_CAJA = 'usuario.ver_seccion_caja'

const RUTAS: { path: string; element: ReactNode; requierePermiso?: string; fallbackSiSinAcceso?: string }[] = [
  // Todo el mundo cae acá después de loguearse, tenga o no el permiso de Dashboard — por eso el
  // fallback silencioso a "/ventas" (ruta sin gate, accesible para cualquier autenticado) en vez
  // de la pantalla de "Sin acceso" (ver ProtectedRoute.fallbackSiSinAcceso).
  { path: '/', element: <InicioPage />, requierePermiso: GATE_DASHBOARD, fallbackSiSinAcceso: '/ventas' },
  { path: '/ventas', element: <VentasListPage /> },
  { path: '/ventas/nueva', element: <VentaNuevaPage />, requierePermiso: 'venta.add_venta' },
  { path: '/ventas/:numeroTicket/cobrar', element: <CobroVentaPage />, requierePermiso: 'caja.add_cobroventa' },
  { path: '/articulos', element: <ArticulosPage />, requierePermiso: GATE_CATALOGO },
  { path: '/articulos/categorias', element: <CategoriasPage />, requierePermiso: GATE_CATALOGO },
  { path: '/articulos/unidades-medida', element: <UnidadesMedidaPage />, requierePermiso: GATE_CATALOGO },
  { path: '/articulos/tipos-iva', element: <TiposIvaPage />, requierePermiso: GATE_CATALOGO },
  { path: '/articulos/listas-precio', element: <ListasPrecioPage />, requierePermiso: GATE_CATALOGO },
  { path: '/articulos/precios', element: <PreciosPage />, requierePermiso: GATE_CATALOGO },
  { path: '/clientes', element: <ClientesPage /> },
  { path: '/clientes/cuentas-corrientes', element: <CuentasCorrientesPage /> },
  { path: '/empleados', element: <EmpleadosPage />, requierePermiso: GATE_PERSONAL },
  { path: '/empleados/sucursales', element: <SucursalesPage />, requierePermiso: GATE_PERSONAL },
  { path: '/empleados/usuarios', element: <UsuariosPage />, requierePermiso: GATE_PERSONAL },
  { path: '/promociones', element: <PromocionesPage />, requierePermiso: GATE_PROMOCIONES },
  { path: '/promociones/descuentos', element: <DescuentosPage />, requierePermiso: GATE_PROMOCIONES },
  { path: '/caja', element: <CajaPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/ingresos', element: <IngresosPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/sueldos', element: <SueldosPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/adelantos', element: <AdelantosPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/retiros-efectivo', element: <RetirosEfectivoPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/gastos', element: <GastosPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/tarjetas', element: <TarjetasPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/planes-tarjeta', element: <PlanesTarjetaPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/tipos-ingreso', element: <TiposIngresoPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/tipos-gasto', element: <TiposGastoPage />, requierePermiso: GATE_CAJA },
  { path: '/caja/bancos', element: <BancosPage />, requierePermiso: GATE_CAJA },
]

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallback />} />
          {RUTAS.map((ruta) => (
            <Route
              key={ruta.path}
              path={ruta.path}
              element={
                <Privada requierePermiso={ruta.requierePermiso} fallbackSiSinAcceso={ruta.fallbackSiSinAcceso}>
                  {ruta.element}
                </Privada>
              }
            />
          ))}
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
