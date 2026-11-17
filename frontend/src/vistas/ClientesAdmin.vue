<script setup>
// Lista de solo lectura de los clientes de la tienda, para el dueño.
import { computed, onMounted, ref } from 'vue'
import { adminClientes } from '../api'

const clientes = ref([])
const busqueda = ref('')
const cargando = ref(false)
const error = ref('')
const filtrados = computed(() => clientes.value.filter((c) =>
  `${c.nombres} ${c.apellidos} ${c.numero_documento}`.toLowerCase().includes(busqueda.value.toLowerCase())))

async function cargar() {
  cargando.value = true; error.value = ''
  try { clientes.value = await adminClientes.listar() }
  catch (e) { error.value = e.message }
  finally { cargando.value = false }
}
onMounted(cargar)
</script>

<template>
  <section class="panel">
    <div class="entre">
      <h2>Clientes de mi tienda</h2>
      <div class="fila">
        <input v-model="busqueda" class="buscar" placeholder="Buscar por nombre o documento" />
        <button :disabled="cargando" @click="cargar">Actualizar</button>
      </div>
    </div>
    <p v-if="error" class="aviso" role="alert">{{ error }}</p>
    <p v-if="cargando" class="suave">Cargando…</p>
    <p v-else-if="!filtrados.length" class="suave">No hay clientes para mostrar.</p>
    <div v-else class="tabla-scroll">
      <table>
        <thead><tr><th>Cliente</th><th>Documento</th><th>Estado</th><th class="num">Límite de crédito</th></tr></thead>
        <tbody>
          <tr v-for="c in filtrados" :key="c.id">
            <td><strong>{{ c.nombres }} {{ c.apellidos }}</strong></td>
            <td class="suave">{{ c.tipo_documento }} {{ c.numero_documento }}</td>
            <td><span class="etiqueta" :class="c.estado === 'ACTIVO' ? '' : 'neutra'">{{ c.estado === 'ACTIVO' ? 'Activo' : 'De baja' }}</span></td>
            <td class="num">{{ c.moneda }} {{ c.limite_credito }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.buscar { width: 240px; }
</style>
