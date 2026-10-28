<script setup>
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import VentaDetalle from '../../components/VentaDetalle.vue'
import { dinero, fecha } from '../../formato'
import { vista } from '../../vista'

const ventas = ref([])
const filtro = ref('TODAS')
const abierta = ref(null)
const error = ref('')

async function cargar() {
  try { ventas.value = await vendedor.ventas() } catch (e) { error.value = e.message }
}
onMounted(cargar)

const filtradas = computed(() => ventas.value.filter((v) => filtro.value === 'TODAS' || v.estado === filtro.value))

async function anular(v) {
  if (!confirm(`¿Anular la venta ${v.numero}? Solo es posible si aún no entró en un estado de cuenta.`)) return
  error.value = ''
  try { await vendedor.anularVenta(v.numero); await cargar() } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="pagina">
    <div class="entre">
      <h1>Ventas</h1>
      <RouterLink to="/vendedor/ventas/nueva"><button class="primario">Nueva venta</button></RouterLink>
    </div>
    <div class="pestanas">
      <button v-for="f in ['TODAS', 'VIGENTE', 'PAGADA', 'ANULADA']" :key="f" :class="{ activa: filtro === f }" @click="filtro = f">
        {{ f === 'TODAS' ? 'Todas' : f[0] + f.slice(1).toLowerCase() + 's' }}
      </button>
    </div>
    <p v-if="error" class="aviso">{{ error }}</p>
    <section class="panel">
      <div class="tabla-scroll">
        <table>
          <thead><tr><th>N.°</th><th>Fecha</th><th>Cliente</th><th>Productos</th><th>{{ vista.simple ? 'Forma de pago' : 'Modalidad' }}</th><th class="num">{{ vista.simple ? 'Monto' : 'Capital' }}</th><th>{{ vista.simple ? 'Paga hasta' : 'Vence' }}</th><th>Estado</th></tr></thead>
          <tbody>
            <tr v-if="!filtradas.length"><td colspan="8" class="suave">No hay ventas.</td></tr>
            <template v-for="v in filtradas" :key="v.numero">
              <tr class="fila-clic" @click="abierta = abierta === v.numero ? null : v.numero">
                <td>{{ v.numero }}</td>
                <td>{{ fecha(v.fecha) }}</td>
                <td><RouterLink :to="`/vendedor/clientes/${v.cliente_id}`" @click.stop>{{ v.cliente }}</RouterLink></td>
                <td>{{ v.items.map((i) => i.descripcion).join(', ') }}</td>
                <td>{{ v.modalidad === 'CUOTAS' ? `${vista.simple ? 'En ' : ''}${v.numero_cuotas} cuotas` : (vista.simple ? 'Un solo pago' : 'Fin de mes') }}</td>
                <td class="num">{{ dinero(v.capital, v.moneda) }}</td>
                <td>{{ fecha(v.modalidad === 'CUOTAS' ? v.cuotas[0]?.fecha_vencimiento : v.fecha_pago) }}</td>
                <td><span class="etiqueta" :class="{ info: v.estado === 'VIGENTE', neutra: v.estado === 'ANULADA' }">{{ v.estado.toLowerCase() }}</span></td>
              </tr>
              <tr v-if="abierta === v.numero">
                <td colspan="8" class="detalle">
                  <VentaDetalle :venta="{ ...v, cliente: null }">
                    <template #acciones>
                      <button v-if="v.estado === 'VIGENTE'" class="enlace chico" @click="anular(v)">Anular</button>
                    </template>
                  </VentaDetalle>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
.fila-clic { cursor: pointer; }
.fila-clic:hover td { background: var(--panel-suave); }
.detalle { background: var(--fondo); padding: 10px; }
</style>
