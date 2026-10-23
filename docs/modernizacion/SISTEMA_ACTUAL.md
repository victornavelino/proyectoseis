# Sistema actual — Relevamiento técnico y funcional

> Generado en la etapa 1 (Auditoría) del proceso de modernización. Refleja el estado del código
> en la rama `feature-dokploy` al 2026-08-30. Ver `ESTADO.md` para el estado vivo del proyecto y
> `ARQUITECTURA.md` / `ROADMAP.md` para lo que viene después.

## 1. Visión general

Sistema de gestión para una carnicería con múltiples sucursales ("Carnicería Virgen del Valle").
Django 4.2 LTS + Django Admin como interfaz operativa actual (punto de venta, cobro, caja,
cuentas corrientes, inventario, promociones). No hay frontend SPA todavía: todo se opera sobre
Django Admin con vistas/templates/JS propios superpuestos.

Apps Django (`project/apps/`), en orden de `PROJECT_APPS` (`project/settings/base.py`):

| App | Responsabilidad | Notas |
|---|---|---|
| `usuario` | Usuario custom (`AUTH_USER_MODEL`), API de registro/perfil | Ya tiene `api.py`/`serializers.py` (DRF) |
| `core` | Mixins/filtros genéricos para el Admin (`Publicado`, `ControlsAdminMixin`) | Infraestructura transversal |
| `persona` | Datos personales compartidos (clientes y empleados apuntan acá) | Ya tiene `api.py`/`serializers.py` (DRF) |
| `util` | `Telefono` (genérico), PDF (WeasyPrint), paginación DRF | |
| `empleado` | `Sucursal`, `Empleado` | Sucursal es el eje de casi todo el negocio |
| `articulo` | Productos, categorías (árbol MPTT), precios por sucursal/lista | |
| `cliente` | Cliente (liga `Persona` + condición IVA + lista de precio) | |
| `promocion` | Promociones y descuentos automáticos | |
| `venta` | Venta, detalle de venta, cierre de ventas | El corazón del sistema |
| `caja` | Apertura/cierre de caja, medios de pago, tarjetas | |
| `inventario` | Inventario físico y movimientos internos entre sucursales | **Admin deshabilitado, ver §7** |
| `cuentacorriente` | Cuenta corriente de clientes | |

## 2. Modelos y relaciones clave

```
Persona ──< Empleado (cuil)
   │      └─< Cliente (condicion_iva, lista_precio)
   │
Usuario(AbstractUser) ──> Empleado, Sucursal

Articulo ──> Categoria (MPTT, tipo_iva) ──> UnidadMedida
Articulo ──< Precio >── Sucursal, ListaPrecio   (unique articulo+sucursal+lista_precio)

Venta ──> Empleado, Sucursal, Cliente, Usuario, CierreVentas
Venta ──< VentaArticulo >── Articulo   (snapshot de nombre/código/precio al momento de vender)

Caja ──> Sucursal, Usuario
MovimientoCaja (tabla base, herencia multi-tabla) ──> Caja, Usuario, tipo(ingreso/egreso)
   ├─ CobroVenta(venta)      ├─ Sueldo(empleado)      ├─ Adelanto(empleado)
   ├─ Ingreso(tipo_ingreso)  ├─ RetiroEfectivo         └─ Gasto(tipo_gasto)
CuponPagoTarjeta ──> Cliente, PlanTarjetaDeCredito(→TarjetaDeCredito), Venta
PagoTransferencia ──> Venta

CuentaCorriente ──> Cliente
MovimientoCuentaCorriente ──> CuentaCorriente, Usuario, Venta?, tipo(D/C)

Promocion ──> Sucursal, DiasSemana; ──< PromocionArticulo >── Articulo
Descuento (CUMPLEAÑOS, EMPLEADOS — por nombre, no por FK)

Inventario ──> Sucursal, TipoInventario; ──< ArticuloInventario (conteo físico periódico)
MovimientoInterno ──> Sucursal origen/destino, Usuario emisor/receptor
   ──< MovimientoInternoArticulo >── Articulo
```

