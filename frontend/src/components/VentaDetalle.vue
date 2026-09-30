<script setup>
import { dinero, fecha, tasa } from '../formato'

defineProps({ venta: { type: Object, required: true } })
const clase = { VIGENTE: 'info', PAGADA: '', ANULADA: 'neutra' }
</script>

<template>
  <article class="panel">
    <div class="entre">
      <h3>Venta {{ venta.numero }} · {{ fecha(venta.fecha) }}</h3>
      <span class="fila">
        <span class="etiqueta neutra">{{ venta.modalidad === 'CUOTAS' ? `${venta.numero_cuotas} cuotas` : 'Fin de mes' }}</span>
        <span class="etiqueta" :class="clase[venta.estado]">{{ venta.estado.toLowerCase() }}</span>
      </span>
    </div>

    <div class="tabla-scroll">
      <table>
        <thead><tr><th>Producto</th><th class="num">Cant.</th><th class="num">Precio lista</th><th class="num">Subtotal</th></tr></thead>
        <tbody>
          <tr v-for="(i, n) in venta.items" :key="n">
            <td>{{ i.descripcion }}</td>
            <td class="num">{{ i.cantidad }}</td>
            <td class="num">{{ dinero(i.precio_lista, i.moneda) }}</td>
            <td class="num">{{ dinero(i.subtotal, venta.moneda) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <dl class="datos">
      <div><dt>Capital (consume línea)</dt><dd>{{ dinero(venta.capital, venta.moneda) }}</dd></div>
      <div v-if="venta.tipo_cambio"><dt>Tipo de cambio</dt><dd>{{ venta.tipo_cambio }}</dd></div>
      <div><dt>Tasa pactada</dt><dd>{{ venta.tasa_compensatoria }}</dd></div>
      <div><dt>Corte / pago del ciclo</dt><dd>{{ fecha(venta.fecha_corte) }} · {{ fecha(venta.fecha_pago) }}</dd></div>
      <div><dt>{{ venta.modalidad === 'CUOTAS' ? 'Días de gracia' : 'Días hasta el pago' }}</dt><dd>{{ venta.dias }}</dd></div>
      <div><dt>TE{{ venta.dias }} (tasa del plazo)</dt><dd>{{ tasa(venta.tasa_periodo) }}</dd></div>
      <div><dt>{{ venta.modalidad === 'CUOTAS' ? 'Interés de la gracia' : 'Interés compensatorio' }}</dt><dd>{{ dinero(venta.interes, venta.moneda) }}</dd></div>
      <div><dt>{{ venta.modalidad === 'CUOTAS' ? 'Capital capitalizado' : 'Total a pagar' }}</dt><dd><strong>{{ dinero(venta.total, venta.moneda) }}</strong></dd></div>
      <div v-if="venta.tem"><dt>TEM</dt><dd>{{ tasa(venta.tem) }}</dd></div>
      <div v-if="venta.estado_cuenta"><dt>Cobrada en</dt><dd>{{ venta.estado_cuenta }}</dd></div>
    </dl>

    <div v-if="venta.cuotas.length" class="tabla-scroll">
      <h4>Cronograma · método francés vencido ordinario</h4>
      <table>
        <thead>
          <tr>
            <th>N.°</th><th>Vence</th><th class="num">Saldo inicial</th><th class="num">Interés</th><th class="num">Cuota</th>
            <th class="num">Amortización</th><th class="num">Saldo final</th><th class="num">Libera línea</th><th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in venta.cuotas" :key="c.numero">
            <td>{{ c.numero }}</td>
            <td>{{ fecha(c.fecha_vencimiento) }}</td>
            <td class="num">{{ dinero(c.saldo_inicial, venta.moneda) }}</td>
            <td class="num">{{ dinero(c.interes, venta.moneda) }}</td>
            <td class="num"><strong>{{ dinero(c.cuota, venta.moneda) }}</strong></td>
            <td class="num">{{ dinero(c.amortizacion, venta.moneda) }}</td>
            <td class="num">{{ dinero(c.saldo_final, venta.moneda) }}</td>
            <td class="num">{{ dinero(c.libera_linea, venta.moneda) }}</td>
            <td><span class="etiqueta" :class="c.estado === 'PAGADA' ? '' : 'neutra'">{{ c.estado.toLowerCase() }}</span> <span class="suave chico">{{ c.estado_cuenta }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<style scoped>
.datos { margin: 0; display: grid; gap: 8px 16px; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); }
dt { font-size: 12px; color: var(--suave); }
dd { margin: 0; font-variant-numeric: tabular-nums; }
</style>
