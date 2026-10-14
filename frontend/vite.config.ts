import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // En producción Django sirve el build bajo /static/frontend/ (DEC-009, mismo dominio — ver
  // ../docs/modernizacion/DECISIONES.md, Dockerfile y project/urls.py § frontend_index). En
  // desarrollo (`npm run dev`) Vite sigue sirviendo todo desde la raíz, como siempre.
  base: command === 'build' ? '/static/frontend/' : '/',
  server: {
    port: 5173,
  },
}))
