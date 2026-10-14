# Decisiones arquitectónicas

Formato: `DEC-XXX: título` + motivo + alternativas consideradas + implicancias. Se agregan a
medida que se toman, en orden cronológico ascendente.

---

## DEC-001: Mantener Django Admin como backoffice

**Decisión**: Django Admin sigue existiendo indefinidamente como herramienta administrativa,
en paralelo al nuevo frontend React. No se retira ninguna funcionalidad de Admin como parte de
esta modernización salvo que se documente explícitamente lo contrario.

**Motivo**: Es requisito explícito del usuario (`especificaciones.md` §1, §6, §8) y evita una
reescritura riesgosa "a ciegas": gran parte de la lógica de negocio real hoy vive en
personalizaciones de Admin (ver `SISTEMA_ACTUAL.md` §7) que tomaría tiempo no trivial reproducir
1:1 en React sin antes entenderlas a fondo.

**Alternativas consideradas**: reemplazo total inmediato de Admin por React — descartada por
riesgo de pérdida de funcionalidad y por instrucción explícita del usuario.

**Implicancias**: el backend debe seguir sirviendo tanto vistas Admin como API DRF sobre los
mismos modelos; la lógica de negocio compartida (cálculo de precios, saldo de caja, etc.) debe
extraerse a funciones/servicios reutilizables por ambos consumidores en vez de duplicarse.

---

## DEC-002: OAuth2 con Authorization Code + PKCE para el cliente React

**Decisión**: el frontend React se autentica contra Django usando el flujo **Authorization Code
con PKCE** de OAuth2, sobre `django-oauth-toolkit` (ya instalado). No se usa Resource Owner
Password Credentials.

**Motivo**: es el flujo recomendado para SPAs públicas (sin client secret embebido en el
navegador) y evita manejar credenciales de usuario directamente en el frontend.

**Alternativas consideradas**: password grant simple — descartado, deprecado en OAuth 2.1 y menos
seguro para este caso.

**Implicancias**: hay que crear una `Application` de tipo *public* + *authorization-code* en
`django-oauth-toolkit`, definir la pantalla/redirect de callback en React, y resolver el
almacenamiento del `access_token`/`refresh_token` en el cliente (ver `ARQUITECTURA.md` §
Autenticación). Queda como trabajo concreto de la etapa "OAuth2 para cliente SPA" del roadmap.

**Implementación y verificación (etapa 5, ejecutada)**:
- `project/settings/base.py`: `OAUTH2_PROVIDER` configurado explícitamente (`SCOPES` como dict
  `{'read': ..., 'write': ...}`, `ACCESS_TOKEN_EXPIRE_SECONDS=1800` /30 min/,
  `REFRESH_TOKEN_EXPIRE_SECONDS=2592000` /30 días/, `ROTATE_REFRESH_TOKEN=True`,
  `PKCE_REQUIRED=True` — estas dos últimas ya eran el default de la librería, se dejaron
  explícitas para que la intención quede documentada en el propio settings).
- `OAUTH2_SPA_REDIRECT_URIS` (nuevo setting, desde env `OAUTH2_SPA_REDIRECT_URIS`): redirect
  URI(s) del frontend.
- Management command nuevo `crear_aplicacion_oauth_spa` (`usuario` app): crea/actualiza
  (idempotente, por `name`) la `Application` pública de `django-oauth-toolkit`
  (`client_type=public`, `authorization_grant_type=authorization-code`). No genera
  `client_secret` (no aplica a un cliente público). Se corre con
  `python manage.py crear_aplicacion_oauth_spa` (toma las redirect URIs de
  `OAUTH2_SPA_REDIRECT_URIS`) o pasando `--redirect-uris` a mano.
- **Bug encontrado y corregido en el camino**: `project/settings/testing.py` traía su propio
  `OAUTH2_PROVIDER = {'SCOPES': ['read', 'write', 'groups']}` (lista), que pisaba por completo
  el `OAUTH2_PROVIDER` (dict) de `base.py` y rompía con
  `AttributeError: 'list' object has no attribute 'keys'` en cuanto se ejercitaba un flujo de
  autorización real — la librería instalada espera `SCOPES` como dict. Sólo afectaba a
  `testing.py` (usado por pytest y por los smoke tests de esta sesión), **no** a
  `development`/`production`, que ya usaban el dict correcto de `base.py`. Se sacó la
  redefinición de `testing.py` para que herede el `OAUTH2_PROVIDER` de `base.py`.
