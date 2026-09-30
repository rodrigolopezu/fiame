<script setup>
// Escenario de un cliente: condiciones + eventos. Cada cambio vuelve a simular en el backend.
import { computed, ref, watch } from 'vue'
import { api } from '../api'
import { CASOS, copiar } from '../casos'
import Ayuda from './Ayuda.vue'
import Condiciones from './Condiciones.vue'
import ListaEventos from './ListaEventos.vue'
import NuevoEvento from './NuevoEvento.vue'
import Resultados from './Resultados.vue'

const CLAVE = 'fiame.escenario'

function cargarGuardado() {
  try {
    const guardado = JSON.parse(localStorage.getItem(CLAVE))
    if (guardado?.condiciones && Array.isArray(guardado.eventos)) return guardado
  } catch { /* sin almacenamiento disponible */ }
  return copiar(CASOS.caso1)
}

const escenario = ref(cargarGuardado())
const resultado = ref(null)
const error = ref('')
const cargando = ref(false)

const ultimaFecha = computed(() =>
  escenario.value.eventos.map((e) => e.fecha).sort().at(-1) || escenario.value.fecha_hasta,
)

function cargarCaso(clave) {
  escenario.value = copiar(CASOS[clave])
}

function agregarEvento(evento) {
  escenario.value.eventos.push(evento)
  if (evento.fecha > escenario.value.fecha_hasta) escenario.value.fecha_hasta = evento.fecha
}

let temporizador
let pedido = 0
async function simular() {
  const id = ++pedido
  cargando.value = true
  try {
    const { nombre, descripcion, ...solicitud } = escenario.value
    const r = await api.simular(solicitud)
    if (id === pedido) { resultado.value = r; error.value = '' }
  } catch (e) {
    if (id === pedido) error.value = e.message
  } finally {
    if (id === pedido) cargando.value = false
  }
}

watch(escenario, () => {
  try { localStorage.setItem(CLAVE, JSON.stringify(escenario.value)) } catch { /* sin almacenamiento */ }
  clearTimeout(temporizador)
  temporizador = setTimeout(simular, 300)
}, { deep: true, immediate: true })
</script>

<template>
  <div class="simulador">
    <aside class="lateral">
      <section class="panel">
        <h2>Escenario</h2>
        <div class="casos">
          <button v-for="(caso, clave) in CASOS" :key="clave" :title="caso.descripcion" @click="cargarCaso(clave)">{{ caso.nombre }}</button>
        </div>
        <label class="campo hasta">
          <span>Simular hasta <Ayuda texto="Hace de 'hoy': se generan los cortes hasta esta fecha y la mora de lo vencido se calcula a este día." /></span>
          <input v-model="escenario.fecha_hasta" type="date" />
        </label>
      </section>
      <Condiciones v-model="escenario.condiciones" />
      <NuevoEvento
        :key="escenario.condiciones.moneda"
        :moneda="escenario.condiciones.moneda"
        :max-cuotas="escenario.condiciones.max_meses"
        :ventas="resultado?.ventas || []"
        :fecha-sugerida="ultimaFecha"
        @agregar="agregarEvento"
      />
      <ListaEventos
        :eventos="escenario.eventos"
        :bitacora="resultado?.bitacora || []"
        :moneda="escenario.condiciones.moneda"
        @quitar="escenario.eventos.splice($event, 1)"
      />
    </aside>

    <main class="principal">
      <div v-if="error" class="aviso">No se pudo simular:
{{ error }}</div>
      <p v-if="cargando && !resultado" class="suave">Calculando…</p>
      <Resultados v-if="resultado" :resultado="resultado" :class="{ desactualizado: error }" />
    </main>
  </div>
</template>

<style scoped>
.simulador { display: grid; grid-template-columns: minmax(380px, 460px) 1fr; gap: 16px; align-items: start; }
.lateral, .principal { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.casos { display: flex; flex-direction: column; gap: 6px; }
.casos button { text-align: left; }
.hasta { max-width: 200px; }
.desactualizado { opacity: 0.45; }
@media (max-width: 1000px) { .simulador { grid-template-columns: 1fr; } }
</style>
