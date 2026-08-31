/**
 * Integración con la balanza física del mostrador — DEC-006 (ver
 * ../../docs/modernizacion/DECISIONES.md en la raíz del repo): en cada máquina de venta corre un
 * script Python aparte (fuera de este proyecto) que expone el peso actual en un puerto local.
 * El backend Django NO se entera de que esto existe — es un llamado directo del navegador,
 * igual que en el JS legacy (`admin/venta/venta/add.html`).
 */
const URL_BALANZA = 'http://localhost:4700'

export async function leerPesoBalanza(): Promise<string> {
  const response = await fetch(URL_BALANZA)
  if (!response.ok) {
    throw new Error('No se pudo leer la balanza.')
  }
  const texto = (await response.text()).trim()
  const valor = Number(texto)
  if (Number.isNaN(valor)) {
    throw new Error(`La balanza devolvió un valor inesperado: "${texto}"`)
  }
  return valor.toFixed(2)
}