- **Verificado con un smoke test funcional end-to-end** (no simulado): `Authorization Code +
  PKCE` completo — `/oauth2/authorize/` (con `code_challenge`/`code_challenge_method=S256`) →
  `/oauth2/token/` (con `code_verifier`) → llamada real a un endpoint protegido con el
  `access_token` (`Authorization: Bearer ...`, pasando por `OAuth2Authentication`, no
  `force_authenticate`) → `refresh_token` (confirmado que rota: el `refresh_token` viejo deja de
  servir y el `access_token` viejo se invalida) → `revoke_token` (confirmado que invalida el
  token). También se probó que el flujo **rechaza** un `code_verifier` incorrecto (400
  `invalid_grant`) y que **exige** PKCE (sin `code_challenge`, `/authorize/` redirige con
  `error=invalid_request&error_description=Code+challenge+required.`).
- **Hallazgo para PEND-I**: al forzar un login con `AUTHENTICATION_BACKENDS` tal como está
  configurado hoy, el primer backend (`drf_social_oauth2.backends.DjangoOAuth2`) **falla al
  instanciarse** (`social_core.exceptions.DefaultStrategyMissingError`) porque `social_django`
  no está en `INSTALLED_APPS` ni hay `SOCIAL_AUTH_STRATEGY` configurado. No es sólo "posiblemente
  sin usar" — está roto si algo lo invoca. Refuerza la sospecha de PEND-I. No se tocó
  `AUTHENTICATION_BACKENDS` todavía (fuera de alcance de esta etapa; se decide en PEND-I).

**Bug real encontrado recién al probar contra un navegador de verdad (etapa 6, no en el smoke
test de la etapa 5 — ver por qué abajo) y corregido**: `/oauth2/authorize/` exige sesión iniciada
(`LoginRequiredMixin`) y redirige a `settings.LOGIN_URL` si no la hay. Este proyecto nunca definió
`LOGIN_URL`, así que Django usaba su default (`/accounts/login/`), **inexistente acá** → 404 real
al hacer click en "iniciar sesión" desde el frontend. El smoke test de la etapa 5 no lo detectó
porque usaba `Client.force_login()`, que setea la sesión directamente sin pasar por ninguna
pantalla de login — un atajo de testing que sortea exactamente el tramo que estaba roto.

Corrección:
- `project/urls.py`: nuevas rutas `path('login/', ...)` / `path('logout/', ...)` con las vistas
  estándar de `django.contrib.auth.views` (`LoginView`/`LogoutView`).
- `project/templates/registration/login.html` (nuevo): template mínimo para `LoginView`.
- `project/settings/base.py`: `LOGIN_URL = '/login/'`, `LOGIN_REDIRECT_URL = '/admin/'`.
- **Importante — por qué no se usó `/admin/login/`** (que sí existe): el login de Django Admin
  exige `is_staff=True` (`AdminAuthenticationForm.confirm_login_allowed`), por diseño. Si
  `LOGIN_URL` hubiera apuntado ahí, cualquier empleado de mostrador con cuenta no-staff (la
  mayoría — `is_staff` está pensado para quien accede al backoffice) **jamás hubiera podido
  loguearse en el frontend React**, con usuario y contraseña correctos y todo. `/login/` usa el
  `AuthenticationForm` genérico, que sólo exige `is_active`.
- Re-verificado con un smoke test que **no usa `force_login`**: sesión anónima real →
  `/oauth2/authorize/` → 302 a `/login/` → `GET` de la página de login (200, confirma que el
  template existe y renderiza) → `POST` real del formulario con usuario/contraseña de un
  **usuario explícitamente no-staff** → redirige de vuelta a `/oauth2/authorize/` → pantalla de
  consentimiento (200) → `POST allow` → `code` de vuelta al frontend. Circuito completo, sin
  atajos de testing, con el caso exacto que se había roto.

---

## DEC-003: Respuestas de la API en JSON plano (no JSON:API)

**Decisión**: todos los endpoints DRF, incluidos los 2 que ya existían (`persona`, `usuario`),
usan JSON plano (`rest_framework.renderers.JSONRenderer`/`JSONParser`) en vez del formato
JSON:API que traía `djangorestframework-jsonapi`.

