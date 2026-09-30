<script setup>
import { dinero, fecha, tasa } from '../formato'

defineProps({ ec: { type: Object, required: true } })
const clase = { PENDIENTE: 'info', VENCIDO: 'error', PAGADO: '' }
</script>

<template>
  <article class="panel" :class="{ vencido: ec.estado === 'VENCIDO' }">
    <div class="entre">
      <div>
        <h3>{{ ec.codigo }}</h3>
        <p class="suave chico">
          Periodo {{ fecha(ec.periodo_desde) }} – {{ fecha(ec.fecha_corte) }} · pagar hasta el <strong>{{ fecha(ec.fecha_pago) }}</strong>
        </p>
      </div>
      <span class="fila">
        <span v-if="ec.pagado_con" class="suave chico">Pago {{ ec.pagado_con }}</span>
        <span class="etiqueta" :class="clase[ec.estado]">{{ ec.estado.toLowerCase() }}</span>
      </span>
    </div>

    <p class="chico suave">
      Compensatoria {{ ec.tasa_compensatoria }} (TEA {{ tasa(ec.tea_compensatoria) }}) ·
      Moratoria {{ ec.tasa_moratoria }} (TEA {{ tasa(ec.tea_moratoria) }})
    </p>

    <div class="tabla-scroll">
      <table>
        <thead>
          <tr><th>Fecha</th><th>Concepto</th><th class="num">Capital</th><th class="num">Días</th><th class="num">Tasa</th><th class="num">Interés</th><th class="num">Total</th></tr>
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
            <td colspan="2">Total a pagar</td>
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
      Intereses por mora: compensatorio {{ dinero(ec.deuda_al_dia.interes_compensatorio, ec.moneda) }}
      (TE{{ ec.deuda_al_dia.dias_mora }} {{ tasa(ec.deuda_al_dia.tasa_compensatoria) }}) +
      moratorio {{ dinero(ec.deuda_al_dia.interes_moratorio, ec.moneda) }}
      (TE{{ ec.deuda_al_dia.dias_mora }} {{ tasa(ec.deuda_al_dia.tasa_moratoria) }}).
      Debe hoy <strong>{{ dinero(ec.deuda_al_dia.total_a_pagar, ec.moneda) }}</strong>.
    </div>

    <div class="pie chico suave">
      <span>Línea al corte: límite {{ dinero(ec.linea.limite, ec.moneda) }} · usado {{ dinero(ec.linea.usado, ec.moneda) }} · disponible {{ dinero(ec.linea.disponible, ec.moneda) }}</span>
      <span v-for="v in ec.vencidos_anteriores" :key="v.codigo">
        Informativo: {{ v.codigo }} vencido el {{ fecha(v.fecha_pago) }} ({{ dinero(v.exigible, ec.moneda) }}, {{ v.dias_atraso }} días de atraso al corte)
      </span>
    </div>
  </article>
</template>

<style scoped>
.vencido { border-color: #efc2bf; }
.pie { display: flex; flex-direction: column; gap: 2px; }
</style>
