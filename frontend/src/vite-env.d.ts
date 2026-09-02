/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_OAUTH_CLIENT_ID: string
  readonly VITE_OAUTH_REDIRECT_URI: string
  /** Nombre del negocio mostrado en el sidebar y en el <title> (ver index.html). Opcional. */
  readonly VITE_BUSINESS_NAME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
