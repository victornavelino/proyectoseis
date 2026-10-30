# Arquitectura

## Arquitectura actual

```
┌─────────────────────────────────────────────────────────┐
│ Navegador (mostrador)                                    │
│  - Django Admin (sesión, cookies, CSRF)                  │
│  - Templates admin/* sobrescritos con jQuery embebido     │
│  - Llama directo a http://localhost:4700 (balanza)        │
└───────────────┬────────────────────────────┬─────────────┘
                │ sesión + CSRF               │ HTTP local (fuera de Django)
                ▼                              ▼
┌─────────────────────────────┐      ┌────────────────────┐
│ Django 4.2 (project/)       │      │ Servicio balanza    │
│  - Django Admin              │      │ (no está en el repo)│
│  - Vistas función propias    │      └────────────────────┘
│    bajo /admin/... (JSON     │
│    hecho a mano, no DRF)     │
│  - DRF ya instalado:         │
│    /api/v1/persona/          │
│    /api/v1/usuario/          │
│    /api/v1/usuario/registro/ │
│  - OAuth2 montado en /oauth2/│
│    (django-oauth-toolkit)    │
│  - drf-social-oauth2 en /auth/│
│  - WeasyPrint (PDF tickets)  │
└───────────────┬───────────────┘
                │
                ▼
        PostgreSQL (Dokploy / Docker Compose)
```

Todo corre en un único contenedor (`Dockerfile` + `entrypoint.sh` + `gunicorn`), detrás de
Traefik (Dokploy) que termina TLS. Ver commits `a66dac2`/`dd2756f` para el detalle de esa
configuración — **no tocar `SECURE_PROXY_SSL_HEADER`/`CSRF_TRUSTED_ORIGINS` sin entender el fix**.

## Arquitectura objetivo (a construir incrementalmente)

```
┌───────────────────────────┐        ┌───────────────────────────┐
│ React + TypeScript (Vite) │  OAuth2│ Django Admin (sigue existiendo)│
│ - UI de mostrador          │◄──────►│ backoffice / superusuario  │
│ - cliente API (fetch/axios)│  code+ └───────────────────────────┘
│ - manejo de auth central   │  PKCE
│ - manejo de errores HTTP   │
└──────────────┬─────────────┘
               │ HTTPS + Bearer token (OAuth2 access token)
               ▼
┌─────────────────────────────────────────────┐
│ Django + DRF (mismo proyecto, mismas apps)   │
│  - ViewSets/serializers nuevos por dominio    │
│  - servicios/selectors para lógica compartida │
│    entre Admin y API (extraída progresivamente)│
│  - transaction.atomic() en operaciones        │
│    multi-modelo (venta, cobro, cierre de caja) │
│  - django-oauth-toolkit como Authorization    │
│    Server                                     │
└─────────────────────┬─────────────────────────┘
                       ▼
                 PostgreSQL (sin cambios)
```

Django Admin **no se apaga**: sigue siendo el backoffice (altas de artículos, precios,
promociones, usuarios, reportes de exportación) mientras React se enfoca en la operación diaria
de mostrador (venta, cobro, caja, cuenta corriente). Qué se queda sólo en Admin vs. qué se
replica en React se decide **pantalla por pantalla** en las etapas 9 en adelante — no todo lo que
hoy es un admin custom necesita convertirse en React.

## Autenticación — flujo implementado (DEC-002, DEC-009 — ver `DECISIONES.md`)

- **Authorization Code + PKCE** vía `django-oauth-toolkit`. `Application` pública creada
  (management command `crear_aplicacion_oauth_spa`, idempotente) y flujo verificado
  end-to-end con un smoke test real — ver `API.md` § OAuth2 para el detalle completo (scopes,
  expiración, endpoints, ejemplo de request).
- **DEC-009**: el frontend React vive en el **mismo dominio** que Django en producción
  (decisión del usuario). Consecuencias concretas:
  - `access_token` en memoria del frontend (no `localStorage`, mitiga XSS).
  - `refresh_token` en cookie `httpOnly` + `secure`, primer origen — sin necesidad de
    cross-subdomain ni de un proxy de backend intermedio, porque same-origin en producción.
  - `redirect_uri` de la `Application` es una ruta bajo el mismo dominio (ej.
    `https://carniceria.dominio.com/auth/callback`), configurable vía
    `OAUTH2_SPA_REDIRECT_URIS`.
  - `CORS_ALLOWED_ORIGINS` (`project/settings/base.py`) reemplazó a `CORS_ALLOW_ALL_ORIGINS=True`
    — en producción las requests del frontend son same-origin y no necesitan CORS; la lista sólo
    cubre el servidor de desarrollo de Vite (`localhost:5173`, otro puerto = otro origen para el
    navegador), configurable vía `DJANGO_CORS_ALLOWED_ORIGINS`.
- Formato de respuesta DRF: **JSON plano** (DEC-003) — ya aplicado a todos los endpoints
  existentes. Ver `API.md`.

## Principios para el backend a medida que se extiende

- Reusar `persona`, `usuario`, `util` (ya con `api.py`/`serializers.py`) como plantilla de estilo
  para los ViewSets nuevos.
- Operaciones de negocio complejas (guardar venta, cobrar ticket, cerrar caja) → **una vista
  DRF/APIView transaccional**, no CRUD directo sobre varios modelos desde el frontend. Ya existe
  el patrón en el código legacy (`guardar_venta_cliente_articulos`, `cobrar_ticket`) — la migración
  es envolver esa misma lógica (corrigiendo los riesgos de `SISTEMA_ACTUAL.md` §15) en
  `transaction.atomic()` dentro de un `APIView`/`ViewSet.create` en vez de una vista de función
  que arma JSON a mano.
