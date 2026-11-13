import { notifications } from '@mantine/notifications'
import { imprimirCuentaCorriente, imprimirMovimientoCuentaCorriente } from '../../api/cuentacorriente'
import { mensajeDeError } from '../../api/client'

/** Abre un blob PDF en una pestaña nueva -mismo criterio que ventas/imprimirTicket.ts
 * § abrirTicketParaImprimir (Bearer token, no la cookie de sesión de Django). */
function abrirBlobPdf(blob: Blob) {
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

export async function abrirComprobanteDeMovimiento(id: number): Promise<void> {
  try {
    abrirBlobPdf(await imprimirMovimientoCuentaCorriente(id))
  } catch (err) {
    notifications.show({ title: 'No se pudo generar el comprobante', message: mensajeDeError(err), color: 'red' })
  }
}

export async function abrirEstadoDeCuentaParaImprimir(id: number): Promise<void> {
  try {
    abrirBlobPdf(await imprimirCuentaCorriente(id))
  } catch (err) {
    notifications.show({ title: 'No se pudo generar el estado de cuenta', message: mensajeDeError(err), color: 'red' })
  }
}
