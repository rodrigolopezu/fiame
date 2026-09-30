<script setup>
// Eventos del escenario, en orden cronológico, con el resultado de la simulación.
import { computed } from 'vue'
import { dinero, fecha, TIPOS_EVENTO } from '../formato'

const props = defineProps({
  eventos: { type: Array, required: true },
  bitacora: { type: Array, default: () => [] },
  moneda: { type: String, required: true },
})
defineEmits(['quitar'])

const ordenados = computed(() =>
  props.eventos
    .map((evento, indice) => ({ evento, indice, registro: props.bitacora.find((r) => r.evento === indice) }))
    .sort((a, b) => a.evento.fecha.localeCompare(b.evento.fecha) || a.indice - b.indice),
)

function resumen(ev) {
  if (ev.tipo === 'VENTA') {
    const items = ev.items.map((i) => `${i.descripcion || 'sin nombre'} ${dinero(i.precio_lista, i.moneda)}`).join(', ')
    return `${items} · ${ev.modalidad === 'CUOTAS' ? `${ev.numero_cuotas} cuotas` : 'fin de mes'}`
  }
  if (ev.tipo === 'PAGO') return `${ev.cantidad_estados} estado(s) de cuenta · ${ev.medio.toLowerCase()}`
  if (ev.tipo === 'ANULAR_VENTA') return `Venta ${ev.venta}`
  const cambios = []
  if (ev.tasa_compensatoria) cambios.push(`compensatoria ${ev.tasa_compensatoria.valor} %`)
  if (ev.tasa_moratoria) cambios.push(`moratoria ${ev.tasa_moratoria.valor} %`)
  if (ev.limite_credito) cambios.push(`límite ${dinero(ev.limite_credito, props.moneda)}`)
  return cambios.join(', ')
}
</script>

<template>
  <section class="panel">
    <div class="entre">
      <h2>Eventos ({{ eventos.length }})</h2>
      <span class="suave chico">Los cortes se generan solos</span>
    </div>
    <p v-if="!eventos.length" class="suave">Agrega una venta para empezar.</p>
    <ol class="lista">
      <li v-for="{ evento, indice, registro } in ordenados" :key="indice" :class="{ rechazado: registro?.resultado === 'RECHAZADO' }">
        <div class="entre">
          <span><strong>{{ fecha(evento.fecha) }}</strong> · {{ TIPOS_EVENTO[evento.tipo] }}</span>
          <span class="fila">
            <span v-if="registro" class="etiqueta" :class="{ error: registro.resultado === 'RECHAZADO' }">{{ registro.resultado === 'OK' ? 'OK' : 'Rechazado' }}</span>
            <button class="icono" title="Quitar evento" @click="$emit('quitar', indice)">×</button>
          </span>
        </div>
        <p class="chico">{{ resumen(evento) }}</p>
        <p v-if="registro" class="chico suave">{{ registro.mensaje }}</p>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
li { border: 1px solid var(--borde); border-left: 3px solid var(--marca); border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; gap: 3px; }
li.rechazado { border-left-color: var(--error); background: #fffafa; }
</style>
