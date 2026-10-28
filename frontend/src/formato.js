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

export const ACCIONES = {
  LOGIN: 'Inicio de sesión',
  AVANZAR_FECHA: 'Fecha del sistema adelantada',
  EDITAR_TIENDA: 'Configuración de la tienda',
  CREAR_PRODUCTO: 'Producto creado',
  EDITAR_PRODUCTO: 'Producto editado',
  CREAR_CLIENTE: 'Cliente registrado',
  EDITAR_CLIENTE: 'Cliente editado',
  BAJA_CLIENTE: 'Cliente dado de baja',
  REACTIVAR_CLIENTE: 'Cliente reactivado',
  GENERAR_CODIGO_PORTAL: 'Código del portal generado',
  REGISTRAR_VENTA: 'Venta registrada',
  ANULAR_VENTA: 'Venta anulada',
  GENERAR_CORTE: 'Estado de cuenta generado',
  REGISTRAR_PAGO: 'Pago registrado',
  ANULAR_PAGO: 'Pago anulado',
}

export const MEDIOS = [['EFECTIVO', 'Efectivo'], ['YAPE', 'Yape'], ['PLIN', 'Plin'], ['TRANSFERENCIA', 'Transferencia'], ['OTRO', 'Otro']]

// Presentación al cliente: 4 decimales (el cálculo siempre usa 7, en el backend).
export function tasaCorta(valor) {
  if (valor === null || valor === undefined) return '—'
  return `${Number(valor).toFixed(4)} %`
}