`MovimientoCaja` usa **herencia multi-tabla** de Django (`InheritanceManager` de
`django-model-utils`) — `obj.clase()` hace `try/except` sobre cada tabla hija para saber de qué
subtipo es un movimiento. Tenerlo en cuenta al diseñar los serializers DRF (no es un simple CRUD).

`Articulo` y `Precio` heredan de `SoftDeleteObject` (`django-softdelete`): el borrado es lógico,
no físico. `Categoria` es un árbol `django-mptt`.

## 3. Flujo de Venta (punto de venta / mostrador)

Pantalla principal: template Admin sobrescrito `admin/venta/venta/add.html` (~1000 líneas, con
JS embebido) — **no es una vista Django Admin estándar**, es una consola de venta hecha a medida
sobre el `add_view` del admin de `Venta`.

Pasos (según `venta/views.py` + `venta/utils.py` + el JS del template):

1. El operador identifica **cliente** (`get_clientes`) y **empleado** (`get_empleados`),
   busca **artículos** por nombre/código (`get_articulos`, `get_articulos_todos`).
2. Al elegir artículo + cliente, `get_valores` (view) decide el precio a mostrar:
   - Si es cumpleaños del cliente (`cumpleanio()`) y existe `Descuento(nombre='CUMPLEAÑOS')` con
     `valor>0` → aplica ese % sobre el precio de lista.
   - Si no, si el cliente es empleado (`es_empleado()`) y existe `Descuento(nombre='EMPLEADOS')`
     con `valor>0` → aplica ese %.
   - Si no, y la lista de precios del cliente contiene `'COMUN'` → busca si el artículo entra en
     alguna `Promocion` activa de la sucursal (por prioridad); si no matchea, precio de lista.
   - Si no ('lista no común', cliente con lista propia) → precio de esa lista, sin promo.
3. **Si el artículo `es_por_peso`**, el navegador pide el peso a una **balanza vía un servicio
   HTTP local en `http://localhost:4700`** (`jQuery.get('http://localhost:4700', ...)`, en
   `admin/venta/venta/add.html:612` y `admin/venta/venta_articulo/change_form.html:14`). Esto es
   una **integración de hardware fuera de Django**, invisible si sólo se lee el backend. Ver
   riesgos (§8) — hay que decidir qué hacer con esto en React.
4. `guardar_venta` (POST, `venta/views.py`) exige **caja abierta** en la sucursal del usuario;
   si no, rechaza la venta. Delega el cálculo real a `guardar_venta_cliente_articulos()`
   (`venta/utils.py`), que **recalcula el precio en servidor** repitiendo la misma cascada
   cumpleaños→empleado→promo→lista — **excepto** en la rama de descuento (cumpleaños/empleado),
   donde usa el `precio_unitario` que **vino del frontend sin validar** (`calcular_total_con_descuento`).
   Ver riesgo de integridad en §8.
5. Se crea `Venta` (monto ya calculado) y un `VentaArticulo` por línea (snapshot de nombre,
   código y precios). `cobrada=False` hasta que se cobra.
6. **Cobro** (`caja/views.cobrar_ticket`, disparado desde `admin/venta/cobro_venta/cobrar_venta.html`,
   1289 líneas): admite pago combinado (parcial) en efectivo, tarjeta, cuenta corriente y
   transferencia en la misma venta. Exige caja abierta y `caja.fecha_inicio <= venta.fecha`.
   Cada medio de pago crea su propio registro (`CobroVenta`, `CuponPagoTarjeta`,
   `MovimientoCuentaCorriente` vía `guardar_pago_ccorriente`, `PagoTransferencia`) y al final
   marca `venta.cobrada = True` — **incluso si alguno de los pagos falló** (hay un comentario del
   propio equipo en el código: `# REVISAR BIEN PORQUE LO MISMO LA SETEA COMO COBRADA...`).
7. **Anulación** (`VentaAdmin.anular_venta`, admin action, sólo 1 venta a la vez): si la venta
   estaba cobrada, intenta borrar el `CobroVenta`/`CuponPagoTarjeta` asociados (el código usa
   `.delete` sin paréntesis — **no ejecuta el borrado real**, ver §8) y no toca stock ni cuenta
   corriente. Sólo bloquea si la caja de ese cobro ya está cerrada.
