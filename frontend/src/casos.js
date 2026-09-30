// Escenarios precargados: los casos de prueba de docs/casos-de-prueba.md.

const tasa = (tipo, valor, periodo = 'ANUAL', capitalizacion = null) => ({ tipo, periodo, valor, capitalizacion })
const item = (descripcion, precio_lista, moneda = 'PEN') => ({
  descripcion, precio_lista, moneda, cantidad: '1', permite_pago_unico: true, permite_cuotas: true,
})
const venta = (fecha, items, modalidad = 'FIN_DE_MES', numero_cuotas = null, tipo_cambio = null) => ({
  tipo: 'VENTA', fecha, items, modalidad, numero_cuotas, tipo_cambio,
})
const pago = (fecha, cantidad_estados = 1, medio = 'EFECTIVO') => ({ tipo: 'PAGO', fecha, cantidad_estados, medio })

export const CASOS = {
  caso1: {
    nombre: 'Caso 1 · Bodega, tasa efectiva',
    descripcion: 'TEA 24 %, mora TEA 36 %, corte 20 y pago 26. Cuotas con gracia, compra después del corte, pago con mora, bloqueo por vencido, venta que excede la línea y pago anticipado.',
    condiciones: {
      moneda: 'PEN', limite_credito: '500.00', max_meses: 3, dia_corte: 20, dia_pago: 26,
      tasa_compensatoria: tasa('EFECTIVA', '24'), tasa_moratoria: tasa('EFECTIVA', '36'),
      bloquear_con_vencido: true,
    },
    eventos: [
      venta('2026-09-10', [item('Arroz 5 kg', '22.00')]),
      venta('2026-09-15', [item('Licuadora', '165.00')], 'CUOTAS', 3),
      venta('2026-09-22', [item('Arroz 5 kg', '22.00')]),
      venta('2026-09-28', [item('Gaseosa 3 L', '12.00')]),
      pago('2026-09-30'),
      venta('2026-10-16', [item('Televisor', '400.00')]),
      venta('2026-10-18', [item('Aceite 1 L', '9.50')]),
      pago('2026-10-24', 1, 'YAPE'),
      pago('2026-11-26'),
      pago('2026-12-26'),
    ],
    fecha_hasta: '2026-12-31',
  },
  caso2: {
    nombre: 'Caso 2 · Belleza, tasa nominal y dólares',
    descripcion: 'TNA 30 % c. mensual, mora TNA 36 % c. diaria, corte 25 y pago 5. Producto en dólares, compra en cuotas después del corte, compra el día del corte y cuota pagada con mora.',
    condiciones: {
      moneda: 'PEN', limite_credito: '800.00', max_meses: 6, dia_corte: 25, dia_pago: 5,
      tasa_compensatoria: tasa('NOMINAL', '30', 'ANUAL', 'MENSUAL'),
      tasa_moratoria: tasa('NOMINAL', '36', 'ANUAL', 'DIARIA'),
      bloquear_con_vencido: true,
    },
    eventos: [
      venta('2026-09-26', [item('Kit importado', '49.90', 'USD')], 'CUOTAS', 4, '3.520'),
      venta('2026-10-03', [item('Limpieza facial', '80.00')]),
      venta('2026-10-25', [item('Labial', '35.00')]),
      pago('2026-11-03'),
      pago('2026-12-15', 1, 'PLIN'),
    ],
    fecha_hasta: '2026-12-31',
  },
  vacio: {
    nombre: 'Escenario en blanco',
    descripcion: 'Condiciones por defecto, sin eventos.',
    condiciones: {
      moneda: 'PEN', limite_credito: '500.00', max_meses: 6, dia_corte: 20, dia_pago: 26,
      tasa_compensatoria: tasa('EFECTIVA', '24'), tasa_moratoria: tasa('EFECTIVA', '36'),
      bloquear_con_vencido: true,
    },
    eventos: [],
    fecha_hasta: new Date().toISOString().slice(0, 10),
  },
}

export function copiar(caso) {
  return JSON.parse(JSON.stringify(caso))
}
