<script setup>
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import Semaforo from '../../components/Semaforo.vue'
import { dinero, fecha } from '../../formato'
import { vista } from '../../vista'

const clientes = ref([])
const buscar = ref('')
const verBajas = ref(false)
const error = ref('')

onMounted(async () => {
  try { clientes.value = await vendedor.clientes() } catch (e) { error.value = e.message }
})

const filtrados = computed(() => {
  const q = buscar.value.trim().toLowerCase()
  return clientes.value.filter((c) =>
    (verBajas.value || c.estado === 'ACTIVO') &&
    (!q || c.nombre.toLowerCase().includes(q) || c.numero_documento.includes(q)))
})

function uso(c) {
  const limite = Number(c.linea.limite)
  return limite ? Math.min(100, (Number(c.linea.usado) / limite) * 100) : 0
}
</script>

<template>
  <div class="pagina">
    <div class="entre">
      <h1>Clientes</h1>
      <RouterLink to="/vendedor/clientes/nuevo"><button class="primario">Nuevo cliente</button></RouterLink>
    </div>
    <div class="fila">
      <input v-model="buscar" class="buscar" placeholder="Buscar por nombre o documento" />
      <label class="check"><input v-model="verBajas" type="checkbox" /> Mostrar dados de baja</label>
    </div>
    <p v-if="error" class="aviso">{{ error }}</p>
    <section class="panel">
      <div class="tabla-scroll">
        <table>
          <thead>
            <tr><th>Cliente</th><th>Documento</th><th>{{ vista.simple ? 'Crédito' : 'Línea de crédito' }}</th><th class="num">{{ vista.simple ? 'Por pagar' : 'Deuda pendiente' }}</th><th>Próximo pago</th><th>{{ vista.simple ? 'Cómo paga' : 'Score' }}</th></tr>
          </thead>
          <tbody>
            <tr v-if="!filtrados.length"><td colspan="6" class="suave">No hay clientes.</td></tr>
            <tr v-for="c in filtrados" :key="c.id">
              <td>
                <RouterLink :to="`/vendedor/clientes/${c.id}`"><strong>{{ c.nombre }}</strong></RouterLink>
                <span v-if="c.estado === 'BAJA'" class="etiqueta neutra">baja</span>
                <div class="suave chico">{{ c.telefono || 'sin teléfono' }}</div>
              </td>
              <td>{{ c.tipo_documento }} {{ c.numero_documento }}</td>
              <td class="linea">
                <div class="barra"><div :style="{ width: `${uso(c)}%` }" :class="{ alta: uso(c) > 80 }" /></div>
                <span class="chico">{{ vista.simple ? `le puedes fiar ${dinero(c.linea.disponible, c.moneda)} más` : `${dinero(c.linea.disponible, c.moneda)} disponibles de ${dinero(c.linea.limite, c.moneda)}` }}</span>
              </td>
              <td class="num">
                {{ dinero(c.deuda_pendiente, c.moneda) }}
                <div v-if="c.estados_vencidos" class="chico"><span class="etiqueta error">{{ c.estados_vencidos }} {{ vista.simple ? 'atrasado(s)' : 'vencido(s)' }}</span></div>
              </td>
              <td>{{ c.proximo_vencimiento ? fecha(c.proximo_vencimiento) : '—' }}</td>
              <td><Semaforo :score="c.score" /></td>
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
.buscar { max-width: 340px; }
.linea { min-width: 200px; }
.barra { height: 6px; background: var(--gris-suave); border-radius: 3px; overflow: hidden; margin: 4px 0; }
.barra div { height: 100%; background: var(--exito); border-radius: 3px; }
.barra div.alta { background: var(--alerta); }
</style>
