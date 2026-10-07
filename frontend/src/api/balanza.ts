/**
 * Integración con la balanza física del mostrador — DEC-006 (ver
 * ../../docs/modernizacion/DECISIONES.md en la raíz del repo): en cada máquina de venta corre un
 * script Python aparte (fuera de este proyecto) que expone el peso actual en un puerto local.
 * El backend Django NO se entera de que esto existe — es un llamado directo del navegador,
 * igual que en el JS legacy (`admin/venta/venta/add.html`).
 */
const URL_BALANZA = 'http://localhost:4700'

export async function leerPesoBalanza(): Promise<string> {
  // `cache: 'no-store'`: sin esto, al pedir la misma URL cada 300ms (VentaNuevaPage la relee en
  // loop mientras se pesa) el navegador puede servir la respuesta cacheada de la primera lectura
  // en vez de volver a golpear el servidor local — el síntoma es exactamente "toma bien el peso
  // la primera vez pero no se entera si después le agregás o sacás mercadería".
  const response = await fetch(URL_BALANZA, { cache: 'no-store' })
  if (!response.ok) {
    throw new Error('No se pudo leer la balanza.')
  }
  const texto = (await response.text()).trim()
  const valor = Number(texto)
  if (Number.isNaN(valor)) {
    throw new Error(`La balanza devolvió un valor inesperado: "${texto}"`)
  }
  // 3 decimales: precisión de gramos (0.001 kg) — ver VentaArticulo.cantidad_peso en el backend.
  return valor.toFixed(3)
}
