<script setup>
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import EstadoCuentaDetalle from '../../components/EstadoCuentaDetalle.vue'
import { dinero, fecha } from '../../formato'
import { estadoSimple, mayuscula, mes } from '../../lenguaje'
import { vista } from '../../vista'

const estados = ref([])
const filtro = ref('PENDIENTES')
const ocultarVacios = ref(true)
const abierto = ref(null)
const error = ref('')

onMounted(async () => {
  try { estados.value = await vendedor.estadosCuenta() } catch (e) { error.value = e.message }
})

const FILTROS = { TODOS: 'Todos', PENDIENTES: 'Por cobrar', VENCIDO: 'Vencidos', PAGADO: 'Pagados' }
const filtrados = computed(() => estados.value.filter((ec) =>
  (!ocultarVacios.value || ec.lineas.length) &&
  (filtro.value === 'TODOS' || (filtro.value === 'PENDIENTES' ? ec.estado !== 'PAGADO' : ec.estado === filtro.value))))
const clase = { PENDIENTE: 'info', VENCIDO: 'error', PAGADO: '' }
</script>

<template>
  <div class="pagina">
    <h1>{{ vista.simple ? 'Cuentas del mes' : 'Estados de cuenta' }}</h1>
    <p class="suave chico">{{ vista.simple ? 'Cada mes, al día de cierre, el sistema arma solo la cuenta de cada cliente con lo que tiene que pagar.' : 'Se generan solos al cierre de cada día de corte (23:59:59), uno por cliente activo, aunque no tenga movimientos.' }}</p>
    <div class="entre">
      <div class="pestanas">
        <button v-for="(nombre, f) in FILTROS" :key="f" :class="{ activa: filtro === f }" @click="filtro = f">{{ nombre }}</button>
      </div>
      <label class="check"><input v-model="ocultarVacios" type="checkbox" /> Ocultar sin movimientos</label>
    </div>
    <p v-if="error" class="aviso">{{ error }}</p>
    <section class="panel">
      <div class="tabla-scroll">
        <table>
          <thead><tr><th>{{ vista.simple ? 'Mes' : 'Código' }}</th><th>Cliente</th><th>{{ vista.simple ? 'Cierre' : 'Corte' }}</th><th>{{ vista.simple ? 'Paga hasta' : 'Vence' }}</th><th class="num">{{ vista.simple ? 'Monto' : 'Total' }}</th><th class="num">Debe hoy</th><th>Estado</th></tr></thead>
          <tbody>
            <tr v-if="!filtrados.length"><td colspan="7" class="suave">No hay estados de cuenta.</td></tr>
            <template v-for="ec in filtrados" :key="ec.id">
              <tr class="fila-clic" @click="abierto = abierto === ec.id ? null : ec.id">
                <td>{{ vista.simple ? mayuscula(mes(ec.codigo)) : ec.codigo }}</td>
                <td><RouterLink :to="`/vendedor/clientes/${ec.cliente_id}`" @click.stop>{{ ec.cliente }}</RouterLink></td>
                <td>{{ fecha(ec.fecha_corte) }}</td>
                <td>{{ fecha(ec.fecha_pago) }}</td>
                <td class="num">{{ dinero(ec.total_a_pagar, ec.moneda) }}</td>
                <td class="num">{{ ec.deuda_al_dia ? dinero(ec.deuda_al_dia.total_a_pagar, ec.moneda) : ec.estado === 'PAGADO' ? '—' : dinero(ec.total_a_pagar, ec.moneda) }}</td>
                <td><span class="etiqueta" :class="clase[ec.estado]">{{ vista.simple ? estadoSimple(ec.estado) : ec.estado.toLowerCase() }}</span></td>
              </tr>
              <tr v-if="abierto === ec.id">
                <td colspan="7" class="detalle">
                  <EstadoCuentaDetalle :ec="ec">
                    <template #acciones>
                      <RouterLink v-if="ec.estado !== 'PAGADO'" :to="`/vendedor/pagos/nuevo?cliente=${ec.cliente_id}`" class="chico">Registrar pago</RouterLink>
                    </template>
                  </EstadoCuentaDetalle>
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
