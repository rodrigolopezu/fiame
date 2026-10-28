// Frases de la vista simple. `perspectiva` es quien lee: el vendedor ("Juan debe…")
// o el propio cliente ("Debes…").
import { dinero } from './formato'

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre']
const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']

function partes(iso) {
  const [a, m, d] = iso.split('-').map(Number)
  return { a, m, d, fecha: new Date(a, m - 1, d) }
}

export function mayuscula(texto) {
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/** "setiembre 2026" a partir de una fecha o de un código EC-2026-09. */
export function mes(isoOCodigo) {
  const [a, m] = isoOCodigo.startsWith('EC-') ? isoOCodigo.slice(3).split('-').map(Number) : isoOCodigo.split('-').map(Number)
  return `${MESES[m - 1]} ${a}`
}

/** "sábado 26/09" */
export function diaYFecha(iso) {
  const { d, m, fecha } = partes(iso)
  return `${DIAS[fecha.getDay()]} ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}`
}

/** "12/09" */
export function diaMes(iso) {
  const { d, m } = partes(iso)
  return `${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}`
}

export function primerNombre(nombre) {
  return (nombre || 'El cliente').split(' ')[0]
}

/** "24 %" o "34.49 %": la tasa redondeada para leerla de un vistazo. */
export function tasaSimple(valor) {
  return `${Number(Number(valor).toFixed(2))} %`
}

export function estadoSimple(estado) {
  return { PAGADO: 'Pagado', VENCIDO: 'Atrasado', PENDIENTE: 'Por pagar' }[estado] || estado
}

/** Frase principal de un estado de cuenta. */
export function fraseEstadoCuenta(ec, perspectiva, nombre) {
  const total = dinero(ec.total_a_pagar, ec.moneda)
  const hasta = diaYFecha(ec.fecha_pago)
  if (Number(ec.total_a_pagar) === 0) return 'Sin compras ni cuotas este mes'
  const vigente = ec.estado === 'PENDIENTE'
  if (perspectiva === 'cliente') return `${vigente ? 'Tienes' : 'Tenías'} que pagar ${total} hasta el ${hasta}`
  return `${primerNombre(nombre)} ${vigente ? 'tiene' : 'tenía'} que pagar ${total} hasta el ${hasta}`
}

/** Explicación de un atraso con su recargo. */
export function fraseAtraso(dias, recargo, totalHoy, moneda, perspectiva, nombre) {
  const sujeto = perspectiva === 'cliente' ? 'Te atrasaste' : `${primerNombre(nombre)} se atrasó`
  const debe = perspectiva === 'cliente' ? 'hoy debes' : 'hoy debe'
  return `${sujeto} ${dias} ${dias === 1 ? 'día' : 'días'}: por el atraso se sumaron ${dinero(recargo, moneda)}, así que ${debe} ${dinero(totalHoy, moneda)}.`
}

export function fraseDisponible(disponible, moneda, perspectiva) {
  return perspectiva === 'cliente'
    ? `Todavía puedes comprar al fiado hasta ${dinero(disponible, moneda)}.`
    : `Todavía le puedes fiar hasta ${dinero(disponible, moneda)}.`
}