**Motivo**: simplifica el consumo desde React (sin necesidad de una librería cliente JSON:API ni
de desanidar `data.attributes`) y evita mantener dos convenciones de respuesta a medida que se
agreguen ViewSets nuevos.

**Alternativas consideradas**: mantener JSON:API para lo existente y usar JSON plano sólo para
endpoints nuevos — descartada por significar dos convenciones conviviendo permanentemente.

**Implicancias — ya ejecutado en esta sesión**:
- `REST_FRAMEWORK` en `project/settings/base.py`: renderer/parser/paginación pasaron a las
  clases estándar de DRF; se sacó `EXCEPTION_HANDLER` y `DEFAULT_METADATA_CLASS` (eran
  específicos de JSON:API, ahora usan los default de DRF).
- `util/paginations.py`: `LargePagination` ahora extiende
  `rest_framework.pagination.PageNumberPagination` en vez de `JsonApiPageNumberPagination`.
- `persona/serializers.py` y `usuario/serializers.py`: import cambiado de
  `rest_framework_json_api` a `rest_framework`; se sacó `included_serializers` (concepto de
  JSON:API); se agregó `id` explícito a los campos (antes lo exponía el renderer JSON:API
  automáticamente); `UsuarioSerializer.groups` ahora se declara explícito como
  `GroupSerializer(many=True, read_only=True)` para seguir devolviendo el objeto completo
  (antes lo resolvía `included_serializers`); se sacó del `PersonaSerializer` un
  `extra_kwargs={'usuario': {'read_only': True}}` que referenciaba un campo `usuario` que
  **no existe** en el modelo `Persona` (código muerto/incorrecto de antes, no relacionado con
  este cambio pero se limpió de paso por tocar el mismo archivo).
- `requirements/base.txt`: se sacó `djangorestframework-jsonapi` (ya no se usa en ningún lado del
  código, verificado con grep antes de sacarlo).
- Verificado con `manage.py check` (settings de testing) y una instanciación manual de los
  serializers: ambos endpoints existentes siguen respondiendo con la misma información (incluido
  `id`, `telefonos` anidados, `groups` anidados), sólo cambia el sobre JSON.
- **Pendiente para quien despliegue**: correr `pip install -r requirements/production.txt` (o el
  que corresponda) de nuevo para que el entorno reinstale sin `djangorestframework-jsonapi`; no
  rompe si queda instalado de más, pero conviene limpiarlo.

---

## DEC-004: `inventario` queda desactivado por ahora

**Decisión**: no se reactiva el Admin de `inventario` (hoy comentado por completo, ver
`SISTEMA_ACTUAL.md` §7) ni se diseña stock nuevo en esta etapa. La app y sus modelos siguen en el
código tal cual están, sin tocar.

**Motivo**: decisión explícita del usuario — no es prioridad ahora.

**Implicancias**: la etapa "Stock/Inventario" del `ROADMAP.md` queda pospuesta indefinidamente
(no se planifica ni se estima todavía). Si en el futuro se retoma, hay que volver a preguntar si
se reactiva tal cual estaba o se rediseña (sigue sin existir un campo de stock/saldo por
artículo, ver `SISTEMA_ACTUAL.md` §14).

---

## DEC-005: Contraseña de `backup_db.sh` fuera del archivo, por variable de entorno

**Decisión**: `backup_db.sh` ya no contiene la contraseña de PostgreSQL en texto plano; la toma
de la variable de entorno `PGPASSWORD`, que debe exportarse en el entorno donde corre el script
(crontab del servidor, o un archivo local no versionado que se source antes de invocarlo), y el
script falla explícitamente si no está seteada.

**Motivo**: la contraseña estaba commiteada en texto plano en el historial de git (commit
`e87d3a5`) — un secreto real filtrado, hallazgo de la auditoría (`SISTEMA_ACTUAL.md` §11, §15.1).

**Implicancias — importante, acción pendiente del usuario sobre infraestructura real**:
1. **Rotar la contraseña de PostgreSQL en el servidor de producción** (la que estaba filtrada,
   `vallE.852`, hay que asumirla comprometida aunque el servidor no sea públicamente accesible).
   Esto no se puede hacer desde este repositorio.
