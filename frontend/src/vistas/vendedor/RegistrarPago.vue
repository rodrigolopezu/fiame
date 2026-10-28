<script setup>
// Registrar el pago de uno o varios estados de cuenta, completos y del más antiguo al
// más reciente. El monto lo calcula el sistema a la fecha de hoy, con la mora si corresponde.
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import PagoDetalle from '../../components/PagoDetalle.vue'
import Termino from '../../components/Termino.vue'
import { dinero, fecha, MEDIOS, tasa } from '../../formato'
import { diaYFecha, mes, primerNombre } from '../../lenguaje'
import { vista } from '../../vista'

const ruta = useRoute()
const clientes = ref([])
const clienteId = ref(ruta.query.cliente ? Number(ruta.query.cliente) : null)
const cantidad = ref(1)
const medio = ref('EFECTIVO')
const liq = ref(null)
const error = ref('')
const constancia = ref(null)
const guardando = ref(false)

onMounted(async () => {
  try {
    clientes.value = (await vendedor.clientes()).filter((c) => Number(c.deuda_pendiente) > 0)
  } catch (e) { error.value = e.message }
})

const cliente = computed(() => clientes.value.find((c) => c.id === clienteId.value))

async function cargarLiquidacion() {
  liq.value = null
  error.value = ''
  if (!clienteId.value) return
  try { liq.value = await vendedor.liquidacion(clienteId.value, cantidad.value) } catch (e) { error.value = e.message }
}
watch(clienteId, () => { cantidad.value = 1; constancia.value = null; cargarLiquidacion() }, { immediate: true })
watch(cantidad, cargarLiquidacion)

function imprimir() {
  window.print()
}

async function registrar() {
  guardando.value = true
  error.value = ''
  try {
    constancia.value = await vendedor.registrarPago({ cliente_id: clienteId.value, cantidad_estados: cantidad.value, medio: medio.value })
    liq.value = null
    clientes.value = (await vendedor.clientes()).filter((c) => Number(c.deuda_pendiente) > 0 || c.id === clienteId.value)
  } catch (e) {
    error.value = e.message
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <h1>Registrar pago</h1>
    <p class="suave">{{ vista.simple ? 'Se cobra la cuenta completa de cada mes, empezando por la más antigua.' : 'Los estados de cuenta se pagan completos (no hay pagos parciales) y en orden, del más antiguo al más reciente.' }}</p>

    <section class="panel">
      <div class="grilla">
        <label class="campo">
          <span>Cliente <Ayuda texto="Solo aparecen los clientes con estados de cuenta pendientes." /></span>
          <select v-model="clienteId">
            <option :value="null" disabled>Elegir cliente…</option>
            <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nombre }} · debe {{ dinero(c.deuda_pendiente, c.moneda) }}</option>
          </select>
        </label>
        <label v-if="liq" class="campo">
          <span>{{ vista.simple ? 'Meses a pagar' : 'Estados de cuenta a pagar' }} <Ayuda texto="Cuántos estados de cuenta pendientes paga, empezando por el más antiguo." /></span>
          <select v-model.number="cantidad">
            <option v-for="n in liq.pendientes" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
        <label v-if="liq" class="campo">
          <span>Medio de pago <Ayuda texto="Solo informativo: el pago se recibe fuera del sistema." /></span>
          <select v-model="medio"><option v-for="[v, n] in MEDIOS" :key="v" :value="v">{{ n }}</option></select>
        </label>
      </div>
    </section>

    <p v-if="error" class="aviso">{{ error }}</p>

    <section v-if="liq && vista.simple" class="panel">
      <h2>{{ primerNombre(cliente?.nombre) }} debe pagar hoy {{ dinero(liq.total, cliente?.moneda) }}</h2>
      <ul class="lista">
        <li v-for="d in liq.detalle" :key="d.estado_cuenta">
          <span>
            Cuenta de {{ mes(d.estado_cuenta) }}, vencía el {{ diaYFecha(d.fecha_pago_pactada) }}
            <span v-if="d.dias_mora" class="error-texto"> · {{ dinero(d.exigible, cliente?.moneda) }} + {{ dinero(d.recargo_mora, cliente?.moneda) }} por {{ d.dias_mora }} días de atraso</span>
          </span>
          <strong>{{ dinero(d.total, cliente?.moneda) }}</strong>
        </li>
      </ul>
      <div class="total">
        <span class="chico suave">Al pagar, vuelven a quedar disponibles {{ dinero(liq.linea_liberada, cliente?.moneda) }} de crédito.</span>
        <button class="primario grande" :disabled="guardando" @click="registrar">
          {{ guardando ? 'Registrando…' : `Registrar pago de ${dinero(liq.total, cliente?.moneda)}` }}
        </button>
      </div>
    </section>

    <section v-else-if="liq" class="panel">
      <h2>Liquidación al {{ fecha(liq.fecha) }}</h2>
      <div class="tabla-scroll">
        <table>
          <thead>
            <tr><th>Estado de cuenta</th><th class="num"><Termino clave="exigible">Exigible</Termino></th><th class="num">Días de mora</th><th class="num"><Termino clave="compensatorioMora">Comp. por mora</Termino></th><th class="num"><Termino clave="moratorio">Moratorio</Termino></th><th class="num">Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in liq.detalle" :key="d.estado_cuenta">
              <td>{{ d.estado_cuenta }} <span class="suave chico">vence {{ fecha(d.fecha_pago_pactada) }}</span></td>
              <td class="num">{{ dinero(d.exigible, cliente?.moneda) }}</td>
              <td class="num"><span :class="{ 'etiqueta error': d.dias_mora }">{{ d.dias_mora }}</span></td>
              <td class="num">{{ dinero(d.interes_compensatorio_mora, cliente?.moneda) }}<div v-if="d.dias_mora" class="chico suave">{{ tasa(d.tasa_compensatoria_mora) }}</div></td>
              <td class="num">{{ dinero(d.interes_moratorio, cliente?.moneda) }}<div v-if="d.dias_mora" class="chico suave">{{ tasa(d.tasa_moratoria) }}</div></td>
              <td class="num"><strong>{{ dinero(d.total, cliente?.moneda) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="total">
        <div class="desglose chico">
          <Termino clave="imputacion">Desglose</Termino>
          <span>Mora <strong>{{ dinero(liq.total_mora, cliente?.moneda) }}</strong></span>
          <span>→ Interés compensatorio <strong>{{ dinero(liq.total_interes, cliente?.moneda) }}</strong></span>
          <span>→ Capital <strong>{{ dinero(liq.total_capital, cliente?.moneda) }}</strong></span>
          <span class="suave">Libera {{ dinero(liq.linea_liberada, cliente?.moneda) }} de la línea</span>
        </div>
        <button class="primario grande" :disabled="guardando" @click="registrar">
          {{ guardando ? 'Registrando…' : `Registrar pago de ${dinero(liq.total, cliente?.moneda)}` }}
        </button>
      </div>
    </section>

    <template v-if="constancia">
      <p class="aviso info">Pago registrado. Esta es la constancia; el cliente también la ve en su portal.</p>
      <PagoDetalle :pago="constancia" :moneda="cliente?.moneda || 'PEN'">
        <template #acciones><button class="enlace chico" @click="imprimir">Imprimir</button></template>
      </PagoDetalle>
    </template>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; max-width: 1000px; }
h1 { font-size: 22px; }
.total { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.desglose { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.lista li { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--linea); font-variant-numeric: tabular-nums; }
.error-texto { color: var(--error); }
.grande { padding: 12px 18px; font-size: 15px; }
</style>