- Extraer a `services.py`/`selectors.py` sólo donde el Admin y la API vayan a compartir lógica
  (ej. cálculo de precio con descuentos/promos, cálculo de saldo de caja/cta.cte) — no refactorizar
  todo el proyecto de una.
- No tocar modelos existentes salvo que una etapa lo requiera explícitamente y quede documentado
  en `DECISIONES.md` (con su migración).

## Frontend — implementado y verificado (etapa 6)

```
frontend/
  src/
    api/
      client.ts        # fetch central: agrega Bearer token, refresca si venció, normaliza errores
      config.ts         # URLs de API/OAuth2 desde variables de entorno
      articulo.ts, cliente.ts, persona.ts, empleado.ts, venta.ts, caja.ts, balanza.ts
                         # un módulo por dominio, siempre sobre apiFetch (nunca fetch() suelto)
    auth/
      pkce.ts            # code_verifier/code_challenge (RFC 7636, Web Crypto API)
      oauthClient.ts     # login/callback/refresh/logout (Authorization Code + PKCE)
      tokenStore.ts      # tokens en memoria (nunca localStorage)
      AuthContext.tsx    # estado de sesión + perfil (useAuth(), incluye is_staff/sucursal)
      AuthCallback.tsx   # pantalla de destino del redirect_uri
    components/
      AppLayout.tsx       # AppShell (Mantine): sidebar oscuro con 7 secciones agrupadas +
                           # header con breadcrumb/búsqueda/usuario — sigue una referencia de
                           # diseño tipo admin/ERP que pasó el usuario (captura de pantalla)
      ProtectedRoute.tsx
      BuscadorLista.tsx   # buscador genérico (texto + resultados clickeables), reusado en
                           # venta/precio/promoción/cta.cte para elegir cliente/artículo
      EstadoVacio.tsx     # empty state (ícono + texto), usado en toda tabla sin resultados
      Paginador.tsx       # "Mostrando X–Y de Z" + flechas, sobre PageNumberPagination de DRF
      ListaCrud.tsx       # shell genérico de listado (título + filtro + tabla + EstadoVacio +
                           # Paginador), usado por 11 de las 13 pantallas de listado — sólo
                           # cambian columnas y el modal de alta/edición por dominio
    features/
      inicio/           InicioPage.tsx — accesos rápidos
      articulos/        ArticulosPage.tsx + ArticuloFormModal.tsx (CRUD, alta/edición sólo staff)
      catalogo/         CategoriasPage, UnidadesMedidaPage, TiposIvaPage, ListasPrecioPage,
                         PreciosPage (+ PrecioFormModal) — catálogo secundario de `articulo`
      clientes/         ClientesPage.tsx + ClienteFormModal.tsx — alta con búsqueda/creación de
                         Persona integrada (mismo patrón que RegistroUsuarioAPIView del backend)
      empleados/        EmpleadosPage (+ EmpleadoFormModal, mismo patrón de búsqueda de Persona
                         que clientes), SucursalesPage
      promociones/      PromocionesPage (+ PromocionFormModal: días de vigencia como checkboxes,
                         gestión de PromocionArticulo anidada), DescuentosPage
      caja/             CajaPage (apertura/cierre + historial + resumen de cierre),
                         TarjetasPage, PlanesTarjetaPage
      cuentacorriente/  CuentasCorrientesPage (+ CuentaCorrienteFormModal,
                         CuentaCorrienteDetalleModal: saldo + historial + alta de movimiento)
      ventas/           VentaNuevaPage.tsx (punto de venta: carrito en memoria + previsualización
                         de precio en vivo + balanza), CobroVentaPage.tsx (cobro combinado
                         efectivo/tarjeta/cta.cte/transferencia), VentasListPage.tsx, dinero.ts
    hooks/                # vacío por ahora, hooks reutilizables entre features
    types/
      api.ts, usuario.ts, persona.ts, articulo.ts, cliente.ts, empleado.ts, venta.ts, caja.ts
```

**Stack**: Vite + TypeScript + React 19 + React Router 7 + **Mantine** (`@mantine/core`,
`@mantine/hooks`, `@mantine/form`, `@mantine/notifications` — decisión del usuario, sesión de la
etapa 6). Mantine 9 exige React 19, así que se subió el scaffold entero desde el React 18/Vite
5/react-router-dom 6 iniciales; de paso se resolvieron las 4 vulnerabilidades conocidas
(`esbuild`, `react-router`) que traía ese scaffold — `npm audit` da 0 ahora. Estado global más
allá de `AuthContext` sigue sin decidir, se propone al construir las primeras pantallas reales de
alta interacción — venta, cobro, caja, cta.cte necesitan un mini-carrito/formulario en memoria
similar al `articulos = []` del JS legacy.

**Verificado de punta a punta, con herramientas reales** (no sólo escrito a mano): `npm install`,
`npx tsc -b`, `npm run build` y `npm run dev` corridos de verdad — compilan y levantan sin
errores. El flujo de login completo (PKCE → callback → perfil → logout) se probó en un navegador
real. En el camino apareció y se corrigió un bug real de backend (`LOGIN_URL`, ver DEC-002 en
`DECISIONES.md`) — el frontend en sí no necesitó ningún cambio para ese fix.
