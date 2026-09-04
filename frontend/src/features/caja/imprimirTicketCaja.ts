import { notifications } from '@mantine/notifications'
import { imprimirCaja as pedirPdfCaja } from '../../api/caja'
import { ApiError } from '../../api/client'

/** Pide el PDF del resumen de cierre de caja a la API y lo abre en una pestaña nueva — mismo
 * criterio que `ventas/imprimirTicket.ts` § abrirTicketParaImprimir (Bearer token, no la cookie
 * de sesión de Django). */
export async function abrirResumenCajaParaImprimir(id: number): Promise<void> {
  try {
    const blob = await pedirPdfCaja(id)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (err) {
    const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
    notifications.show({ title: 'No se pudo generar el resumen de caja', message: detalle, color: 'red' })
  }
}
