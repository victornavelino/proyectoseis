import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import App from './App'
import './index.css'

// Inter + estilo flat/Swiss (sin sombras ni degradés, alto contraste, jerarquía clara) — pensado
// para pantallas de mostrador de uso repetitivo: especificaciones.md pide botones claros y uso
// cómodo en atención al público.
const theme = createTheme({
  primaryColor: 'red',
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  headings: { fontFamily: 'Inter, system-ui, -apple-system, sans-serif', fontWeight: '700' },
  defaultRadius: 'md',
})

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <MantineProvider theme={theme}>
      <Notifications position="top-right" />
      <App />
    </MantineProvider>
  </React.StrictMode>,
)