2. Exportar la nueva contraseña como `PGPASSWORD` en el entorno donde se ejecuta
   `backup_db.sh` (por ejemplo, agregando una línea al crontab del usuario que corre el backup, o
   un `source /ruta/no/versionada/backup.env` al principio de la tarea programada).
3. El código de `backup_db.sh` ya está corregido en este commit; **el secreto sigue existiendo en
   el historial de git** de todos modos (commit `e87d3a5`) — si se quiere eliminarlo también de
   ahí (reescritura de historia con `git filter-repo`/BFG + force-push), es una operación
   destructiva sobre un repositorio compartido que requiere coordinación aparte y no se hizo acá;
   avisar si se quiere encarar.

---

## DEC-006: la balanza sigue siendo un llamado directo del navegador (PEND-F resuelto)

**Decisión**: React sigue llamando directo a `http://localhost:4700` desde el navegador para
leer el peso, igual que el JS legacy — no se cambia esa arquitectura.

**Motivo**: en cada máquina de venta hay un script Python propio (fuera de este repositorio) que
expone el peso de la balanza en ese puerto local de esa máquina específica. Es una integración
por-máquina, no algo que Django pueda intermediar sin agregar una dependencia de red innecesaria
(el navegador ya está físicamente en la misma máquina que la balanza).

**Implicancias**: el endpoint transaccional de alta de venta (`venta/api.py`, acción `crear`)
recibe `cantidad_peso` ya resuelta en el payload — no intenta leer la balanza ni conocer su
existencia. Queda documentado en `venta/services.py`/`API.md` para que quien construya la pantalla
de venta en React sepa que ese paso (leer `http://localhost:4700`) sigue siendo responsabilidad
100% del frontend, tal como hoy.

---

## DEC-007: `venta.CierreVentas` queda sin migrar (PEND-G resuelto)

**Decisión**: `CierreVentas` no se migra a DRF ni se reactiva su Admin. Sólo el cierre de caja
(`caja.Caja` + `caja` app) es el flujo vigente.

**Motivo**: confirmado por el usuario — el cierre de ventas por rango de tickets ya no se usa,
sólo el cierre de caja.

**Implicancias**: el modelo `CierreVentas` y las funciones de cálculo asociadas
(`venta.utils.calcular_importe_eventuales/descuentos/asado/blandos`) quedan tal cual están,
sin tocar, como candidatas a limpieza de código legacy en la etapa 19 (no se hizo ahora — no es
parte de esta etapa, y no rompen nada por seguir existiendo). El endpoint DRF de `venta` no
expone nada relacionado a `CierreVentas`.

---

## DEC-008: corregir `MovimientoCaja.clean()` para que filtre por sucursal

**Decisión**: `caja.models.MovimientoCaja.clean()` ahora toma la última `Caja` **de la sucursal
del movimiento** (`Caja.objects.filter(sucursal=self.sucursal).latest('id')`) en vez de la
última creada en **todo el sistema** (`Caja.objects.latest('id')`).

**Motivo**: al construir el endpoint de cobro combinado (`caja/services.py`) se detectó que el
bug ya señalado en la auditoría (`SISTEMA_ACTUAL.md` §15.8) era más grave de lo estimado: con más
de una sucursal operando cajas simultáneamente, **todos** los movimientos de caja del sistema
(`CobroVenta`, `Sueldo`, `Adelanto`, `Ingreso`, `RetiroEfectivo`, `Gasto` — todas las subclases de
`MovimientoCaja`, en Admin y ahora también en la API) terminaban atados a la caja creada más
recientemente en cualquier sucursal, no a la caja abierta de la sucursal donde realmente estaba
operando el usuario. Peor aún: si esa caja "más reciente globalmente" estaba cerrada, el sistema
rechazaba **todo** movimiento de caja en **cualquier** sucursal, aunque la caja de esa sucursal
estuviera abierta.

**Alternativas consideradas**: dejarlo como estaba y sólo documentarlo (opción que se le
planteó explícitamente al usuario) — se descartó porque el usuario pidió corregirlo.

**Implicancias**:
- Cambio en `project/apps/caja/models.py`, método `MovimientoCaja.clean()` — mismo
  comportamiento cuando sólo hay una sucursal operando (caso más común hasta ahora), cambia el
  comportamiento sólo cuando hay más de una caja abierta en sucursales distintas al mismo tiempo
  — que es exactamente el caso que estaba roto.
