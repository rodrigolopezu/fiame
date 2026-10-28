<script setup>
import { computed, ref } from 'vue'
import { dinero, fecha, tasa, TIPOS_EVENTO } from '../formato'
import EstadoCuentaDetalle from './EstadoCuentaDetalle.vue'
import PagoDetalle from './PagoDetalle.vue'
import VentaDetalle from './VentaDetalle.vue'

const props = defineProps({ resultado: { type: Object, required: true } })
const vista = ref('bitacora')
const ocultarVacios = ref(true)

const r = computed(() => props.resultado)
const estados = computed(() =>
  [...r.value.estados_cuenta].reverse().filter((ec) => !ocultarVacios.value || ec.lineas.length),
)
const vencidos = computed(() => r.value.estados_cuenta.filter((ec) => ec.estado === 'VENCIDO'))
</script>

<template>
  <div class="resultados">
    <section class="panel">
      <div class="entre">
        <h2>Situación al {{ fecha(r.fecha_hasta) }}</h2>
        <span v-if="vencidos.length" class="etiqueta error">{{ vencidos.length }} estado(s) de cuenta vencido(s)</span>
      </div>
      <div class="tarjetas">
        <div class="tarjeta">
          <div class="rotulo">Crédito disponible</div>
          <div class="valor">{{ dinero(r.linea.disponible, r.moneda) }}</div>
          <div class="chico suave">usado {{ dinero(r.linea.usado, r.moneda) }} de {{ dinero(r.linea.limite, r.moneda) }}</div>
        </div>
        <div class="tarjeta">
          <div class="rotulo">Compensatoria · {{ r.tasa_compensatoria.descripcion }}</div>
          <div class="valor">{{ tasa(r.tasa_compensatoria.tea) }}</div>
          <div class="chico suave">TEA · TEM {{ tasa(r.tasa_compensatoria.tem) }}</div>
        </div>
        <div class="tarjeta">
          <div class="rotulo">Moratoria · {{ r.tasa_moratoria.descripcion }}</div>
          <div class="valor">{{ tasa(r.tasa_moratoria.tea) }}</div>
          <div class="chico suave">TEA · TEM {{ tasa(r.tasa_moratoria.tem) }}</div>
        </div>
        <div class="tarjeta">
          <div class="rotulo">Movimientos</div>
          <div class="valor">{{ r.ventas.length }} ventas · {{ r.pagos.length }} pagos</div>
          <div class="chico suave">{{ r.estados_cuenta.length }} cortes generados</div>
        </div>
      </div>
    </section>

    <div class="pestanas">
      <button :class="{ activa: vista === 'bitacora' }" @click="vista = 'bitacora'">Bitácora</button>
      <button :class="{ activa: vista === 'ventas' }" @click="vista = 'ventas'">Ventas y cronogramas ({{ r.ventas.length }})</button>
      <button :class="{ activa: vista === 'estados' }" @click="vista = 'estados'">Estados de cuenta ({{ r.estados_cuenta.length }})</button>
      <button :class="{ activa: vista === 'pagos' }" @click="vista = 'pagos'">Pagos ({{ r.pagos.length }})</button>
    </div>

    <section v-if="vista === 'bitacora'" class="panel">
      <div class="tabla-scroll">
        <table>
          <thead><tr><th>Fecha</th><th>Operación</th><th>Resultado</th><th>Detalle</th><th class="num">Disponible</th></tr></thead>
          <tbody>
            <tr v-for="(b, n) in r.bitacora" :key="n" :class="{ corte: b.tipo === 'CORTE' }">
              <td>{{ fecha(b.fecha) }}</td>
              <td>{{ TIPOS_EVENTO[b.tipo] }}</td>
              <td><span class="etiqueta" :class="b.resultado === 'OK' ? (b.tipo === 'CORTE' ? 'info' : '') : 'error'">{{ b.resultado === 'OK' ? 'OK' : 'Rechazado' }}</span></td>
              <td>{{ b.mensaje }}</td>
              <td class="num">{{ dinero(b.linea.disponible, r.moneda) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <template v-else-if="vista === 'ventas'">
      <p v-if="!r.ventas.length" class="panel suave">No hay ventas registradas.</p>
      <VentaDetalle v-for="v in r.ventas" :key="v.numero" :venta="v" modo="detallada" />
    </template>

    <template v-else-if="vista === 'estados'">
      <label class="check"><input v-model="ocultarVacios" type="checkbox" /> Ocultar estados de cuenta sin compras ni cuotas</label>
      <p v-if="!estados.length" class="panel suave">No hay estados de cuenta para mostrar.</p>
      <EstadoCuentaDetalle v-for="ec in estados" :key="ec.codigo" :ec="ec" modo="detallada" />
    </template>

    <template v-else>
      <p v-if="!r.pagos.length" class="panel suave">No hay pagos registrados.</p>
      <PagoDetalle v-for="p in r.pagos" :key="p.numero" :pago="p" :moneda="r.moneda" modo="detallada" />
    </template>
  </div>
</template>

<style scoped>
.resultados { display: flex; flex-direction: column; gap: 12px; }
tr.corte td { background: var(--panel-suave); }
</style>
