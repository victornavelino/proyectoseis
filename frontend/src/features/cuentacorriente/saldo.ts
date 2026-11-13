// saldo = débitos - créditos (cuentacorriente.utils.calcular_saldo_cc): positivo es deuda del
// cliente hacia el negocio, negativo es saldo a favor del cliente. Se aclara en palabras al lado
// del número en toda pantalla que lo muestre, para no tener que interpretar el signo cada vez.
export function etiquetaSaldo(saldo: string | number): { texto: string; color: string } | null {
  const numero = Number(saldo)
  if (numero > 0) return { texto: '(Deudor)', color: 'red.7' }
  if (numero < 0) return { texto: '(A favor del cliente)', color: 'green.7' }
  return null
}
