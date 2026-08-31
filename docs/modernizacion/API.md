# API

Este documento se completa a medida que se crean/tocan endpoints DRF (etapa 4 en adelante).
Por ahora sólo registra lo que **ya existe** en el repo, relevado en la etapa de auditoría.

## Convención de formato

**JSON plano** (DEC-003, ver `DECISIONES.md`): `REST_FRAMEWORK` en
`project/settings/base.py` usa `rest_framework.renderers.JSONRenderer` /
`rest_framework.parsers.JSONParser` como parser/renderer por defecto. Las respuestas son objetos
JSON directos (`{"id": 1, "campo": "valor", ...}` o listas de esos objetos, paginadas con
`{"count", "next", "previous", "results"}` vía `util.paginations.LargePagination`), no el
formato JSON:API (`{"data": {"type", "attributes", ...}}`) que se usaba antes. Todo endpoint
nuevo sigue esta misma convención.

## Autenticación

- `DEFAULT_AUTHENTICATION_CLASSES`: `oauth2_provider.contrib.rest_framework.OAuth2Authentication`
  + `drf_social_oauth2.authentication.SocialAuthentication`.
- Con `ACTIVAR_HERRAMIENTAS_DEBUGGING=True` (dev) se suma `SessionAuthentication` +
  `BrowsableAPIRenderer`.
- Endpoints de token: `/oauth2/...` (`base_urlpatterns` de `django-oauth-toolkit` — sólo
  token/revoke, no el panel de gestión de `Application`s, que sigue en Django Admin en
  `/admin/oauth2_provider/`).
- `/auth/...` → `drf_social_oauth2.urls` (login social). **Probablemente vestigial**: al forzar
  un login con el `AUTHENTICATION_BACKENDS` actual, el backend
  `drf_social_oauth2.backends.DjangoOAuth2` falla al instanciarse (`social_django` no está en
  `INSTALLED_APPS`) — ver PEND-I en `DECISIONES.md`. No se tocó todavía.

## OAuth2 — Authorization Code + PKCE (DEC-002) — nuevo, etapa 5

Flujo pensado para el frontend React (sin `client_secret` embebido en el navegador — cliente
público). Endpoints (`django-oauth-toolkit`, montados en `/oauth2/`):

| Endpoint | Método | Uso |
|---|---|---|
| `/oauth2/authorize/` | GET (mostrar) / POST (confirmar) | Requiere sesión de Django ya iniciada; si no hay, redirige a `/login/?next=...` (ver abajo). Tras aceptar, redirige a la `redirect_uri` de la app con `?code=...&state=...` |
| `/oauth2/token/` | POST | `grant_type=authorization_code` (intercambia `code` + `code_verifier` por tokens) o `grant_type=refresh_token` |
| `/oauth2/revoke_token/` | POST | Invalida un token (`access_token` o `refresh_token`) |
| `/login/`, `/logout/` | GET/POST, POST | Login/logout genérico (`django.contrib.auth.views.LoginView`/`LogoutView`) — **no** `/admin/login/`, que exige `is_staff` y hubiera dejado afuera a cualquier vendedor no-staff. Ver DEC-002 en `DECISIONES.md` |

El navegador ve `/login/` como una pantalla intermedia dentro del mismo flujo: el frontend
redirige a `/oauth2/authorize/`, que redirige a `/login/?next=/oauth2/authorize/...` si no hay
sesión; tras loguearse, vuelve solo a `/oauth2/authorize/` y sigue el flujo normal. El frontend
no necesita saber nada de `/login/` explícitamente, es puro redirect del lado del servidor.

**Parámetros del flujo** (`response_type=code`, PKCE con `S256`):

```
GET /oauth2/authorize/?response_type=code&client_id=<client_id>
    &redirect_uri=<redirect_uri>&scope=read%20write&state=<random>
    &code_challenge=<base64url(sha256(code_verifier))>&code_challenge_method=S256
```

Tras el login + aprobación del usuario, redirige a `redirect_uri?code=...&state=...`. Luego:

```
POST /oauth2/token/
grant_type=authorization_code&code=<code>&redirect_uri=<redirect_uri>
&client_id=<client_id>&code_verifier=<code_verifier>
```

Respuesta: `{"access_token", "refresh_token", "expires_in": 1800, "token_type": "Bearer", "scope": "read write"}`.

**Configuración**:
- `OAUTH2_PROVIDER` (`project/settings/base.py`): `SCOPES` = `read`/`write`;
  `ACCESS_TOKEN_EXPIRE_SECONDS=1800` (30 min, configurable por env
  `OAUTH2_ACCESS_TOKEN_EXPIRE_SECONDS`); `REFRESH_TOKEN_EXPIRE_SECONDS=2592000` (30 días,
  configurable por `OAUTH2_REFRESH_TOKEN_EXPIRE_SECONDS`); `ROTATE_REFRESH_TOKEN=True` (cada
  refresh invalida el `refresh_token` anterior); `PKCE_REQUIRED=True` (rechaza cualquier
  `/authorize/` sin `code_challenge`).
- `OAUTH2_SPA_REDIRECT_URIS` (env, lista separada por coma): redirect URI(s) válidas del
  frontend.
