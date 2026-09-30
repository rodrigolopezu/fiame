<script setup>
import { dinero, fecha, tasa } from '../formato'

defineProps({ pago: { type: Object, required: true }, moneda: { type: String, required: true } })
</script>

<template>
  <article class="panel">
    <div class="entre">
      <h3>Pago {{ pago.numero }} · {{ fecha(pago.fecha) }}</h3>
      <span class="fila">
        <span class="etiqueta neutra">{{ pago.medio.toLowerCase() }}</span>
        <strong>{{ dinero(pago.total, moneda) }}</strong>
      </span>
    </div>
    <div class="tabla-scroll">
      <table>
        <thead>
          <tr>
            <th>Estado de cuenta</th><th class="num">Exigible</th><th class="num">Días mora</th>
            <th class="num">Comp. por mora</th><th class="num">Moratorio</th>
            <th class="num">Mora</th><th class="num">Interés</th><th class="num">Capital</th><th class="num">Total</th><th class="num">Libera línea</th>
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
    <p class="chico suave">
      Desglose según el orden de imputación del Anexo A: mora {{ dinero(pago.total_mora, moneda) }} →
      interés compensatorio {{ dinero(pago.total_interes, moneda) }} → capital {{ dinero(pago.total_capital, moneda) }}.
    </p>
  </article>
</template>
