# Frontend — Carnicería Virgen del Valle

React 19 + TypeScript + Vite + Mantine (componentes UI) + React Router. Consume la API Django de
`../` vía OAuth2 Authorization Code + PKCE (ver `../docs/modernizacion/API.md` § OAuth2 y
`../docs/modernizacion/ARQUITECTURA.md` para el diseño completo).

> Verificado de punta a punta: `npm install`, `npx tsc -b`, `npm run build` y `npm run dev`
> corridos de verdad (no sólo escrito a mano) — compilan y levantan sin errores, y el login OAuth2
> PKCE completo se probó en un navegador real. El scaffold inicial (React 18 + Vite 5 +
> react-router-dom 6) se subió a React 19 + Vite 8 + react-router-dom 7 al agregar Mantine (que
> exige React 19) y de paso quedaron resueltas 4 vulnerabilidades conocidas (esbuild, react-router)
> que traía el scaffold original — `npm audit` da 0 ahora.

## Poner en marcha

1. Backend Django corriendo (`python manage.py runserver`, puerto 8000 por defecto).
2. Crear la `Application` OAuth2 si todavía no existe:
   ```
   python manage.py crear_aplicacion_oauth_spa
   ```
   Copiar el `client_id` que imprime.
3. `cd frontend && npm install`
4. `cp .env.example .env` y completar `VITE_OAUTH_CLIENT_ID` con el `client_id` del paso 2.
5. `npm run dev` → abre en `http://localhost:5173`.

Al entrar, si no hay sesión, redirige automáticamente a `/oauth2/authorize/` de Django (pantalla
de login + "¿Autorizar a Frontend SPA?"). Tras aceptar, vuelve a `/auth/callback`, intercambia el
código por tokens, y muestra el perfil del usuario autenticado (`InicioPage`, llamando a
`GET /api/v1/usuario/me/`) con un botón para cerrar sesión.

## Estructura

```
src/
  api/
    client.ts      # fetch central: agrega Bearer token, refresca si venció, normaliza errores
    config.ts       # URLs de API/OAuth2 desde variables de entorno
  auth/
    pkce.ts          # generación de code_verifier/code_challenge (RFC 7636)
    oauthClient.ts   # flujo Authorization Code + PKCE (login, callback, refresh, logout)
    tokenStore.ts    # tokens en memoria (nunca localStorage) — ver el comentario ahí sobre
                      # la simplificación respecto al diseño con cookie httpOnly
    AuthContext.tsx  # estado de sesión disponible en toda la app (useAuth())
    AuthCallback.tsx # pantalla de destino de VITE_OAUTH_REDIRECT_URI
  components/
    ProtectedRoute.tsx  # exige sesión, si no hay dispara el login
  features/
    inicio/            # placeholder de esta etapa; cada pantalla real (venta, caja, ...) va
                        # en su propia carpeta acá, siguiendo el mismo patrón
  types/
    api.ts             # tipos compartidos (ej. PaginatedResponse<T>)
  hooks/                # hooks reutilizables entre features (vacío por ahora)
```

## UI: Mantine

`@mantine/core` + `@mantine/hooks` + `@mantine/form` + `@mantine/notifications`, con un
`MantineProvider` mínimo en `main.tsx` (tema con `primaryColor: 'red'`, a ajustar más adelante).
`@mantine/form` todavía no se usó en ninguna pantalla (se suma cuando se arme el primer
formulario real); `@mantine/notifications` está montado y listo para feedback tipo "venta
guardada"/"error al cobrar".

## Qué falta (fuera del alcance de "base del frontend", etapa 6)

- El `refresh_token` vive en memoria igual que el `access_token` (se pierde al recargar la
  página). La variante más segura (cookie `httpOnly` de mismo origen) requiere un endpoint propio
  en el backend que envuelva `/oauth2/token/` — no se hizo, ver `tokenStore.ts`.
- Sin tests todavía (mismo estado que el backend antes de la etapa de testing del roadmap).
- Si tenías `npm run dev` corriendo desde antes de este cambio, conviene reiniciarlo
  (`Ctrl+C` y `npm run dev` de nuevo) — se subieron varias dependencias mayores (React 19, Vite 8,
  react-router-dom 7) y el pre-bundling de Vite queda más prolijo arrancando de cero.