- **Crear/actualizar la `Application`**: `python manage.py crear_aplicacion_oauth_spa` (lee
  `OAUTH2_SPA_REDIRECT_URIS`, o pasar `--redirect-uris <uri1> <uri2>`). Idempotente — correrlo
  de nuevo (ej. al cambiar de redirect URI de desarrollo a producción) no genera un `client_id`
  nuevo, actualiza la `Application` existente (identificada por `--nombre`, default
  `'Frontend SPA'`). El `client_id` generado se imprime por consola; no hay `client_secret`
  (cliente público). Gestión manual alternativa: Django Admin →
  `/admin/oauth2_provider/application/`.

**Almacenamiento de tokens en el cliente** (ver `ARQUITECTURA.md` § Autenticación):
`access_token` en memoria (no `localStorage`, mitiga XSS); `refresh_token` en cookie `httpOnly`
+ `secure` si el frontend se sirve del mismo dominio/subdominio que Django, o vía un pequeño
proxy de backend si no — **pendiente de confirmar con el usuario dónde va a vivir el frontend**
antes de definir esto en detalle y de acotar `CORS_ALLOWED_ORIGINS` (hoy
`CORS_ALLOW_ALL_ORIGINS=True`, sin acotar).

**Verificado con un smoke test funcional end-to-end real** (no simulado — HTTP real contra las
vistas de `django-oauth-toolkit`, login de sesión real para `/authorize/`, `Authorization:
Bearer` real contra un endpoint DRF protegido, no `force_authenticate`):
1. Comando `crear_aplicacion_oauth_spa` — idempotente, no duplica ni cambia el `client_id` al
   correrlo dos veces.
2. Flujo completo con PKCE correcto: `authorize` → `code` → `token` → `access_token`/
   `refresh_token` válidos, `expires_in` respeta el setting.
3. El `access_token` obtenido funciona contra un endpoint protegido real
   (`/api/v1/usuario/<pk>/`); sin token → 401.
4. `code_verifier` incorrecto en el intercambio → 400 `invalid_grant` (PKCE realmente
   verificado, no sólo aceptado).
