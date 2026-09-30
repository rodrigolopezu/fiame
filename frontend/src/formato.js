// Formato de presentación. Trabaja sobre el texto que envía el backend, sin pasar a float.

function separarMiles(entero) {
  return entero.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export function dinero(valor, moneda = 'PEN') {
  if (valor === null || valor === undefined || valor === '') return '—'
  const texto = String(valor)
  const negativo = texto.startsWith('-')
  const [entero, decimales = '00'] = texto.replace('-', '').split('.')
  const simbolo = moneda === 'USD' ? 'US$' : 'S/'
  return `${negativo ? '−' : ''}${simbolo} ${separarMiles(entero)}.${decimales.padEnd(2, '0')}`
}

export function tasa(valor) {
  if (valor === null || valor === undefined) return '—'
  return `${valor} %`
}

export function fecha(iso) {
  if (!iso) return '—'
  const [a, m, d] = iso.split('-')
  return `${d}/${m}/${a}`
}

export const PERIODOS = [
  ['ANUAL', 'Anual'], ['SEMESTRAL', 'Semestral'], ['CUATRIMESTRAL', 'Cuatrimestral'],
  ['TRIMESTRAL', 'Trimestral'], ['BIMESTRAL', 'Bimestral'], ['MENSUAL', 'Mensual'],
  ['QUINCENAL', 'Quincenal'], ['DIARIA', 'Diaria'],
]

export const TIPOS_EVENTO = {
  VENTA: 'Venta',
  PAGO: 'Pago',
  CAMBIO_CONDICIONES: 'Cambio de condiciones',
  ANULAR_VENTA: 'Anulación',
  CORTE: 'Corte',
}
