/** Formatea un string decimal del backend (ej. "1234.50") como moneda para mostrar. */
export function formatearMonto(valor: string | number): string {
  const num = typeof valor === 'string' ? Number(valor) : valor
  if (Number.isNaN(num)) return valor.toString()
  return num.toLocaleString('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 2 })
}