5. `/authorize/` sin `code_challenge` → rechazado (`error=invalid_request`, "Code challenge
   required"), confirma `PKCE_REQUIRED=True` activo.
6. `refresh_token` → nuevos `access_token`/`refresh_token`; el `access_token` viejo se invalida
   y el `refresh_token` viejo deja de servir (rotación confirmada).
7. `revoke_token` → el token revocado deja de servir.

Al pasar, se encontró y corrigió un bug de configuración en `project/settings/testing.py` (ver
DEC-002 en `DECISIONES.md`) que hubiera roto este mismo flujo si se hubiera probado antes.

## Endpoints DRF existentes

### `POST /api/v1/usuario/registro/`
- Vista: `usuario.api.RegistroUsuarioAPIView` (`CreateAPIView`)
- Auth: `AllowAny` (público)
- Body: `username`, `password`, `password_2`, `email`, `first_name`, `last_name`, y
  opcionalmente `persona: {documento_identidad, nombre, apellido, ..., telefonos: [...]}`
- Efecto: crea (o reutiliza, si el documento ya existe) una `Persona`, y crea el `Usuario`
  asociado. Valida que `password == password_2` y las reglas estándar de Django
  (`validate_password`).
- Serializer: `usuario.serializers.RegistroUsuarioSerializer`.

### `GET/POST /api/v1/persona/`, `GET /api/v1/persona/{id}/`
- Vista: `persona.api.PersonaViewSet` (list, create, retrieve — no update/delete por ViewSet)
- Auth: `IsAuthenticated`
- Filtros: `DjangoFilterBackend` + `OrderingFilter` (sin `filterset_fields` explícitos vistos
  todavía — revisar al extender)
- Serializer: `persona.serializers.PersonaSerializer` (incluye `telefonos`, relación genérica)

### `POST /api/v1/persona/obtener_persona/`
- Acción custom del `PersonaViewSet`. Body: `{documento_identidad}`. Devuelve
  `{persona_id: <id o null>}` — usado para chequear si una persona ya existe por documento antes
  de crear otra.

### `GET/PATCH /api/v1/usuario/<cualquier-pk>/` (ej. `/me/` — el pk se ignora)
- Vista: `usuario.api.UsuarioViewSet` (`RetrieveModelMixin`, `UpdateModelMixin`)
- `get_object()` ignora el `pk` de la URL y devuelve `request.user` — es decir, este endpoint es
  "mi perfil", no un CRUD de usuarios en general. Convención del frontend: pedirlo como
  `/api/v1/usuario/me/`.
- Serializer: `usuario.serializers.UsuarioSerializer` (`username`, `email`, `first_name`,
  `last_name`, `is_staff`, `sucursal`, `sucursal_nombre`, `groups`). **`is_staff` y `sucursal`
  son de sólo lectura** (nuevo, etapa 7) — sin eso, cualquier usuario podría auto-otorgarse
  `is_staff` haciendo `PATCH` sobre su propio perfil (verificado explícitamente con un smoke
  test: se intentó, se confirmó que no tiene efecto). El frontend usa `is_staff` para decidir si
  mostrar botones de alta/edición en pantallas `IsStaffOrReadOnly` (ej. artículos) — es sólo una
  mejora de UX, el backend igual rechaza la escritura con 403 si se intenta igual.

### `PATCH /api/v1/usuario/cambiar-clave-secreta/`
- Acción custom del `UsuarioViewSet`. Body: `{clave, clave_nueva, clave_nueva_2}`. Valida la
  contraseña actual, coincidencia de las nuevas y reglas de Django, y actualiza la contraseña del
  usuario autenticado.

## Permiso `IsStaffOrReadOnly`

Definido en `util.permissions.IsStaffOrReadOnly` (nuevo, etapa 4 — dominio `articulo`): cualquier
usuario autenticado puede leer (`GET`/`list`/`retrieve`); sólo usuarios con `is_staff=True` (el
mismo criterio que ya usa Django Admin) pueden crear/editar/borrar. Se usa en los ViewSets de
catálogo/precios de `articulo` porque el mostrador necesita **consultar** productos y precios
para vender, pero no debería poder **modificarlos** vía API — ver
`especificaciones.md` §15 y `SISTEMA_ACTUAL.md` §15.4. Se reutiliza en los próximos dominios
donde aplique el mismo criterio (a evaluar caso por caso, no es automático).

## Catálogo de artículos y precios (`articulo`) — nuevo, etapa 4

Todos bajo `IsAuthenticated` para lectura, `IsStaffOrReadOnly` para escritura (ver arriba). Todos
son `ModelViewSet` completos (list/retrieve/create/update/partial_update/destroy) registrados en
`project/router.py`. El `destroy` de `Articulo` y `Precio` es un **soft delete**
(`django-softdelete`: el manager por defecto ya excluye los borrados de todas las respuestas, y
`DELETE` no borra la fila física — queda disponible sólo vía `Articulo.objects.all_with_deleted()`
desde Django, no expuesto por la API).

| Recurso | Endpoint | Serializer | Filtros (`?query=`) | Búsqueda | Notas |
|---|---|---|---|---|---|
| Tipo de IVA | `/api/v1/tipoiva/` | `TipoIvaSerializer` | — | `search=` (nombre) | catálogo simple |
| Unidad de medida | `/api/v1/unidadmedida/` | `UnidadMedidaSerializer` | — | `search=` (nombre, abreviatura) | catálogo simple |
| Categoría | `/api/v1/categoria/` | `CategoriaSerializer` | `nodo_padre`, `tipo_iva` | `search=` (nombre) | árbol MPTT; expone `nodo_padre` como id del padre, sin anidar hijos todavía |
| Lista de precios | `/api/v1/listaprecio/` | `ListaPrecioSerializer` | — | `search=` (nombre) | sólo `nombre`, tal como está el modelo hoy (ver `SISTEMA_ACTUAL.md` §6 sobre el endpoint legacy roto que esperaba más campos) |
| Artículo | `/api/v1/articulo/` | `ArticuloSerializer` | `categoria`, `unidad_medida`, `es_por_peso` | `search=` (nombre, código, abreviatura) | incluye `categoria_nombre`/`unidad_medida_nombre` de sólo lectura para listas sin N+1 |
| Precio | `/api/v1/precio/` | `PrecioSerializer` | `articulo`, `sucursal`, `lista_precio` | — | uso típico: `GET /api/v1/precio/?articulo=<id>&sucursal=<id>&lista_precio=<id>`; incluye nombres de artículo/sucursal/lista de sólo lectura; la unicidad `(articulo, sucursal, lista_precio)` la valida DRF automáticamente a partir del `UniqueConstraint` del modelo |

Reemplaza, para el catálogo de artículos y precios, a las vistas legacy `get_articulos`,
`get_articulos_todos`, `get_precio_articulo` y `get_listas_precio_sucursal` de
`SISTEMA_ACTUAL.md` §9 — esas vistas **no se tocaron todavía** (siguen sirviendo al JS del Admin
actual, conviven hasta que React las reemplace, DEC-001).

Verificado con un smoke test manual (Django `APIClient` + sqlite en memoria): anónimo → 401;
usuario autenticado no-staff → 200 en lectura y 403 en escritura; staff → 201 al crear; soft
delete confirmado (204, desaparece del listado y de `retrieve`, sigue en la tabla).

## Clientes (`cliente`) — nuevo, etapa 4

| Recurso | Endpoint | Serializer | Filtros | Búsqueda | Permiso |
|---|---|---|---|---|---|
| Cliente | `/api/v1/cliente/` | `ClienteSerializer` | `condicion_iva`, `lista_precio` | `search=` sobre `persona__nombre`, `persona__apellido`, `persona__documento_identidad` | `IsAuthenticated` (no restringido a staff: dar de alta un cliente es parte de la operación normal de mostrador, a diferencia de tocar precios) |

`ClienteSerializer` expone `persona` (id, para escritura) + `persona_detalle` (objeto
`PersonaSerializer` completo, sólo lectura, para no requerir un segundo pedido al buscar
clientes) + `condicion_iva_display` (texto legible) + `lista_precio_nombre` (sólo lectura,
`None` si el cliente no tiene lista asignada — el campo es nullable en el modelo). Orden por
defecto: apellido de la persona, igual que la pantalla de venta legacy
(`venta.views.get_clientes`).

Reemplaza, para alta/consulta/búsqueda de clientes, a `venta.views.get_clientes` de
`SISTEMA_ACTUAL.md` §9 (esa vista legacy no se tocó todavía, sigue sirviendo al Admin actual).
No cubre (queda para la etapa de `venta`): `verificar_cumpleanios` y `get_listaprecio`, que son
casos de uso específicos del punto de venta, no de un CRUD de clientes.

Verificado con smoke test: anónimo → 401; alta por un usuario no-staff → 201 (permiso simple,
no requiere staff); búsqueda por documento → funciona; cliente sin `lista_precio` → serializa
`lista_precio: null` / `lista_precio_nombre: null` sin error (caso nullable probado a propósito).

## `TranslateDjangoValidationErrorMixin`

Definido en `util.mixins.TranslateDjangoValidationErrorMixin` (nuevo, etapa 4 — dominio
`promocion`). Varios modelos del proyecto validan reglas de negocio en `Model.clean()`, invocado
desde el propio `Model.save()` vía `full_clean()` — no sólo desde un `ModelForm` de Django Admin
(ejemplo: `promocion.Promocion`, ver `SISTEMA_ACTUAL.md` §6). Sin este mixin, ese
`django.core.exceptions.ValidationError` escapa del manejo de errores de DRF y se convierte en un
500 en vez de un 400 con el detalle. El mixin sobreescribe `perform_create`/`perform_update` para
traducirlo. Se usa en cualquier `ModelViewSet` cuyo modelo valide así, para no tener que duplicar
esa lógica en el serializer (y así Django Admin y la API comparten exactamente la misma regla).

## Promociones y descuentos (`promocion`) — nuevo, etapa 4

Todos con permiso `IsStaffOrReadOnly` (afectan precios/descuentos, igual criterio que
`articulo`).

| Recurso | Endpoint | Serializer | Filtros | Notas |
|---|---|---|---|---|
| Días de la semana | `/api/v1/diassemana/` | `DiasSemanaSerializer` | — | expone `dias_texto` de sólo lectura (`obtener_dias()` del modelo, ej. `"Lunes, Martes"`) |
| Promoción | `/api/v1/promocion/` | `PromocionSerializer` | `sucursal`, `habilitada`, `es_por_precio` | uso típico del punto de venta: `GET /api/v1/promocion/?sucursal=<id>&habilitada=true`. Expone `dias_semana_detalle` y `sucursal_nombre` de sólo lectura, y `articulos` (lista anidada de `PromocionArticulo`, sólo lectura) para traer todo en un pedido. Las reglas de negocio (`es_por_precio` vs `porcentaje_todos`, `dias_semana` obligatorio, prioridad única por sucursal) las sigue validando `Promocion.clean()` — el ViewSet usa `TranslateDjangoValidationErrorMixin` para que esos errores respondan 400 con el mensaje real, no 500 |
| Artículo en promoción | `/api/v1/promocionarticulo/` | `PromocionArticuloSerializer` | `promocion`, `articulo` | precio fijo (`valor`) de un artículo dentro de una promoción `es_por_precio=True`; también se puede crear/editar directo sin pasar por `Promocion` |
| Descuento | `/api/v1/descuento/` | `DescuentoSerializer` | — | catálogo simple (`nombre`, `valor` 0-100). Los descuentos `CUMPLEAÑOS`/`EMPLEADOS` se siguen identificando por `nombre` exacto, como en el código legacy — ver riesgo en `SISTEMA_ACTUAL.md` §15 (renombrar el registro rompe el descuento; no se corrigió acá, es un cambio de modelo que excede esta etapa) |

**Deliberadamente no incluido todavía**: un endpoint que replique
`venta.utils.get_promociones_activas` (promociones vigentes *por fecha* además de por
`habilitada`/`sucursal`) ni `articulo.utils.buscar_precio_articulo_en_promo` — esa lógica de
"qué promoción aplica a este artículo ahora" es del dominio `venta` (cálculo de precio al vender)
y se resuelve junto con el endpoint transaccional de alta de venta, para no duplicarla en dos
lugares que puedan divergir (PEND-G relacionado). Por ahora, filtrar por `sucursal`+`habilitada`
alcanza para reemplazar `promocion.views.get_promociones_sucursal`.

Verificado con smoke test funcional: alta válida (201, con `articulos`/`dias_semana_detalle`
anidados); alta que viola `es_por_precio`/`porcentaje_todos` → 400 con el mensaje del modelo (no
500); alta con `prioridad` duplicada en la misma sucursal → 400; `prioridad` fuera de rango
(1-10) → 400 desde la validación del propio serializer (antes de tocar la base); filtro
`sucursal`+`habilitada` → funciona; alta de `PromocionArticulo` y su aparición anidada en el
detalle de la promoción → funciona; usuario no-staff → lee pero no puede crear (403).

## Cuenta corriente (`cuentacorriente`) — nuevo, etapa 4

| Recurso | Endpoint | Serializer | Filtros | Permiso |
|---|---|---|---|---|
| Cuenta corriente | `/api/v1/cuentacorriente/` | `CuentaCorrienteSerializer` | `cliente`, `activa`; `search=` sobre nombre/apellido/documento del cliente | `IsStaffOrReadOnly` — abrir/configurar una cuenta (tope, activa) es una decisión de crédito, no operación de mostrador |
| Movimiento de cuenta corriente | `/api/v1/movimientocuentacorriente/` | `MovimientoCuentaCorrienteSerializer` | `cuenta`, `tipo`, `venta` | `IsAuthenticated` — registrar un pago o un consumo a cuenta es operación normal de mostrador, igual que cobrar una venta |

`CuentaCorrienteSerializer` expone `saldo` (`SerializerMethodField`, reutiliza
`cuentacorriente.utils.calcular_saldo_cc` — no se duplica la fórmula) y `cliente_nombre` de
sólo lectura. `MovimientoCuentaCorrienteSerializer` expone `tipo_display` y `cliente_nombre` de
sólo lectura.

**Dos correcciones deliberadas respecto al comportamiento legacy** (sólo en esta capa nueva, no
se tocó el modelo ni las vistas/Admin existentes — conviven ambos comportamientos hasta que se
decida retirar el legacy):

1. **`usuario` del movimiento se asigna server-side** desde `request.user`
   (`ViewSet.perform_create`), es de sólo lectura en el serializer — un intento de mandar
   `usuario` en el body se ignora. Antes no había ningún endpoint DRF para esto, así que no es
   una regresión de un comportamiento existente, es cerrar un hueco antes de que exista.
2. **Se valida el `tope`** al crear un movimiento de tipo `D` (débito/consumo): si
   `saldo_actual + importe > cuenta.tope`, responde 400. Esto **no existe en el código legacy**
   (`SISTEMA_ACTUAL.md` §15.6: "`CuentaCorriente.tope` no se valida nunca") — se agrega acá
   porque es la primera vez que se construye un endpoint real para crear estos movimientos, y
   dejar pasar sin control un límite de crédito que sí está modelado (`tope` existe como campo,
   sólo que nadie lo usa) sería repetir el bug a sabiendas. Los créditos (pagos, tipo `C`) nunca
   se bloquean por tope, sólo los débitos. También se valida `importe > 0`.

Reemplaza, para consulta de saldo y alta de movimientos, a `cuentacorriente.views.get_cc_cliente`
y a `cuentacorriente.utils.guardar_pago_ccorriente`/`cobrar_ccorriente` de `SISTEMA_ACTUAL.md`
§5 — esas vistas legacy no se tocaron todavía. **Nota**: `cobrar_ccorriente` (legacy) además crea
un `Ingreso` de caja al cobrar cuenta corriente fuera de una venta; este endpoint nuevo **no**
replica ese efecto colateral sobre caja — se resuelve cuando se migre `caja` (la relación
movimiento de cta.cte. ↔ movimiento de caja es del dominio de caja, no de cuenta corriente).

Verificado con smoke test funcional: anónimo → 401; saldo inicial en 0; vendedor no-staff no
puede crear/editar la cuenta pero sí puede registrar un movimiento; intento de falsear `usuario`
en el body → se ignora, queda el usuario autenticado real; débito dentro del tope → 201, saldo se
actualiza; débito que supera el tope → 400 con el detalle; importe negativo → 400; crédito grande
(por encima del tope) → se permite igual, sólo los débitos se controlan; historial filtrado por
`cuenta` → funciona.

## Venta (`venta`) — nuevo, etapa 4

`ReadOnlyModelViewSet` (`list`/`retrieve`, `IsAuthenticated`) + dos acciones dedicadas — **no**
es un `ModelViewSet` de CRUD directo (especificaciones.md §4: una venta es una operación
transaccional controlada por el backend, no CRUD sobre varios modelos).

| Acción | Endpoint | Permiso | Qué hace |
|---|---|---|---|
| Listar / detalle | `GET /api/v1/venta/`, `GET /api/v1/venta/<numero_ticket>/` | `IsAuthenticated` | Filtros `sucursal`, `cliente`, `cobrada`, `anulado`; incluye `articulos` anidados (`VentaArticuloSerializer`) y nombres legibles de cliente/empleado/usuario/sucursal |
| Crear venta | `POST /api/v1/venta/crear/` | `IsAuthenticated` | Alta transaccional (`venta.services.crear_venta`, `transaction.atomic()`). Body: `{"empleado": <id>, "cliente": <id>, "articulos": [{"articulo": <id>, "cantidad_peso": "2.00"}, ...]}` |
| Anular venta | `POST /api/v1/venta/<numero_ticket>/anular/` | `IsAdminUser` (staff, igual criterio que hoy tiene Django Admin) | Sólo ventas **no cobradas** (ver PEND-J en `DECISIONES.md`); responde 400 si ya está anulada o si está cobrada |

### El precio nunca se recibe del frontend

`crear` recalcula el precio de **cada** artículo enteramente en servidor
(`venta.utils.calcular_precio_venta_articulo`, nueva) — corrige el riesgo de
`SISTEMA_ACTUAL.md` §15.4, donde el flujo legacy sí confiaba en un `precio_unitario` enviado por
el frontend para las ventas con descuento de cumpleaños/empleado. La función nueva reutiliza (no
duplica) `cumpleanio`, `es_empleado`, `get_precio_articulo`, `get_promociones_activas` y
`buscar_precio_articulo_en_promo`, ya existentes en `venta/utils.py`, y replica exactamente la
misma cascada de reglas que ya tenía el sistema:

1. Cumpleaños del cliente + `Descuento(nombre='CUMPLEAÑOS')` con `valor>0` → ese % sobre el
   precio de lista.
2. Si no, cliente es empleado + `Descuento(nombre='EMPLEADOS')` con `valor>0` → ese %.
3. Si no, y la lista de precios del cliente contiene `'COMUN'` → precio de alguna `Promocion`
   activa de la sucursal (por prioridad) si el artículo entra, si no precio de lista.
4. Si no (cliente con lista propia, no común) → precio de lista, sin promo.

**El peso/cantidad sí se recibe del frontend tal cual** (`cantidad_peso`) — no hay forma de
validarlo en servidor porque lo mide una balanza física en el mostrador (DEC-006/PEND-F: sigue
siendo un `http://localhost:4700` que llama el navegador directo, fuera de Django; el backend ni
se entera de que existe). *Nota aparte, no relacionada con esta etapa*: el campo
`VentaArticulo.cantidad_peso` del modelo sólo admite 2 decimales (`decimal_places=2`), es decir
precisión de 10 gramos, no de 1 gramo — así estaba ya en el modelo, no se tocó.

### Validaciones de la acción `crear` (además del precio)

- Exige caja abierta en la sucursal del usuario autenticado (igual que el legacy
  `guardar_venta`) → 400 `{"caja": "..."}` si no hay.
- El usuario debe tener `sucursal` asignada → 400 `{"usuario": "..."}` si no.
- `empleado` debe existir y no tener `fecha_baja` (mismo filtro que `venta.views.get_empleados`).
- Cada artículo debe tener precio cargado para la lista de precios del cliente en esa sucursal →
  400 `{"articulos": "..."}` con el código del artículo si no.
- `cantidad_peso` debe ser mayor que cero.

### Lo que anular NO hace todavía

Anular una venta ya cobrada requiere decidir qué pasa con los `CobroVenta`/`CuponPagoTarjeta`
asociados — no está resuelto (PEND-J, `DECISIONES.md`). El endpoint responde 400 en ese caso en
vez de intentar revertir algo a medias.

### Lo que no se migró a propósito

`venta.CierreVentas` no se migra (DEC-007: confirmado por el usuario que ya no se usa, sólo el
cierre de caja). Impresión de ticket (PDF vía WeasyPrint) sigue siendo sólo la vista legacy
(`venta.views.imprimir_ticket`) — se resuelve en la etapa de impresión del roadmap, no en esta.

Verificado con smoke test funcional cubriendo: sin caja abierta → 400; alta con descuento de
cumpleaños, con descuento de empleado, y con promoción de cliente común → los tres calculan el
precio correcto en servidor; **intento explícito de mandar un `precio_unitario` falso en el
payload → completamente ignorado**, el precio calculado en servidor prevalece; empleado dado de
baja → 400; artículo sin precio para la lista del cliente → 400 con mensaje claro; anular por
usuario no-staff → 403; anular por staff → 200; anular dos veces → 400; anular venta cobrada →
400 (PEND-J); listado filtrado por sucursal → funciona.

## Caja (`caja`) — nuevo, etapa 4 (cierra la etapa)

| Recurso | Endpoint | Permiso | Notas |
|---|---|---|---|
| Tarjeta de crédito | `/api/v1/tarjetadecredito/` | `IsStaffOrReadOnly` | catálogo simple |
| Plan de tarjeta | `/api/v1/plantarjetadecredito/` | `IsStaffOrReadOnly` | `interes` (%) usado para recalcular el recargo al cobrar |
| Cupón de pago con tarjeta | `/api/v1/cuponpagotarjeta/` | `IsAuthenticated`, sólo lectura | se crean exclusivamente vía `caja/cobrar-venta/` |
| Pago por transferencia | `/api/v1/pagotransferencia/` | `IsAuthenticated`, sólo lectura | ídem |
| Caja | `/api/v1/caja/` | `IsAuthenticated`, sólo lectura (`list`/`retrieve`) + acciones `abrir`/`cerrar` | expone `saldo_actual` (reutiliza `caja.utils.calcular_saldo_caja`) |

Al igual que `venta`, `caja` **no** es un `ModelViewSet` de CRUD directo — abrir/cerrar/cobrar son
acciones de negocio dedicadas y transaccionales (`caja/services.py`).

### `POST /api/v1/caja/abrir/`
`IsAuthenticated`. Abre una caja para la sucursal del usuario autenticado. Falla (400) si ya hay
una caja abierta en esa sucursal, o si el usuario no tiene sucursal asignada. `caja_inicial` se
autocompleta con el `caja_final` de la última caja cerrada de la sucursal (0 si es la primera) —
igual criterio que `CajaAdmin.save_model` legacy.

### `POST /api/v1/caja/<id>/cerrar/`
`IsAuthenticated`. Cierra la caja: calcula `caja_final` (reutiliza
`caja.utils.calcular_caja_final`) y devuelve, además de los datos de la caja, el desglose de
cierre (`ingresos`, `total_ingresos`, `egresos`, `total_egresos`, `total_cuenta_corriente` —
reutiliza `caja.utils.calcular_ingresos_caja`/etc., no se duplica la fórmula).

**Corrección deliberada respecto al legacy**: `caja.views.cerrar_caja` y
`CajaAdmin.cerrar_caja` cuentan las ventas sin cobrar de **todo el sistema**
(`Venta.objects.filter(cobrada=False)`, sin filtrar por sucursal — `SISTEMA_ACTUAL.md` §15.9),
por lo que una venta sin cobrar en la sucursal X podía bloquear el cierre de caja de la sucursal
Y. Este endpoint nuevo sólo cuenta las ventas sin cobrar **de la sucursal de esa caja**.
Verificado con smoke test: una venta sin cobrar en la propia sucursal sí bloquea el cierre; tras
cobrarla, cierra sin problema.

### `POST /api/v1/caja/cobrar-venta/`
`IsAuthenticated`. Cobro combinado de una venta (reemplaza a `caja.views.cobrar_ticket`). Body:

```json
{
  "venta": 123,
  "pagos_efectivo": [{"importe": "500.00"}],
  "pagos_tarjeta": [{"plan_tarjeta": 1, "numero_tarjeta": "1234", "importe": "300.00", "numero_cupon": "0001", "lote": "01"}],
  "pagos_cuenta_corriente": [{"importe": "150.00"}],
  "pagos_transferencia": [{"importe": "50.00", "documento_identidad": "12345678", "nombre": "...", "banco": "..."}]
}
```

Las 4 listas son opcionales pero al menos una no puede estar vacía; se puede combinar más de un
medio de pago en la misma venta, como en el legacy.

**Cuatro correcciones deliberadas respecto al legacy**, todas sólo en este endpoint nuevo (el
flujo de Admin/JS sigue igual):

1. **La suma de los pagos debe cubrir exactamente `venta.monto`** — el legacy nunca lo
   validaba. El recargo de tarjeta no cuenta para este total (es un costo financiero aparte, no
   parte del precio de venta).
2. **`venta.cobrada = True` sólo si absolutamente todo se registró sin error** (toda la
   operación corre en `transaction.atomic()`) — el legacy la marcaba cobrada aunque algún medio
   de pago fallara a mitad de camino (`SISTEMA_ACTUAL.md` §15.12, el propio equipo lo señalaba
   en un comentario del código).
3. **El recargo de tarjeta se recalcula en servidor** a partir de `plan_tarjeta.interes`
   (`recargo = importe * interes / 100`) — el legacy aceptaba `recargo`/`importe_con_recargo`
   tal cual venían del frontend (`SISTEMA_ACTUAL.md` §15.5). Verificado con smoke test: se mandó
   un recargo falso a propósito y se ignoró por completo.
4. **El pago a cuenta corriente valida el `tope`**, reutilizando la misma regla agregada en el
   dominio `cuentacorriente` (no se duplica, se llama a la misma función de saldo).

Otras validaciones: caja abierta en la sucursal del usuario; venta no anulada; venta no cobrada
ya; venta no anterior a la apertura de la caja actual (`caja.fecha_inicio <= venta.fecha`, igual
chequeo que el legacy).

**DEC-008 (ver `DECISIONES.md`)**: de paso se corrigió `MovimientoCaja.clean()` (el modelo base
de `CobroVenta` y del resto de movimientos de caja), que hasta ahora ataba cualquier movimiento a
"la última caja creada en todo el sistema" en vez de a la de su propia sucursal — con más de una
sucursal operando a la vez esto podía atribuir mal los movimientos, o directamente bloquear el
cobro en todas las sucursales. Se corrigió a nivel modelo (afecta también a Admin, es la
corrección de un bug, no un cambio de regla de negocio) y se verificó con un smoke test que abre
cajas en dos sucursales distintas y confirma que cada cobro queda atado a la caja de su propia
sucursal.

### Lo que quedó fuera de esta etapa, a propósito

- **Movimientos "varios" de caja** (`Sueldo`, `Adelanto`, `Ingreso`, `RetiroEfectivo`, `Gasto`,
  y sus catálogos `TipoIngreso`/`TipoGasto`) no se expusieron todavía en la API — no son
  centrales para el flujo de venta/cobro que era el objetivo de esta etapa. Quedan para un
  incremento posterior (misma mecánica que el resto: `ModelViewSet` con
  `TranslateDjangoValidationErrorMixin`, ya que también validan en `save()`).
- **PEND-J (anular venta cobrada)** sigue sin resolver — ahora que `CobroVenta`/
  `CuponPagoTarjeta` están modelados en la API, están las piezas para encararlo, pero decidir
  qué hacer con esos movimientos al anular (reversar, generar egreso compensatorio, etc.) no se
  abordó en esta etapa.

Verificado con smoke test funcional extenso: apertura de caja en dos sucursales distintas y
confirmación del fix de DEC-008; cobro combinado con efectivo, tarjeta (recargo recalculado) y
cuenta corriente (tope validado); monto que no coincide → 400; venta ya cobrada → 400; cierre de
caja bloqueado por venta sin cobrar de la propia sucursal pero no por la de otra sucursal; cierre
exitoso con desglose de ingresos/egresos.

## Sucursales y empleados (`empleado`) — nuevo, etapa 7

Faltaba del backend: la pantalla de venta necesita elegir "quién atiende" (empleado) — no tenía
API propia hasta ahora, sólo modelos usados internamente por `venta`/`caja`.

| Recurso | Endpoint | Filtros | Permiso |
|---|---|---|---|
| Sucursal | `/api/v1/sucursal/` | `search=` (nombre) | `IsStaffOrReadOnly` (alta de sucursal es decisión de infraestructura) |
| Empleado | `/api/v1/empleado/` | `fecha_baja` (ej. `?fecha_baja__isnull=true` para activos), `search=` (nombre/apellido/cuil) | `IsStaffOrReadOnly` (alta/baja es RR.HH.; leer para elegir en el punto de venta es operación normal, igual que el legacy `get_empleados`) |

`EmpleadoSerializer` expone `persona_nombre` y `activo` (`fecha_baja is None`) de sólo lectura.

## Previsualización de venta (`venta`) — nuevo, etapa de pantallas reales

### `POST /api/v1/venta/previsualizar/`
`IsAuthenticated`. Calcula el precio de cada artículo con la misma lógica exacta que `crear`
(reutiliza `venta.utils.calcular_precio_venta_articulo`, sin duplicarla) **sin persistir nada** —
pensado para que el frontend muestre el total en tiempo real mientras se arma el carrito
(especificaciones.md §6: "feedback inmediato"). No exige caja abierta (es sólo un cálculo).
Body: `{"cliente": <id>, "articulos": [{"articulo": <id>, "cantidad_peso": "1.250"}]}`. Devuelve
`{"articulos": [...], "monto": "..."}`. Verificado con smoke test: no persiste ninguna `Venta`;
artículo sin precio → 400 con mensaje claro (mismo comportamiento que `crear`).

## Corrección de seguridad en `cliente` (nuevo, esta sesión)

`ClienteViewSet` **ya no expone `DELETE`** (antes era `ModelViewSet` completo). Motivo:
`Venta.cliente` es `on_delete=CASCADE` — borrar un `Cliente` borraba en cascada **todo su
historial de ventas**, y el permiso era `IsAuthenticated` (cualquier vendedor, no sólo staff).
Se detectó al construir la pantalla de clientes del frontend. Ahora es
`ListModelMixin + CreateModelMixin + RetrieveModelMixin + UpdateModelMixin` (sin `destroy`).
Verificado con smoke test: `DELETE /api/v1/cliente/<id>/` → 405.

## Corrección de seguridad en `usuario` (nuevo, esta sesión)

`UsuarioSerializer` ahora expone `is_staff` y `sucursal` (el frontend los necesita: `is_staff`
para decidir si mostrar acciones de escritura en pantallas `IsStaffOrReadOnly` como artículos).
**Ambos son de sólo lectura** (`read_only_fields`) — sin eso, cualquier usuario podría
auto-otorgarse `is_staff` haciendo `PATCH /api/v1/usuario/me/`, dado que ese endpoint permite
actualizar el propio perfil. Verificado con smoke test: se intentó `PATCH {"is_staff": true}`
con un usuario no-staff y se confirmó que no tiene efecto.

## Sucursales y empleados (`empleado`) — nuevo, etapa de pantallas reales

Faltaba del backend: la pantalla de venta necesita elegir "quién atiende" (empleado) — no tenía
API propia hasta ahora, sólo modelos usados internamente por `venta`/`caja`.

| Recurso | Endpoint | Filtros | Permiso |
|---|---|---|---|
| Sucursal | `/api/v1/sucursal/` | `search=` (nombre) | `IsStaffOrReadOnly` (alta de sucursal es decisión de infraestructura) |
| Empleado | `/api/v1/empleado/` | `fecha_baja` (ej. `?fecha_baja__isnull=true` para activos), `search=` (nombre/apellido/cuil) | `IsStaffOrReadOnly` (alta/baja es RR.HH.; leer para elegir en el punto de venta es operación normal, igual que el legacy `get_empleados`) |

`EmpleadoSerializer` expone `persona_nombre` y `activo` (`fecha_baja is None`) de sólo lectura.
Verificado con smoke test: listar activos funciona; vendedor no-staff no puede crear (403).

## Vistas JSON "a mano" (no DRF) — inventario completo en `SISTEMA_ACTUAL.md` §9

El resto de la operatoria (venta, cobro, caja, cuenta corriente, precios, promociones,
inventario) se sirve hoy por **vistas de función bajo `/admin/...` que arman JSON con
`json.dumps`**, consumidas exclusivamente por el JS embebido en los templates de Admin, no
pensadas como API pública. El listado completo con método/URL/vista está en
`SISTEMA_ACTUAL.md` §9 — se van a ir migrando a DRF (con recálculo server-side de todo lo
financiero) a medida que cada dominio entre en su etapa correspondiente del roadmap, y este
documento se irá completando con la tabla estándar (endpoint / método / auth / params /
request / response / errores / frontend que lo usa) en ese momento.
