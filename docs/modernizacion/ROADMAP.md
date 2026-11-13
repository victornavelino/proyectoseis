# Roadmap

Estados: `PENDIENTE` | `EN CURSO` | `COMPLETADO` | `BLOQUEADO`.

Propuesta de etapas basada en lo relevado (no la lista orientativa genérica de
`especificaciones.md` §9, sino ajustada a lo que el código realmente tiene y necesita). Se puede
reordenar; lo único fijo es que **1 va antes que todo** y que **6 (base React) no puede empezar
sin haber resuelto PEND-A/PEND-B de `DECISIONES.md`**.

| # | Etapa | Estado | Depende de | Criterio de finalización |
|---|---|---|---|---|
| 1 | Auditoría y relevamiento | **COMPLETADO** | — | Esta documentación (`SISTEMA_ACTUAL.md`, `ARQUITECTURA.md`, `API.md`, `DECISIONES.md`, `ROADMAP.md`, `ESTADO.md`) existe y refleja el código real |
| 2 | Resolver decisiones pendientes bloqueantes | **COMPLETADO** | 1 | Usuario respondió PEND-A→DEC-002, PEND-B→DEC-003, PEND-C→DEC-004, PEND-H→DEC-005 (ver `DECISIONES.md`) |
| 3 | Seguridad inmediata (código) | **COMPLETADO** | 2 (DEC-005) | `backup_db.sh` ya no tiene el password hardcodeado, lo toma de `PGPASSWORD` y falla si no está seteada. **Falta acción del usuario sobre infraestructura real**: rotar el password filtrado en el servidor y exportar el nuevo donde corra el cron — ver DEC-005 |
| 4 | Extender DRF a los dominios de negocio | **COMPLETADO** | 2 (DEC-003) | `articulo`, `cliente`, `promocion`, `cuentacorriente`, `venta`, `caja` — los 6 dominios con ViewSets/serializers DRF, verificados con smoke tests. De paso: DEC-008 (bug de `MovimientoCaja` atado a la caja equivocada, corregido a nivel modelo). Movimientos "varios" de caja (`Sueldo`/`Adelanto`/etc.) y PEND-J (anular venta cobrada) quedaron fuera, no eran centrales para venta/cobro — ver `API.md` |
| 5 | OAuth2 para cliente SPA | **COMPLETADO** | 2 (DEC-002) | `Application` OAuth2 pública (authorization-code + PKCE) creada vía management command idempotente; flujo completo verificado con smoke test real (authorize→token→endpoint protegido→refresh con rotación→revoke, más los casos negativos de PKCE); documentado en `API.md`. Bug de config encontrado y corregido (`testing.py`). Pendiente confirmar con el usuario dominio/subdominio del frontend para CORS antes de producción |
| 6 | Base del frontend React | **COMPLETADO** | 4, 5 | Proyecto Vite+TS en `frontend/`, verificado en un navegador real por el usuario: `npm install`/`npm run dev` levantan sin errores, login OAuth2 PKCE completo (con el fix de `LOGIN_URL`, DEC-002), `InicioPage` muestra el perfil del usuario autenticado vía `GET /api/v1/usuario/me/` y permite cerrar sesión |
| 7 | Autenticación en React | **COMPLETADO** | 6 | Ya incluido en la etapa 6: login PKCE, refresh automático, logout, manejo de 401 |
| 8 | Layout y navegación general | **COMPLETADO** | 7 | `AppLayout` (Mantine `AppShell`) con navegación a Artículos/Clientes/Ventas, rutas protegidas |
| 9 | Gestión de artículos/clientes en React | **COMPLETADO** | 8 | `ArticulosPage`/`ArticuloFormModal` (alta/edición sólo staff, vía `perfil.is_staff`), `ClientesPage`/`ClienteFormModal` (búsqueda/creación de Persona integrada). Verificado con `npm run build` real |
| 10 | Venta (punto de venta) en React | **COMPLETADO** | 9 | `VentaNuevaPage`: carrito en memoria, búsqueda de cliente/artículo/empleado, lectura de balanza (`localhost:4700`, DEC-006), previsualización de precio en vivo (`POST /venta/previsualizar/`, nuevo), confirmación vía `POST /venta/crear/` |
| 11 | Cobro en React | **COMPLETADO** | 10 | `CobroVentaPage`: cobro combinado efectivo/tarjeta/cta.cte/transferencia vía `POST /caja/cobrar-venta/` (ya corregía el bug de §15.12 desde que se construyó el endpoint, etapa 4) |
| 12 | Cuenta corriente en React | **COMPLETADO** | 9 | `CuentasCorrientesPage` (alta/edición sólo staff) + `CuentaCorrienteDetalleModal` (saldo, historial, alta de movimiento — cualquier autenticado, igual criterio que la API) |
| 13 | Caja en React | **COMPLETADO** | 11 | `CajaPage`: abrir/cerrar con resumen de cierre (ingresos/egresos), historial por sucursal. `TarjetasPage`/`PlanesTarjetaPage` para el catálogo que usa el cobro |
| 14b | Catálogo secundario en React | **COMPLETADO** (nuevo, no estaba en la lista original) | 9 | Categorías, unidades de medida, tipos de IVA, listas de precio, precios — CRUD completo, todos sólo-staff para escritura salvo lectura |
| 14c | Personal en React | **COMPLETADO** (nuevo) | 9 | Empleados (con búsqueda/creación de Persona integrada, igual patrón que clientes) y Sucursales |
| 14d | Promociones en React | **COMPLETADO** (nuevo) | 9 | Promociones (días de vigencia, artículos con precio fijo anidados) y Descuentos |
| 14 | Stock/Inventario | PENDIENTE | 2 (PEND-C, PEND-D) | Depende 100% de la decisión: reactivar Admin legacy, rediseñar, o dejar fuera de alcance |
| 15 | Reportes/exportaciones en React | PENDIENTE | 10–13 | Los que hoy son exports de Excel (`django-import-export`) y no se resuelvan mejor quedándose en Admin |
| 16 | Impresión de tickets/comprobantes | **COMPLETADO** | 11, 13 | Se optó por PDF vía la API existente (`util/pdf.py`, WeasyPrint) en vez de `window.print()` sobre HTML: `VentaViewSet.imprimir` (nuevo, `GET /api/v1/venta/<numero_ticket>/imprimir/`, mismo template `ticket_venta.html`) autenticado con el Bearer token de la API — la vista legacy (`venta.views.imprimir_ticket`) exigía sesión de Django, no alcanzable desde el SPA, por eso no imprimía nada. Frontend: botón "Imprimir" en `VentasListPage`/`CobroVentaPage` que pide el PDF y lo abre en una pestaña nueva (el visor del navegador da el diálogo de impresión) |
| 17 | Permisos finos en React | PENDIENTE | 7 | Traducir los chequeos ad-hoc de sucursal/superuser (§7, §11) a un modelo consistente expuesto por la API |
| 18 | Testing | PENDIENTE | continuo | Resolver primero que `pytest.ini` apunta a una carpeta `tests/` inexistente (§13); definir estrategia (pytest-django para backend, algo tipo Vitest/RTL para frontend) |
| 19 | Limpieza progresiva de código legacy | PENDIENTE | cada etapa de React equivalente completada | Sólo retirar templates/JS/vistas de un dominio cuando su reemplazo en React esté validado en uso real |
| 20 | Despliegue | EN CURSO | continuo | Dockerfile multi-stage (build de React + Django, mismo dominio, DEC-009) y catch-all en `project/urls.py` ya hechos — falta correrlo en el servidor real (crear la `Application` OAuth2 de prod, setear las variables en Dokploy, verificar en el dominio) |

