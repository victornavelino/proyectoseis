import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import App from './App'
import './index.css'

// Tema mínimo por ahora — se ajusta (colores, tamaños) al construir las primeras pantallas
// reales de mostrador (especificaciones.md: botones claros, uso cómodo en atención al público).
const theme = createTheme({
  primaryColor: 'red',
  fontFamily: 'system-ui, -apple-system, sans-serif',
})

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <MantineProvider theme={theme}>
      <Notifications position="top-right" />
      <App />
    </MantineProvider>
  </React.StrictMode>,
)