- No requiere migración (no cambia campos del modelo, sólo lógica de validación).
- Afecta tanto a Django Admin como a la API nueva, porque comparten el mismo modelo — es
  intencional, es la corrección de un bug, no un cambio de regla de negocio.
- Verificado con un smoke test específico: se abrieron cajas en dos sucursales distintas (la
  segunda con id mayor que la primera) y se confirmó que un cobro en la primera sucursal quedó
  atado a **su propia** caja, no a la de la segunda.

---

## DEC-009: el frontend React vive en el mismo dominio que Django

**Decisión**: en producción, el frontend React se sirve desde el mismo dominio que la API
Django (no un subdominio ni un dominio separado).

**Motivo**: decisión explícita del usuario. Simplifica CORS (las requests del frontend a la API
son same-origin, no hace falta configurar orígenes cruzados en producción) y permite que el
`refresh_token` viaje en una cookie `httpOnly`+`secure` de primer origen, sin la complejidad de
cookies cross-subdomain ni de un proxy intermedio.

**Alternativas consideradas**: subdominio distinto (`app.dominio.com` hablando con
`api.dominio.com`) — descartada por el usuario, hubiera requerido `CORS_ALLOWED_ORIGINS` y
cookies `SameSite=None`/cross-subdomain.

**Implicancias**:
- `CORS_ALLOW_ALL_ORIGINS = True` (estaba así desde antes de esta modernización) se reemplaza
  por `CORS_ALLOWED_ORIGINS` explícito, tomado de una variable de entorno — en producción no
  debería necesitarse ningún origen cross-site una vez que el build de React se sirva desde el
  mismo dominio, pero **en desarrollo** el servidor de Vite corre en otro puerto
  (`localhost:5173` por defecto) que técnicamente sí es "otro origen" para el navegador, así que
  se necesita igual una lista chica de orígenes de desarrollo permitidos.
- El `redirect_uri` de la `Application` OAuth2 (`OAUTH2_SPA_REDIRECT_URIS`, DEC-002) en
  producción va a ser una ruta bajo el mismo dominio (ej.
  `https://carniceria.dominio.com/auth/callback`), no un dominio aparte.
- Si en el futuro se decide separar el frontend a otro dominio, esta decisión debería
  revisitarse (nueva entrada `DEC-0XX`, no editar esta retroactivamente).

---

## Decisiones pendientes (a resolver con el usuario cuando corresponda su etapa)

Estas **no son decisiones tomadas**, son los puntos donde la auditoría (o el trabajo de una
etapa) encontró que hace falta una definición explícita más adelante. No bloquean el trabajo
actual.

- **PEND-E — Compras/proveedores**: no existen en el sistema actual. ¿Está fuera de alcance o hay
  que diseñarlo de cero? (relacionado con DEC-004, ambos pospuestos)
- **PEND-I — `drf-social-oauth2`**: ¿login social realmente en uso, o vestigial? Afecta si se
  simplifica `AUTHENTICATION_BACKENDS` al terminar de integrar OAuth2 PKCE (DEC-002). Se retoma
  en la etapa "OAuth2 para cliente SPA".
- **PEND-J — Anular una venta ya cobrada**: nueva, surgida al construir `venta/api.py`. Anular
  una venta que ya tiene cobros/cupones de tarjeta/movimientos de cuenta corriente asociados
  implica decidir qué pasa con esos movimientos: ¿se reversan?, ¿se genera un egreso
  compensatorio en caja?, ¿no se permite directamente y hay que hacer una nota de crédito
  aparte? El código legacy nunca resolvió esto realmente (intentaba borrar el `CobroVenta` pero
  con un bug que lo dejaba sin efecto, `SISTEMA_ACTUAL.md` §15.7). El endpoint DRF nuevo
  (`venta/api.py`, acción `anular`) por ahora **sólo permite anular ventas no cobradas** y
  responde 400 explicando por qué en el caso cobrado, en vez de decidir esto unilateralmente. Se
  retoma al migrar `caja` (que es quien conoce los `CobroVenta`/`CuponPagoTarjeta`) o antes, si
  el usuario lo prioriza.