## Próxima etapa concreta

**Etapas 1 a 13 (más 14b/14c/14d, catálogo/personal/promociones) COMPLETADAS.** Backend (6
dominios en DRF + OAuth2 PKCE) y frontend completo (base, auth, layout, y CRUD de los 13
dominios: artículos, categorías, unidades de medida, tipos de IVA, listas de precio, precios,
clientes, empleados, sucursales, promociones, descuentos, tarjetas, planes de tarjeta, caja,
cuenta corriente, venta, cobro) funcionando y verificados. Detalle completo en `API.md` /
`ARQUITECTURA.md`; todas las decisiones tomadas en el camino (DEC-001 a DEC-009) en
`DECISIONES.md`.

**Cómo se verificó cada cosa** (para que quien retome sepa qué nivel de confianza tiene cada
parte):
- Backend: smoke tests funcionales reales (`rest_framework.test.APIClient` contra una base
  sqlite en memoria) en cada dominio, incluyendo los casos negativos (permisos, validaciones de
  negocio, intentos de manipular datos desde el cliente).
- Frontend: `npx tsc -b` + `npm run build` reales (no sólo escrito a mano) en cada tanda de
  pantallas nuevas, más un smoke test de backend que reproduce **exactamente** los payloads que
  manda cada formulario nuevo — así se encontraron y corrigieron, antes de que el usuario los
  viera, dos bugs reales de "campo nullable que no acepta string vacío, sólo `null`"
  (`TarjetaDeCredito.banco`, ya generalizado al resto de los formularios).
- Interactivo en navegador: sólo el login (etapa 6) y las pantallas de artículos/clientes/venta/
  cobro (confirmado por el usuario: "quedó perfecto"). **El resto de las pantallas nuevas de esta
  tanda (catálogo secundario, empleados, sucursales, promociones, descuentos, tarjetas, planes,
  caja, cuenta corriente) todavía no se probaron a mano** — sólo compilación + smoke test de
  payloads. Es razonablemente probable que aparezca algún detalle de UX que sólo el uso real
  revela (mismo patrón que ya pasó dos veces: `LOGIN_URL` y `telefonos`).

**Siguiente**: el usuario prueba en el navegador las pantallas nuevas y reporta qué encuentra.
Después de eso, lo que queda del roadmap original:
- Etapa 14 (Stock/Inventario) — sigue bloqueada por DEC-004 (`inventario` desactivado a
  propósito, PEND-C/D).
- Etapa 15 (Reportes/exportaciones), 17 (Permisos finos), 18 (Testing — falta resolver que
  `pytest.ini` apunta a una carpeta `tests/` inexistente), 19 (Limpieza de código legacy), 20
  (Despliegue) — ninguna arrancada todavía. Etapa 16 (Impresión de tickets) ya completada.
- PEND-J (anular venta cobrada) sigue pendiente, ahora con `caja`/`cuentacorriente` ya
  construidos en el frontend además del backend, por si se quiere retomar.

Con "Continuá con la siguiente etapa" se retoma leyendo este archivo + `ESTADO.md`.