8. **Impresión de ticket**: `imprimir_ticket` / acción de admin `Imprimir Ticket` renderizan
   `admin/venta/ticket_venta.html` a PDF con WeasyPrint (`util/pdf.py`) o vía un `<iframe>` +
   `window.print()` del navegador (impresión térmica es responsabilidad del navegador/SO, no hay
   integración con impresora fiscal/térmica en el backend).
9. **Cierre de ventas** (`CierreVentas`, admin **comentado por completo** en `venta/admin.py`,
   ver §7) agrupaba tickets por rango y calculaba importes por categoría (asados, blandos,
   eventuales, empleados) vía funciones de `venta/utils.py` que siguen existiendo y se usan desde
   `caja` para el cierre de caja.

No existe un paso de "carrito" persistente en servidor: el JS arma el array `articulos` en
memoria del navegador y lo manda entero a `guardar_venta` al confirmar.

## 4. Caja

- **Apertura**: `CajaAdmin.save_model` — sólo una caja abierta por sucursal a la vez; toma
  `caja_inicial` = `caja_final` de la última caja cerrada de la sucursal (o 0).
- **Movimientos** (`MovimientoCaja` y subtipos): ingresos varios, sueldos, adelantos, retiros de
  efectivo, gastos, cobros de venta. `MovimientoCaja.clean()` fuerza que la caja esté abierta y el
  importe sea > 0; el modelo se autoasigna a `Caja.objects.latest('id')` (**no filtra por
  sucursal** — con más de una sucursal con cajas abiertas simultáneas esto podría atar el
  movimiento a la caja equivocada, ver §8).
- **Cierre** (`cerrar_caja` view + acción de admin `CajaAdmin.cerrar_caja`): exige que no haya
  ventas sin cobrar (`Venta.objects.filter(cobrada=False)`, **sin filtrar por sucursal**),
  calcula `caja_final = caja_inicial + Σingresos − Σegresos` y marca todos los movimientos como
  `cerrado=True`. Suma aparte cobranzas de cuenta corriente (`MovimientoCuentaCorriente` tipo
  `CREDITO`) y compras con tarjeta (`CuponPagoTarjeta.importe_con_recargo`).
- **Impresión de cierre**: `admin/caja/ticket_cierre_caja.html` vía WeasyPrint o HTML directo.
- **Tarjetas de crédito**: `TarjetaDeCredito` → `PlanTarjetaDeCredito` (interés, "es vale") →
  `CuponPagoTarjeta` (importe, recargo, importe_con_recargo, nº cupón/lote). El **recargo y el
  importe con recargo los calcula el frontend y el backend los persiste tal cual** — no hay
  recálculo server-side (§8).

## 5. Cuenta corriente

- `CuentaCorriente` por cliente, con `tope` (límite) que **no se valida en ningún lado** al
  registrar un débito — se puede superar el tope sin aviso (§8).
- `MovimientoCuentaCorriente`: `D` (débito, consumo) / `C` (crédito, pago). Saldo =
  `Σdébitos − Σcréditos` (`calcular_saldo_cc`).
- Pagar con cuenta corriente en una venta = crear un `D` (`guardar_pago_ccorriente`, llamado
  desde `caja.cobrar_ticket`). Cobrar cuenta corriente fuera de una venta = `cobrar_ccorriente`
  (crea un `C` y además un `Ingreso` de caja tipo "Pago de cuenta corriente" — mueve caja).
- Endpoint propio `admin/cuentacorriente/<cliente_id>` (`get_cc_cliente`) para consultar saldo
  desde el JS del punto de venta.

## 6. Artículos, precios y promociones

- `Precio` es por combinación (`articulo`, `sucursal`, `lista_precio`) — **no existe un precio
  único global**; cada sucursal/lista tiene el suyo.
- `ListaPrecio` en el modelo sólo tiene `nombre`. Sin embargo `articulo/views.get_listas_precio_sucursal`
  filtra `ListaPrecio.objects.filter(sucursal__id=..., habilitada=True)` — **esos campos no
  existen en el modelo actual**; ese endpoint está roto o el modelo quedó desactualizado
  respecto al código que lo usa (§7).
