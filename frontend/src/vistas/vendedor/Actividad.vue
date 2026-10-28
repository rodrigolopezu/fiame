<script setup>
// Bitácora de todas las operaciones (requisito del enunciado).
import { onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import { ACCIONES } from '../../formato'

const registros = ref([])
const error = ref('')

onMounted(async () => {
  try { registros.value = await vendedor.actividad() } catch (e) { error.value = e.message }
})

function momento(valor) {
  return new Date(valor).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' })
}

function detalle(a) {
  if (!a.datos) return ''
  return Object.entries(a.datos)
    .filter(([, v]) => typeof v !== 'object' || Array.isArray(v))
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
    .join(' · ')
}
</script>

<template>
  <div class="pagina">
    <h1>Actividad</h1>
    <p class="suave chico">Registro de todas las operaciones del sistema. Los cortes los genera el sistema automáticamente.</p>
    <p v-if="error" class="aviso">{{ error }}</p>
    <section class="panel">
      <div class="tabla-scroll">
        <table>
          <thead><tr><th>Registrado</th><th>Operación</th><th>Referencia</th><th>Detalle</th></tr></thead>
          <tbody>
            <tr v-for="a in registros" :key="a.id">
              <td class="suave">{{ momento(a.fecha_hora) }}</td>
              <td>{{ ACCIONES[a.accion] || a.accion }} <span v-if="a.automatico" class="etiqueta neutra">automático</span></td>
              <td class="suave">{{ a.entidad }}<span v-if="a.entidad_id"> #{{ a.entidad_id }}</span></td>
              <td class="chico">{{ detalle(a) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
</style>
