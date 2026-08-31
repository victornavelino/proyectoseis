# Estado del proyecto

_Última actualización: 2026-08-30 — fin de sesión larga: CRUD completo de los 13 dominios de
negocio en el frontend, backend con 6 dominios DRF + OAuth2. Sesión cerrada a pedido del
usuario, con todo verificado por compilador/build/smoke-tests pero **sin probar a mano las
pantallas nuevas de esta última tanda**._

## Etapa actual

**Etapas 1 a 13 (+ catálogo secundario, personal, promociones) completas.** Falta: que el
usuario pruebe en el navegador las pantallas construidas en la última tanda (todo lo que no sea
artículos/clientes/venta/cobro, que sí ya se probó y confirmó "quedó perfecto"). Ver `ROADMAP.md`
§ Próxima etapa concreta para el detalle completo de qué se verificó y cómo.

## Qué hay hecho, en una frase por parte

- **Backend**: Django 4.2 + DRF + `django-oauth-toolkit` (Authorization Code + PKCE). 6 dominios
  de negocio expuestos como API (`articulo`, `cliente`, `promocion`, `cuentacorriente`, `venta`,
  `caja`), más `empleado`/`persona`/`usuario`. Todo verificado con smoke tests funcionales reales
  (no mocks) — ver `API.md` para cada endpoint y `DECISIONES.md` (DEC-001 a DEC-009) para el
  porqué de cada decisión de diseño/seguridad tomada en el camino.
- **Frontend**: React 19 + TypeScript + Vite + Mantine + React Router, en `frontend/`. Sidebar
  con 7 secciones (Inicio, Ventas, Catálogo, Clientes, Personal, Promociones, Caja), 19 pantallas
  en total. Login OAuth2 PKCE funcionando de punta a punta (confirmado en navegador). Punto de
  venta con carrito en memoria, previsualización de precio en vivo y lectura de balanza. Cobro
  combinado. El resto son CRUD administrativos con el mismo patrón visual (filtro + tabla +
  paginación).

## Qué falta (para la próxima sesión)

1. **Probar en el navegador** las pantallas de: catálogo secundario (categorías, unidades,
   tipos de IVA, listas de precio, precios), empleados, sucursales, promociones, descuentos,
   tarjetas, planes de tarjeta, caja (abrir/cerrar), cuenta corriente. Reportar qué anda y qué
   no — el patrón de esta sesión (2 bugs reales encontrados así: `LOGIN_URL` y campos
   nullable-pero-no-blank) sugiere que vale la pena antes de dar esto por terminado del todo.
2. Después de eso, el roadmap original sigue en: Stock/Inventario (bloqueado, DEC-004),
   Reportes, Impresión de tickets, Permisos finos, Testing, Limpieza de legacy, Despliegue —
   ninguna arrancada todavía.
3. Decisiones pendientes sin urgencia: PEND-E (compras/proveedores), PEND-I
   (`drf-social-oauth2` roto, evidencia ya encontrada), PEND-J (anular venta cobrada).

## Acción pendiente del usuario (fuera del alcance del código)

- **Rotar la contraseña real de PostgreSQL en el servidor** (DEC-005) — sigue pendiente desde
  el principio de esta modernización, es la única tarea de infraestructura real que quedó sin
  hacer.
- Probar las pantallas nuevas (ver arriba).
- Cuando haya dominio real de producción: completar `OAUTH2_SPA_REDIRECT_URIS`/
  `DJANGO_CORS_ALLOWED_ORIGINS`.

## Cómo continuar en la próxima sesión

Simplemente abrí una conversación nueva acá (Claude Code recuerda el proyecto por la carpeta,
no hace falta repetir nada de contexto) y decime **"Continuá con la siguiente etapa"** — la
consigna original (`especificaciones.md`) es justamente que yo lea esta documentación primero
(este archivo + `ROADMAP.md` + `DECISIONES.md`) antes de tocar nada. Si preferís arrancar
directamente con algo puntual ("probá tal pantalla", "seguí con tal cosa"), también funciona, no
hace falta la frase exacta.

Dos cosas a tener en cuenta para cuando retomes:
- **Nada de esto está commiteado todavía** (todo el trabajo de varias sesiones sigue como
  cambios locales sin commitear en `feature-dokploy`). Si querés que arme commits divididos por
  etapa antes de seguir, pedímelo explícitamente.
- Si volvés a trabajar con el frontend, el `npm run dev` que tenías corriendo puede haber
  quedado abierto en tu terminal — no hace falta que lo toques, pero si lo cerraste, hay que
  volver a levantarlo (`cd frontend && npm run dev`) para probar las pantallas.
