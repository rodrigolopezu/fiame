<script setup>
import { dinero, fecha, MEDIOS, tasa } from '../formato'
import { diaYFecha, mes } from '../lenguaje'
import { usarSimple } from '../vista'
import Termino from './Termino.vue'

const props = defineProps({
  pago: { type: Object, required: true },
  moneda: { type: String, required: true },
  modo: { type: String, default: null }, // fuerza 'simple' o 'detallada'
})
const simple = usarSimple(props)
const medio = (m) => Object.fromEntries(MEDIOS)[m] || m
</script>

<template>
  <!-- Vista simple: qué se pagó y qué cubre -->
  <article v-if="simple" class="panel" :class="{ anulado: pago.estado === 'ANULADO' }">
    <div class="entre">
      <div>
        <p class="suave chico">Pago {{ pago.numero }} · {{ diaYFecha(pago.fecha) }} · {{ medio(pago.medio) }}<span v-if="pago.cliente"> · {{ pago.cliente }}</span></p>
        <h3 class="frase">Se pagó {{ dinero(pago.total, moneda) }}</h3>
      </div>
      <span class="fila">
        <slot name="acciones" />
        <span v-if="pago.estado === 'ANULADO'" class="etiqueta error">Anulado</span>
      </span>
    </div>
    <ul class="lista">
      <li v-for="d in pago.detalle" :key="d.estado_cuenta">
        <span>
          Cuenta de {{ mes(d.estado_cuenta) }}
          <span v-if="d.dias_mora" class="suave"> · incluye {{ dinero(d.recargo_mora, moneda) }} por {{ d.dias_mora }} {{ d.dias_mora === 1 ? 'día' : 'días' }} de atraso</span>
        </span>
        <strong>{{ dinero(d.total, moneda) }}</strong>
      </li>
    </ul>
    <p v-if="pago.estado === 'ANULADO'" class="aviso">Anulado: {{ pago.motivo_anulacion }}</p>
    <p v-else class="chico suave">Con este pago vuelven a quedar disponibles {{ dinero(pago.linea_liberada, moneda) }} de crédito.</p>
  </article>

  <!-- Vista detallada: desglose completo -->
  <article v-else class="panel" :class="{ anulado: pago.estado === 'ANULADO' }">
    <div class="entre">
      <h3>Pago {{ pago.numero }} · {{ fecha(pago.fecha) }}<span v-if="pago.cliente" class="suave"> · {{ pago.cliente }}</span></h3>
      <span class="fila">
        <slot name="acciones" />
        <span v-if="pago.estado === 'ANULADO'" class="etiqueta error">anulado</span>
        <span class="etiqueta neutra">{{ pago.medio.toLowerCase() }}</span>
        <strong>{{ dinero(pago.total, moneda) }}</strong>
      </span>
    </div>
    <div class="tabla-scroll">
      <table>
        <thead>
          <tr>
            <th>Estado de cuenta</th><th class="num"><Termino clave="exigible">Exigible</Termino></th><th class="num">Días mora</th>
            <th class="num"><Termino clave="compensatorioMora">Comp. por mora</Termino></th><th class="num"><Termino clave="moratorio">Moratorio</Termino></th>
            <th class="num">Mora</th><th class="num">Interés</th><th class="num">Capital</th><th class="num">Total</th>
            <th class="num"><Termino clave="liberaLinea">Libera línea</Termino></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in pago.detalle" :key="d.estado_cuenta">
            <td>{{ d.estado_cuenta }} <span class="suave chico">vencía {{ fecha(d.fecha_pago_pactada) }}</span></td>
            <td class="num">{{ dinero(d.exigible, moneda) }}</td>
            <td class="num">{{ d.dias_mora }}</td>
            <td class="num">{{ dinero(d.interes_compensatorio_mora, moneda) }}<br /><span class="suave chico" v-if="d.dias_mora">{{ tasa(d.tasa_compensatoria_mora) }}</span></td>
            <td class="num">{{ dinero(d.interes_moratorio, moneda) }}<br /><span class="suave chico" v-if="d.dias_mora">{{ tasa(d.tasa_moratoria) }}</span></td>
            <td class="num">{{ dinero(d.mora, moneda) }}</td>
            <td class="num">{{ dinero(d.interes, moneda) }}</td>
            <td class="num">{{ dinero(d.capital, moneda) }}</td>
            <td class="num"><strong>{{ dinero(d.total, moneda) }}</strong></td>
            <td class="num">{{ dinero(d.libera_linea, moneda) }}</td>
          </tr>
        </tbody>
        <tfoot v-if="pago.detalle.length > 1">
          <tr>
            <td colspan="5">Total</td>
            <td class="num">{{ dinero(pago.total_mora, moneda) }}</td>
            <td class="num">{{ dinero(pago.total_interes, moneda) }}</td>
            <td class="num">{{ dinero(pago.total_capital, moneda) }}</td>
            <td class="num">{{ dinero(pago.total, moneda) }}</td>
            <td class="num">{{ dinero(pago.linea_liberada, moneda) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
    <p v-if="pago.estado === 'ANULADO'" class="aviso">Anulado: {{ pago.motivo_anulacion }}</p>
    <p class="chico suave">
      <Termino clave="imputacion">Desglose según el orden de imputación del Anexo A</Termino>: mora {{ dinero(pago.total_mora, moneda) }} →
      interés compensatorio {{ dinero(pago.total_interes, moneda) }} → capital {{ dinero(pago.total_capital, moneda) }}.
    </p>
  </article>
</template>

<style scoped>
.anulado { opacity: 0.7; }
.frase { font-size: 16px; margin-top: 2px; }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.lista li { display: flex; justify-content: space-between; gap: 12px; padding: 7px 0; border-bottom: 1px solid var(--linea); font-variant-numeric: tabular-nums; }
.lista li:last-child { border-bottom: none; }
</style>