- **Copiar precios entre sucursales** (`copiar_precios_sucursal*`, admin/articulo/precio/*):
  duplica/actualiza `Articulo` + `Precio` de una sucursal a otra (por lista completa o
  específica).
- **Promociones**: vigencia por fecha (`fecha_inicio`/`fecha_fin`) + días de la semana
  (`DiasSemana`) + `prioridad` única por sucursal. Dos modos: `porcentaje_todos` (% sobre todos
  los artículos de la lista Común) o `es_por_precio` (precio fijo por artículo vía
  `PromocionArticulo`). Sólo se evalúan promos para clientes con lista `'COMUN'` (matching por
  substring del nombre, no por FK/flag — frágil).
- **Descuentos especiales** `CUMPLEAÑOS` y `EMPLEADOS`: identificados **por nombre exacto**
  (`Descuento.objects.get(nombre='CUMPLEAÑOS')`), no por una constante/flag — renombrar el
  registro en el Admin rompe silenciosamente el descuento.
- **Copiar promociones entre sucursales**: análogo a copiar precios (`promocion/utils.py`).

## 7. Django Admin: qué es estándar, qué está personalizado, qué está roto

| App.Modelo | Estado | Detalle |
|---|---|---|
| `venta.Venta` | Muy personalizado | Templates propios (`add.html`, `change_list.html`), acciones custom (`anular_venta`, `imprimir_ticket`), exportación Excel (`django-import-export`), inlines de `VentaArticulo` |
| `venta.VentaArticulo` | Personalizado (solo lectura) | Admin de solo consulta/exportación, sin alta/baja |
| `venta.CierreVentas` | **Deshabilitado** | Todo el `ModelAdmin` está comentado (triple-quoted string) en `venta/admin.py`; el modelo existe y las funciones de cálculo (`venta/utils.py`) se siguen usando desde `caja`, pero no hay UI para generarlo en Admin |
| `caja.Caja` | Muy personalizado | Control de una caja abierta por sucursal, acciones `cerrar_caja`/`imprimir_cierre_caja`/`exportar_movimientos`, permisos de borrado condicionados a superuser |
| `caja.CuponPagoTarjeta` | Personalizado | `changeform` propio |
| `inventario.*` (Inventario, TipoInventario, ArticuloInventario, MovimientoInterno, MovimientoInternoArticulo) | **Admin completamente deshabilitado** | Todo `inventario/admin.py` (98 líneas) está dentro de un docstring `"""..."""` nunca cerrado hasta el final del archivo — **ningún modelo de esta app está registrado en Django Admin hoy**. Las views (`recepcionar_movimiento_ingreso`), forms, templates (`recepcion_movimiento.html`, `add.html`, `change_form.html`) y URLs siguen existiendo, apuntando a un Admin que no se puede abrir. Confirmar con el usuario si es intencional (¿se gestiona por otro medio?) antes de decidir qué migrar. |
| `articulo.*` | Estándar + 1 personalizado | CRUD estándar salvo `Precio` (vista propia "copiar precios entre sucursales", fuera del Admin, linkeada como flujo aparte) |
| `promocion.Promocion` | Personalizado | Template `promocion_changelist.html` con botón "copiar promociones", form propio `PromocionForm` (no leído en detalle todavía) |
| `cliente.Cliente` | Estándar + exportación | `ExportMixin` con `ClienteResource` (código con bugs cosméticos: `dehydrate_full_title` referencia campos que no existen, es código muerto/copy-paste) |
| `persona.Persona` | Casi estándar | `save_model` asigna `obj.referente = request.user`, pero el modelo `Persona` **no tiene campo `referente`** — esto tira `AttributeError` si algún día se ejecuta ese admin save (posible bug latente, revisar si `PersonaAdmin` se usa en la práctica) |
| `empleado.*`, `usuario.Usuario` | Estándar | `UsuarioAdmin` extiende `UserAdmin` agregando `sucursal`/`empleado` |
| `caja.Sueldo/Adelanto/Ingreso/RetiroEfectivo/Gasto/TarjetaDeCredito/PlanTarjetaDeCredito` | No confirmado en detalle | Quedó fuera del muestreo profundo de esta primera auditoría; revisar admin.py completo antes de tocar `caja` |

**Permisos**: no hay un modelo de "Rol" propio. Se usa `is_superuser` (chequeado a mano en varias
`has_*_permission`/`save_model` de `caja` e `inventario`) + grupos/permisos estándar de Django
(`UsuarioAdmin` expone `groups`/`user_permissions`). No hay permisos por sucursal más allá de
filtrar querysets por `request.user.sucursal`.

## 8. JavaScript / AJAX (fuera de templates de terceros)

Todo el JS de negocio vive **inline dentro de los templates de Admin sobrescritos**
(`project/templates/admin/**/*.html`), no en `project/assets/js/` (esa carpeta sólo tiene
librerías de terceros: jQuery, Bootstrap modal forms, SweetAlert, Popper, jQuery UI).
`project/assets/promocion/formset_handlers.js` existe pero **está 100% comentado** (código
muerto, no se ejecuta).

Templates con lógica de negocio en JS (`jQuery.ajax` contando llamadas por archivo):

| Template | Líneas | Llamadas AJAX | Qué hace |
|---|---|---|---|
| `admin/venta/venta/add.html` | ~998 | 7 (+2 `localhost:4700`) | Punto de venta completo: buscar artículo/cliente/empleado, calcular precio con descuentos, leer peso de balanza, armar carrito en memoria, `guardar_venta`, imprimir ticket vía iframe |
| `admin/venta/cobro_venta/cobrar_venta.html` | ~1289 | 5 | Pantalla de cobro combinado (efectivo/tarjeta/cta.cte/transferencia), llama `cobrar_ticket` |
| `admin/venta/cobro_venta/add_cobro_venta.html` | ~517 | 4 | Variante/paso del flujo de cobro |
| `admin/venta/venta_articulo/change_form.html` | ~46 | 1 (`localhost:4700`) | Autocompletar peso desde balanza en el inline de artículo |
| `admin/caja/cierre_caja.html` | ~207 | 1 | Cálculo/confirmación de cierre de caja |
| `admin/caja/cuponpagotarjeta_changeform.html` | ~107 | 1 | Cálculo de recargo de tarjeta en el formulario |
| `admin/promocion/copiar_promo.html` | ~333 | 2 | UI de copiar promociones entre sucursales |
| `admin/articulo/precio/copiar_precios.html` | ~325 | 2 | UI de copiar precios entre sucursales |
| `admin/inventario/movimientointerno/change_form.html`, `recepcion_movimiento.html` | ~51 / ~159 | 1 | Recepción de mercadería entre sucursales (Admin actualmente deshabilitado, ver §7) |

**Integración de hardware fuera de Django**: `http://localhost:4700` es un servicio HTTP local
(probablemente un puente serie↔HTTP para una balanza electrónica) que el **navegador** del punto
de venta llama directamente por `jQuery.get`, sin pasar por Django. No hay rastro de ese servicio
en este repositorio — es external al proyecto Django. **Hay que preguntarle al usuario cómo está
implementado ese servicio** (¿un programa aparte en la PC del mostrador? ¿queda igual con React?)
antes de diseñar el flujo de pesaje en el nuevo frontend.

## 9. Endpoints/vistas existentes (no-DRF, consumidos por el propio Admin)

Definidos en `project/urls.py`, casi todos bajo el prefijo `/admin/...` aunque no son vistas de
Django Admin sino vistas de función propias que conviven con el Admin en la misma URL:

```
/admin/venta/guardar_venta/                                  POST  guardar_venta
/admin/venta/articulo/<codigo>/<cliente_pk>                  GET   get_valores
/admin/venta/articulos/<texto>                                GET   get_articulos
/admin/venta/articulos_todos/                                 GET   get_articulos_todos
/admin/venta/clientes/                                        GET   get_clientes
/admin/venta/empleados/                                       GET   get_empleados
/admin/venta/clientes/<pk>                                    GET   verificar_cumpleanios
/admin/venta/clientes/get_listaprecio/<pk>                    GET   get_listaprecio
/admin/caja/tarjetas_de_credito/                               GET   get_tarjetas
/admin/caja/planes_tarjeta/<pk_tarjeta>                       GET   planes_tarjeta
/admin/caja/plan_tarjeta/<id_plan>                            GET   plan_tarjeta
/admin/venta/venta/nuevo_pago_efectivo/                       GET   nuevo_pago_efectivo (render fragmento)
/admin/venta/venta/listado_de_ventas/                         GET   listar_ventas / get_ventas (misma URL, 2 nombres)
/admin/venta/venta/cobrar_venta/<numero_ticket>                GET   cobrar_venta (render)
/admin/venta/venta/cobrar_venta/                               POST  cobrar_ticket
/admin/venta/venta/exportar_ventas                             GET   exportar_ventas (xls)
/admin/venta/venta/<numero_ticket>                             GET   imprimir_ticket (PDF)
/admin/promocion/promocion/copiar_promociones/                 GET   copiar_promociones (render)
/admin/promocion/promocion/copiar_promos/                      POST  copiar_promos
/admin/promocion/promocion/get_promociones_sucursal/<pk>       GET   get_promociones_sucursal
/admin/articulo/precio/copiar_precios/                         GET   copiar_precios (render)
/admin/articulo/precio/copiar_precios_proceso/                 POST  copiar_precios_proceso
/admin/articulo/precio/listas_precio/<pk_sucursal>              GET   get_listas_precio_sucursal (¡ver bug §6!)
/admin/precio/precio_articulo/<id_articulo>                    GET   get_precio_articulo
/admin/inventario/movimientointerno/<numero_lote>               PUT   recepcionar_movimiento_ingreso
/admin/cuentacorriente/<cliente_id>                             GET   get_cc_cliente
/admin/caja/caja/cerrar_caja/                                   POST  cerrar_caja
/admin/caja/imprimir_cierre_caja/<id_caja>                      GET   imprimir_cierre_caja (HTML)
/admin/caja/imprimir/<id_caja>                                  GET   imprimir_cierre_caja_pdf (PDF)
```

Todas devuelven JSON armado a mano (`json.dumps`) o HTML parcial, ninguna usa DRF. Casi todas
sólo chequean `request.user.is_authenticated` (sesión), no hay control de permisos granular por
acción.

## 10. API REST / autenticación ya existentes (punto de partida real para DRF+OAuth2)

Esto **ya está instalado y funcionando**, no hay que agregarlo desde cero — hay que extenderlo:

- **DRF** (`djangorestframework`), con `REST_FRAMEWORK` en `base.py`. *(Nota: al momento de esta
  auditoría el renderer/parser por defecto era `djangorestframework-jsonapi`, formato JSON:API.
  Desde DEC-003 (`DECISIONES.md`) ya se migró a JSON plano — este párrafo describe el estado
  encontrado en la auditoría, ver `API.md` para el estado actual.)*
- **`django-oauth-toolkit`** (`oauth2_provider`) montado en `/oauth2/` (`base_urlpatterns`, o sea
  sólo los endpoints de token/revoke, no el panel de admin de aplicaciones).
- **`drf-social-oauth2`** montado en `/auth/` y como backend de autenticación adicional
  (`AUTHENTICATION_BACKENDS`), pensado originalmente para login social — confirmar si el proyecto
  lo usa realmente o es vestigial.
- **Router DRF** (`project/router.py`) con 2 recursos: `api/v1/persona/` (`PersonaViewSet`:
  list/create/retrieve + acción `obtener_persona` por documento) y `api/v1/usuario/`
  (`UsuarioViewSet`: retrieve/update del usuario autenticado + acción
  `cambiar-clave-secreta`).
- **`api/v1/usuario/registro/`**: alta pública de usuario + persona asociada
  (`RegistroUsuarioAPIView`, `AllowAny`), con validación de contraseña Django y creación
  atómica de `Persona` si no existía por documento.
- **Paginación** propia (`util.paginations.LargePagination`, hasta 300 por página).
- Cuando `ACTIVAR_HERRAMIENTAS_DEBUGGING=True`: se suma `BrowsableAPIRenderer` y
  `SessionAuthentication` a DRF, más Debug Toolbar/`django-extensions`.

**Conclusión para la etapa 5 (OAuth2)**: no hace falta "agregar" OAuth2, hace falta **decidir el
flujo para React** (Authorization Code + PKCE es lo recomendado para un SPA), crear la
`Application` de OAuth2 correspondiente, y **extender el router** con ViewSets para el resto de
los modelos de negocio (Venta, Caja, CuentaCorriente, Articulo, Promocion, etc.), que hoy no
tienen ninguna representación DRF.

## 11. Autenticación / seguridad — estado actual (ampliar en etapa de seguridad)

- Usuario custom `usuario.Usuario` (`AbstractUser` + `empleado` + `sucursal`), configurado como
  `AUTH_USER_MODEL`.
- Login actual: sesión de Django estándar contra el Admin (`AUTHENTICATION_BACKENDS` incluye
  `ModelBackend` + el backend de `drf-social-oauth2`).
- `CORS_ALLOW_ALL_ORIGINS = True` en `base.py` — abierto a cualquier origen. Aceptable
  temporalmente en desarrollo, **hay que acotarlo** al dominio real de React antes de producción.
- `CSRF_TRUSTED_ORIGINS` y `SECURE_PROXY_SSL_HEADER` ya se configuraron correctamente para
  Dokploy/Traefik (ver commits recientes) — no tocar sin entender el fix.
- **Credencial filtrada en el repo**: `backup_db.sh` (raíz del proyecto, trackeado en git,
  commit `e87d3a5`) contiene `export PGPASSWORD="vallE.852"` **en texto plano**. Esto es un
  hallazgo de seguridad real, no hipotético — ver `ESTADO.md` § Problemas conocidos para la
  acción recomendada.
- Casi todas las vistas custom sólo controlan `is_authenticated`, no permisos por acción; el
  control de "editar sólo tu sucursal" se hace ad-hoc en cada `get_queryset`/`save_model`, no hay
  una capa central.

## 12. PDF / impresión / reportes

- `util/pdf.py` — `render_pdf_response()` con **WeasyPrint** (reemplazo reciente de
  `wkhtmltopdf`, ver commit `2c91c70`). Usado para: ticket de venta, cierre de caja.
- `django-import-export` para exportar a Excel: `Venta`, `VentaArticulo`, `Cliente`,
  `MovimientoInterno` (admin deshabilitado igual que el resto de `inventario`).
- Impresión física del ticket: `window.print()` sobre un `<iframe>` — depende de la impresora
  configurada en el navegador/SO del puesto, no hay integración con impresora fiscal.

## 13. Testing

- `pytest.ini`: `DJANGO_SETTINGS_MODULE=project.settings.testing`, `testpaths = tests`,
  `--nomigrations`. **No existe una carpeta `tests/` en la raíz** — con esta configuración
  `pytest` no recolecta nada. Cada app tiene un `tests.py` casi vacío (3 líneas, boilerplate de
  `startapp`), o sea que **hoy no hay cobertura de tests real**, ni ejecutable con `pytest` tal
  como está configurado ni con contenido significativo en los `tests.py` de Django.
- Settings de testing usa SQLite en memoria; deja comentadas las variables
  `OAUTH2_PROVIDER_*_MODEL` (por si se necesitan swappear en el futuro).

## 14. Funcionalidades relevadas que **no** están en el sistema

Buscadas explícitamente porque las menciona la lista orientativa de `especificaciones.md` y no
aparecieron en ningún lado del código (`grep` sin resultados fuera de nombres genéricos):

- **Compras / proveedores**: no existe un modelo `Proveedor` ni `Compra`. El "ingreso" de
  mercadería se modela sólo como `MovimientoInterno` tipo `Ingreso`/`Egreso` **entre sucursales**
  del mismo negocio, no como compra a terceros. Si la carnicería compra a proveedores externos y
  eso hoy se registra en otro sistema (o no se registra), confirmarlo con el usuario.
- **Stock/saldo de mercadería por artículo**: no hay un campo de cantidad/stock en `Articulo` ni
  una tabla de saldo acumulado. `inventario.Inventario` es un conteo físico manual periódico
  (mes/año) y `MovimientoInterno` sólo mueve mercadería entre sucursales — **ninguno de los dos
  se descuenta automáticamente al vender**. "Impacto en stock" de una venta, tal como lo pide la
  especificación, **no existe hoy**: es una funcionalidad a diseñar de cero si se quiere, no a
  migrar.
- Descuentos configurables más allá de `CUMPLEAÑOS`/`EMPLEADOS` (por nombre fijo): no hay un
  motor de reglas de descuento genérico.

## 15. Riesgos y deuda técnica a tener en cuenta antes de tocar cada área

Resumen de todo lo marcado arriba, para no perderlo de vista:

1. **Credencial de base de datos en texto plano commiteada** (`backup_db.sh`) — acción de
   seguridad inmediata recomendada (rotar password, reescribir historia o al menos sacar el
   archivo del tracking y pasar a variable de entorno).
2. **`inventario/admin.py` completamente deshabilitado** (dentro de un docstring) — confirmar con
   el usuario si es intencional antes de decidir si se migra o se rediseña de cero.
3. **`venta.CierreVentas` sin Admin** (comentado) pero sus funciones de cálculo se siguen usando
   desde `caja` — confirmar si el cierre de ventas por rango de tickets sigue siendo un flujo
   vigente o quedó reemplazado por el cierre de caja.
4. **Precio con descuento (cumpleaños/empleado) confía en el `precio_unitario` que manda el
   frontend** al guardar la venta (`calcular_total_con_descuento`) — violación del punto 15 de la
   especificación ("nunca confiar en cálculos críticos del frontend"); recalcular en servidor al
   migrar a la API.
5. **Recargo de tarjeta (`CuponPagoTarjeta.recargo`/`importe_con_recargo`) no se recalcula en
   servidor**, se persiste tal cual llega del frontend.
6. **`CuentaCorriente.tope` no se valida nunca** — se puede superar el límite sin aviso.
7. **`Venta.anular_venta` usa `.delete` sin paréntesis** (no ejecuta el borrado) al intentar
   borrar el cobro/cupón de una venta cobrada al anularla — probable bug, revisar comportamiento
   real antes de replicarlo.
8. **`MovimientoCaja.clean()` toma `Caja.objects.latest('id')` global**, no filtrado por
   sucursal — riesgo de atar movimientos a la caja de otra sucursal si hay más de una abierta a
   la vez.
9. **`cerrar_caja` (view) y `CajaAdmin.cerrar_caja` (acción) chequean ventas sin cobrar sin
   filtrar por sucursal** (`Venta.objects.filter(cobrada=False)`), pudiendo bloquear el cierre de
   una sucursal por ventas pendientes de otra.
10. **`get_listas_precio_sucursal` filtra campos (`sucursal`, `habilitada`) que no existen en
    `ListaPrecio`** — endpoint probablemente roto hoy; confirmar si se usa.
11. **`PersonaAdmin.save_model` asigna `obj.referente`**, campo inexistente en el modelo
    `Persona` — bug latente si se dispara ese código.
12. **`cobrar_ticket` marca `venta.cobrada = True` incluso si algún medio de pago falló**
    (comentario propio del equipo original en el código señalándolo).
13. **Integración de balanza vía `http://localhost:4700`** llamada directo desde el navegador —
    hay que decidir junto al usuario cómo se replica (o no) desde React.
14. **`pytest.ini` apunta a `tests/` que no existe** — no hay tests automatizados corriendo hoy;
    cualquier "ejecutar tests" de las etapas siguientes debe documentarse como no aplicable hasta
    que se cree la carpeta o se reconfigure.
15. **`AUTHENTICATION_BACKENDS`/`drf-social-oauth2`**: confirmar si el login social está
    realmente en uso o es vestigial antes de diseñar el flujo OAuth2 de React sobre él.
