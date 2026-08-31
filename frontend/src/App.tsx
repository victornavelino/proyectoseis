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
import CajaPage from './features/caja/CajaPage'
import PlanesTarjetaPage from './features/caja/PlanesTarjetaPage'
import TarjetasPage from './features/caja/TarjetasPage'
import ClientesPage from './features/clientes/ClientesPage'
import CuentasCorrientesPage from './features/cuentacorriente/CuentasCorrientesPage'
import EmpleadosPage from './features/empleados/EmpleadosPage'
import SucursalesPage from './features/empleados/SucursalesPage'
import InicioPage from './features/inicio/InicioPage'
import DescuentosPage from './features/promociones/DescuentosPage'
import PromocionesPage from './features/promociones/PromocionesPage'
import CobroVentaPage from './features/ventas/CobroVentaPage'
import VentaNuevaPage from './features/ventas/VentaNuevaPage'
import VentasListPage from './features/ventas/VentasListPage'

function Privada({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  )
}

const RUTAS: { path: string; element: ReactNode }[] = [
  { path: '/', element: <InicioPage /> },
  { path: '/ventas', element: <VentasListPage /> },
  { path: '/ventas/nueva', element: <VentaNuevaPage /> },
  { path: '/ventas/:numeroTicket/cobrar', element: <CobroVentaPage /> },
  { path: '/articulos', element: <ArticulosPage /> },
  { path: '/articulos/categorias', element: <CategoriasPage /> },
  { path: '/articulos/unidades-medida', element: <UnidadesMedidaPage /> },
  { path: '/articulos/tipos-iva', element: <TiposIvaPage /> },
  { path: '/articulos/listas-precio', element: <ListasPrecioPage /> },
  { path: '/articulos/precios', element: <PreciosPage /> },
  { path: '/clientes', element: <ClientesPage /> },
  { path: '/clientes/cuentas-corrientes', element: <CuentasCorrientesPage /> },
  { path: '/empleados', element: <EmpleadosPage /> },
  { path: '/empleados/sucursales', element: <SucursalesPage /> },
  { path: '/promociones', element: <PromocionesPage /> },
  { path: '/promociones/descuentos', element: <DescuentosPage /> },
  { path: '/caja', element: <CajaPage /> },
  { path: '/caja/tarjetas', element: <TarjetasPage /> },
  { path: '/caja/planes-tarjeta', element: <PlanesTarjetaPage /> },
]

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallback />} />
          {RUTAS.map((ruta) => (
            <Route key={ruta.path} path={ruta.path} element={<Privada>{ruta.element}</Privada>} />
          ))}
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
