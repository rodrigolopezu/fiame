<script setup>
import { dinero, fecha, tasa } from '../formato'
import {
  diaMes, estadoSimple, fraseAtraso, fraseEstadoCuenta, mayuscula, mes,
} from '../lenguaje'
import { usarSimple } from '../vista'
import Termino from './Termino.vue'

const props = defineProps({
  ec: { type: Object, required: true },
  modo: { type: String, default: null }, // fuerza 'simple' o 'detallada'
  perspectiva: { type: String, default: 'vendedor' }, // 'vendedor' | 'cliente'
  nombre: { type: String, default: null }, // nombre del cliente para la vista simple del vendedor
})
const simple = usarSimple(props)
const clase = { PENDIENTE: 'info', VENCIDO: 'error', PAGADO: '' }
const nombreCliente = () => props.nombre || props.ec.cliente
</script>

<template>
  <!-- Vista simple: lo que hay que pagar, en palabras de todos los días -->
  <article v-if="simple" class="panel" :class="{ vencido: ec.estado === 'VENCIDO' }">
    <div class="entre">
      <div>
        <p class="suave chico">{{ mayuscula(mes(ec.fecha_corte)) }} · compras del {{ diaMes(ec.periodo_desde) }} al {{ diaMes(ec.fecha_corte) }}<span v-if="ec.cliente"> · {{ ec.cliente }}</span></p>
        <h3 class="frase">{{ fraseEstadoCuenta(ec, perspectiva, nombreCliente()) }}</h3>
      </div>
      <span class="fila">
        <slot name="acciones" />
        <span v-if="Number(ec.total_a_pagar) > 0" class="etiqueta" :class="clase[ec.estado]">{{ estadoSimple(ec.estado) }}</span>
      </span>
    </div>

    <ul v-if="ec.lineas.length" class="lista">
      <li v-for="(l, n) in ec.lineas" :key="n">
        <span>{{ l.descripcion }}<span class="suave"> · {{ l.cuota ? `cuota ${l.cuota.replace('/', ' de ')}` : `compra del ${diaMes(l.fecha)}` }}</span></span>
        <strong>{{ dinero(l.total, ec.moneda) }}</strong>
      </li>
    </ul>

    <p v-if="Number(ec.total_interes) > 0" class="chico suave">
      De esos {{ dinero(ec.total_a_pagar, ec.moneda) }}, {{ dinero(ec.total_capital, ec.moneda) }} es el precio de los productos
      y {{ dinero(ec.total_interes, ec.moneda) }} es el interés por comprar al crédito.
    </p>

    <p v-if="ec.deuda_al_dia" class="aviso">
      {{ fraseAtraso(ec.deuda_al_dia.dias_mora, ec.deuda_al_dia.recargo, ec.deuda_al_dia.total_a_pagar, ec.moneda, perspectiva, nombreCliente()) }}
    </p>
    <p v-for="v in ec.vencidos_anteriores" :key="v.codigo" class="chico suave">
      Además, el pago de {{ mes(v.codigo) }} ({{ dinero(v.exigible, ec.moneda) }}) seguía pendiente al cierre de este mes.
    </p>
  </article>

  <!-- Vista detallada: todas las cifras y términos financieros -->
  <article v-else class="panel" :class="{ vencido: ec.estado === 'VENCIDO' }">
    <div class="entre">
      <div>
        <h3>{{ ec.codigo }}<span v-if="ec.cliente" class="suave"> · {{ ec.cliente }}</span></h3>
        <p class="suave chico">
          Periodo {{ fecha(ec.periodo_desde) }} – {{ fecha(ec.fecha_corte) }} (<Termino clave="corte">corte</Termino>) · pagar hasta el <strong>{{ fecha(ec.fecha_pago) }}</strong>
        </p>
      </div>
      <span class="fila">
        <slot name="acciones" />
        <span v-if="ec.pagado_con" class="suave chico">Pago {{ ec.pagado_con }}</span>
        <span class="etiqueta" :class="clase[ec.estado]">{{ ec.estado.toLowerCase() }}</span>
      </span>
    </div>

    <p class="chico suave">
      <Termino clave="compensatorio">Compensatoria</Termino> {{ ec.tasa_compensatoria }} (<Termino clave="tea">TEA</Termino> {{ tasa(ec.tea_compensatoria) }}) ·
      <Termino clave="moratorio">Moratoria</Termino> {{ ec.tasa_moratoria }} (TEA {{ tasa(ec.tea_moratoria) }})
    </p>

    <div class="tabla-scroll">
      <table>
        <thead>
          <tr>
            <th>Fecha</th><th>Concepto</th>
            <th class="num"><Termino clave="capital">Capital</Termino></th><th class="num">Días</th>
            <th class="num"><Termino clave="tasaPlazo">Tasa</Termino></th>
            <th class="num"><Termino clave="compensatorio">Interés</Termino></th><th class="num">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!ec.lineas.length"><td colspan="7" class="suave">Sin compras ni cuotas en el periodo.</td></tr>
          <tr v-for="(l, n) in ec.lineas" :key="n">
            <td>{{ fecha(l.fecha) }}</td>
            <td>{{ l.descripcion }}<span v-if="l.cuota" class="suave"> · cuota {{ l.cuota }}</span> <span class="suave chico">(venta {{ l.venta }})</span></td>
            <td class="num">{{ dinero(l.capital, ec.moneda) }}</td>
            <td class="num">{{ l.dias ?? '—' }}</td>
            <td class="num">{{ l.cuota ? `TEM ${tasa(l.tasa)}` : tasa(l.tasa) }}</td>
            <td class="num">{{ dinero(l.interes, ec.moneda) }}</td>
            <td class="num">{{ dinero(l.total, ec.moneda) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td colspan="2"><Termino clave="exigible">Total a pagar</Termino></td>
            <td class="num">{{ dinero(ec.total_capital, ec.moneda) }}</td>
            <td></td><td></td>
            <td class="num">{{ dinero(ec.total_interes, ec.moneda) }}</td>
            <td class="num">{{ dinero(ec.total_a_pagar, ec.moneda) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <div v-if="ec.deuda_al_dia" class="aviso">
      <strong>Vencido: {{ ec.deuda_al_dia.dias_mora }} días de atraso al {{ fecha(ec.deuda_al_dia.fecha) }}.</strong>
      Intereses por mora: <Termino clave="compensatorioMora">compensatorio</Termino> {{ dinero(ec.deuda_al_dia.interes_compensatorio, ec.moneda) }}
      (TE{{ ec.deuda_al_dia.dias_mora }} {{ tasa(ec.deuda_al_dia.tasa_compensatoria) }}) +
      <Termino clave="moratorio">moratorio</Termino> {{ dinero(ec.deuda_al_dia.interes_moratorio, ec.moneda) }}
      (TE{{ ec.deuda_al_dia.dias_mora }} {{ tasa(ec.deuda_al_dia.tasa_moratoria) }}).
      Debe hoy <strong>{{ dinero(ec.deuda_al_dia.total_a_pagar, ec.moneda) }}</strong>.
    </div>

    <div class="pie chico suave">
      <span><Termino clave="linea">Línea</Termino> al corte: límite {{ dinero(ec.linea.limite, ec.moneda) }} · usado {{ dinero(ec.linea.usado, ec.moneda) }} · disponible {{ dinero(ec.linea.disponible, ec.moneda) }}</span>
      <span v-for="v in ec.vencidos_anteriores" :key="v.codigo">
        Informativo: {{ v.codigo }} vencido el {{ fecha(v.fecha_pago) }} ({{ dinero(v.exigible, ec.moneda) }}, {{ v.dias_atraso }} días de atraso al corte)
      </span>
    </div>
  </article>
</template>

<style scoped>
.vencido { border-color: var(--error-borde); }
.pie { display: flex; flex-direction: column; gap: 2px; }
.frase { font-size: 16px; margin-top: 2px; }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.lista li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--linea); font-variant-numeric: tabular-nums; }
.lista li:last-child { border-bottom: none; }
</style>
