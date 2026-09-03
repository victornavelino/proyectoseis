import { notifications } from '@mantine/notifications'
import { imprimirTicket as pedirPdfTicket } from '../../api/venta'
import { ApiError } from '../../api/client'

/** Pide el PDF del ticket a la API (autenticado con el Bearer token, no con la cookie de sesión
 * de Django — por eso no se reusa la vista legacy `venta.views.imprimir_ticket`) y lo abre en
 * una pestaña nueva: ahí el visor de PDF del navegador se encarga del diálogo de impresión,
 * igual que antes con window.print() (ROADMAP.md etapa 16). */
export async function abrirTicketParaImprimir(numeroTicket: number): Promise<void> {
  try {
    const blob = await pedirPdfTicket(numeroTicket)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    // Se revoca después de un rato, no de inmediato: la pestaña nueva necesita que el blob URL
    // siga siendo válido mientras carga el PDF.
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (err) {
    const detalle = err instanceof ApiError ? JSON.stringify(err.detail) : (err as Error).message
    notifications.show({ title: 'No se pudo generar el ticket', message: detalle, color: 'red' })
  }
}
