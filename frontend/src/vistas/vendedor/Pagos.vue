<script setup>
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import PagoDetalle from '../../components/PagoDetalle.vue'

const pagos = ref([])
const error = ref('')

async function cargar() {
  try { pagos.value = await vendedor.pagos() } catch (e) { error.value = e.message }
}
onMounted(cargar)

// Solo se puede anular el último pago válido de cada cliente.
const anulables = computed(() => {
  const vistos = new Set()
  const ids = new Set()
  for (const p of pagos.value) {
    if (p.estado === 'VALIDO' && !vistos.has(p.cliente_id)) { ids.add(p.numero); vistos.add(p.cliente_id) }
  }
  return ids
})

async function anular(p) {
  const motivo = prompt(`Motivo de la anulación del pago ${p.numero}:`)
  if (!motivo) return
  error.value = ''
  try { await vendedor.anularPago(p.numero, motivo); await cargar() } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="pagina">
    <div class="entre">
      <h1>Pagos</h1>
      <RouterLink to="/vendedor/pagos/nuevo"><button class="primario">Registrar pago</button></RouterLink>
    </div>
    <p class="suave chico">Un pago no se borra: se anula indicando el motivo, y queda registrado.</p>
    <p v-if="error" class="aviso">{{ error }}</p>
    <p v-if="!pagos.length" class="panel suave">Todavía no hay pagos.</p>
    <PagoDetalle v-for="p in pagos" :key="p.numero" :pago="p" :moneda="p.moneda">
      <template #acciones>
        <button v-if="anulables.has(p.numero)" class="enlace chico" @click="anular(p)">Anular</button>
      </template>
    </PagoDetalle>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
</style>
