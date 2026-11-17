<script setup>
import { onMounted, ref, computed } from 'vue'
import { adminClientes } from '../api'
const clientes = ref([])
const busqueda = ref('')
const cargando = ref(false)
const error = ref('')
const filtrados = computed(() => clientes.value.filter(c =>
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
  <section style="border:1px solid #bbb;border-radius:12px;padding:20px;margin:20px 0">
    <h2>Clientes de mi tienda</h2>
    <p>Consulta de clientes registrados por los vendedores de esta tienda.</p>
    <label>Buscar cliente <input v-model="busqueda" placeholder="Nombre o documento" /></label>
    <button type="button" @click="cargar" :disabled="cargando" style="margin-left:12px">Actualizar</button>
    <p v-if="error" role="alert" style="color:#b91c1c">{{ error }}</p>
    <p v-if="cargando">Cargando clientes...</p>
    <p v-else-if="!filtrados.length">No hay clientes para mostrar.</p>
    <div v-else style="overflow-x:auto;margin-top:12px">
      <table style="width:100%;text-align:left;border-collapse:collapse">
        <thead><tr><th>Cliente</th><th>Documento</th><th>Estado</th><th>Límite de crédito</th></tr></thead>
        <tbody><tr v-for="c in filtrados" :key="c.id">
          <td>{{ c.nombres }} {{ c.apellidos }}</td><td>{{ c.numero_documento }}</td>
          <td>{{ c.estado }}</td><td>{{ c.moneda }} {{ c.limite_credito }}</td>
        </tr></tbody>
      </table>
    </div>
  </section>
</template>
