<script setup>
import { dinero, fecha, tasa } from '../formato'
import { diaMes, diaYFecha } from '../lenguaje'
import { usarSimple } from '../vista'
import Termino from './Termino.vue'

const props = defineProps({
  venta: { type: Object, required: true },
  modo: { type: String, default: null }, // fuerza 'simple' o 'detallada'
})
const simple = usarSimple(props)
const clase = { VIGENTE: 'info', PAGADA: '', ANULADA: 'neutra' }
const ESTADO_SIMPLE = { VIGENTE: 'Por pagar', PAGADA: 'Pagada', ANULADA: 'Anulada' }
</script>

<template>
  <!-- Vista simple: qué se compró y cómo se paga -->
  <article v-if="simple" class="panel">
    <div class="entre">
      <div>
        <p class="suave chico">{{ venta.numero ? `Venta ${venta.numero} · ` : '' }}{{ diaYFecha(venta.fecha) }}<span v-if="venta.cliente"> · {{ venta.cliente }}</span></p>
        <h3 class="frase">{{ venta.items.map((i) => i.descripcion).join(', ') }}</h3>
      </div>
      <span class="fila">
        <slot name="acciones" />
        <span class="etiqueta" :class="clase[venta.estado]">{{ ESTADO_SIMPLE[venta.estado] }}</span>
      </span>
    </div>

    <ul class="lista">
      <li v-for="(i, n) in venta.items" :key="n">
        <span>{{ Number(i.cantidad) }} × {{ i.descripcion }}<span v-if="i.moneda !== venta.moneda" class="suave chico"> ({{ dinero(i.precio_lista, i.moneda) }} c/u, al cambio de {{ venta.tipo_cambio }})</span></span>
        <strong>{{ dinero(i.subtotal, venta.moneda) }}</strong>
      </li>
    </ul>

    <p v-if="venta.modalidad === 'FIN_DE_MES'">
      Se paga de una sola vez: <strong>{{ dinero(venta.total, venta.moneda) }}</strong> hasta el {{ diaYFecha(venta.fecha_pago) }}.
      <span class="suave">Incluye {{ dinero(venta.interes, venta.moneda) }} de interés por {{ venta.dias }} días de crédito.</span>
    </p>
    <template v-else>
      <p>
        Se paga en <strong>{{ venta.numero_cuotas }} cuotas de {{ dinero(venta.cuotas[0].cuota, venta.moneda) }}</strong>, la primera el {{ diaYFecha(venta.cuotas[0].fecha_vencimiento) }}.
        <span class="suave">Hasta el {{ diaMes(venta.fecha_pago) }} no se paga nada, pero esos {{ venta.dias }} días suman {{ dinero(venta.interes, venta.moneda) }} de interés, que se reparten en las cuotas.</span>
      </p>
      <div class="tabla-scroll">
        <table>
          <thead><tr><th>Cuota</th><th>Vence</th><th class="num">Monto</th><th>Estado</th></tr></thead>
          <tbody>
            <tr v-for="c in venta.cuotas" :key="c.numero">
              <td>{{ c.numero }} de {{ venta.numero_cuotas }}</td>
              <td>{{ diaYFecha(c.fecha_vencimiento) }}</td>
              <td class="num"><strong>{{ dinero(c.cuota, venta.moneda) }}</strong></td>
              <td><span class="etiqueta" :class="c.estado === 'PAGADA' ? '' : 'neutra'">{{ c.estado === 'PAGADA' ? 'Pagada' : 'Pendiente' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </article>

  <!-- Vista detallada: cálculo completo -->
  <article v-else class="panel">
    <div class="entre">
      <h3>Venta {{ venta.numero || '' }} · {{ fecha(venta.fecha) }}<span v-if="venta.cliente" class="suave"> · {{ venta.cliente }}</span></h3>
      <span class="fila">
        <slot name="acciones" />
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
      <div><dt><Termino clave="capital">Capital</Termino> (consume línea)</dt><dd>{{ dinero(venta.capital, venta.moneda) }}</dd></div>
      <div v-if="venta.tipo_cambio"><dt><Termino clave="tipoCambio">Tipo de cambio</Termino></dt><dd>{{ venta.tipo_cambio }}</dd></div>
      <div><dt>Tasa pactada</dt><dd>{{ venta.tasa_compensatoria }}</dd></div>
      <div><dt><Termino clave="corte">Corte</Termino> / pago del ciclo</dt><dd>{{ fecha(venta.fecha_corte) }} · {{ fecha(venta.fecha_pago) }}</dd></div>
      <div><dt><template v-if="venta.modalidad === 'CUOTAS'"><Termino clave="gracia">Días de gracia</Termino></template><template v-else>Días hasta el pago</template></dt><dd>{{ venta.dias }}</dd></div>
      <div><dt><Termino clave="tasaPlazo">TE{{ venta.dias }}</Termino> (tasa del plazo)</dt><dd>{{ tasa(venta.tasa_periodo) }}</dd></div>
      <div><dt>{{ venta.modalidad === 'CUOTAS' ? 'Interés de la gracia' : 'Interés compensatorio' }}</dt><dd>{{ dinero(venta.interes, venta.moneda) }}</dd></div>
      <div><dt><template v-if="venta.modalidad === 'CUOTAS'"><Termino clave="capitalizado">Capital capitalizado</Termino></template><template v-else>Total a pagar</template></dt><dd><strong>{{ dinero(venta.total, venta.moneda) }}</strong></dd></div>
      <div v-if="venta.tem"><dt><Termino clave="tem">TEM</Termino></dt><dd>{{ tasa(venta.tem) }}</dd></div>
      <div v-if="venta.estado_cuenta"><dt>Cobrada en</dt><dd>{{ venta.estado_cuenta }}</dd></div>
    </dl>

    <div v-if="venta.cuotas.length" class="tabla-scroll">
      <h4>Cronograma · <Termino clave="frances">método francés vencido ordinario</Termino></h4>
      <table>
        <thead>
          <tr>
            <th>N.°</th><th>Vence</th><th class="num"><Termino clave="saldo">Saldo inicial</Termino></th><th class="num">Interés</th><th class="num">Cuota</th>
            <th class="num"><Termino clave="amortizacion">Amortización</Termino></th><th class="num">Saldo final</th>
            <th class="num"><Termino clave="liberaLinea">Libera línea</Termino></th><th>Estado</th>
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
.frase { font-size: 16px; margin-top: 2px; }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.lista li { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--linea); font-variant-numeric: tabular-nums; }
.lista li:last-child { border-bottom: none; }
</style>
