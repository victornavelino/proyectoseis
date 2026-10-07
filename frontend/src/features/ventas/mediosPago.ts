import type { MedioDePago } from '../../types/venta'

// Un color fijo por medio de pago (nunca reasignado según el monto) para que se pinte siempre
// igual en todos lados (torta de "Medios de pago" del Dashboard, badges del listado de Ventas)
// — ver dataviz skill: "color follows the entity, never its rank". Paleta categórica validada
// (CVD-safe) con scripts/validate_palette.js del skill. Compartido entre InicioPage y
// VentasListPage para no duplicar ni desincronizar la paleta.
export const MEDIOS_PAGO_INFO: Record<MedioDePago, { etiqueta: string; color: string }> = {
  efectivo: { etiqueta: 'Efectivo', color: 'blue.6' },
  tarjeta: { etiqueta: 'Tarjeta', color: 'teal.6' },
  cuenta_corriente: { etiqueta: 'Cuenta corriente', color: 'orange.7' },
  transferencia: { etiqueta: 'Transferencia', color: 'grape.6' },
  qr: { etiqueta: 'QR', color: 'pink.6' },
}
