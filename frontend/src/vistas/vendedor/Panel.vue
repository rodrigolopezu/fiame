<script setup>
import { CircleCheck } from 'lucide-vue-next'
import { onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import Semaforo from '../../components/Semaforo.vue'
import { ACCIONES, dinero, fecha } from '../../formato'
import { mayuscula, mes } from '../../lenguaje'
import { vista } from '../../vista'

const panel = ref(null)
const error = ref('')

onMounted(async () => {
  try { panel.value = await vendedor.panel() } catch (e) { error.value = e.message }
})

function hora(fechaHora) {
  const d = new Date(fechaHora)
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="pagina">
    <div class="entre">
      <h1>Panel</h1>
      <div class="fila">
        <RouterLink to="/vendedor/ventas/nueva"><button class="primario">Nueva venta</button></RouterLink>
        <RouterLink to="/vendedor/pagos/nuevo"><button>Registrar pago</button></RouterLink>
      </div>
    </div>
    <p v-if="error" class="aviso">{{ error }}</p>
    <template v-if="panel">
      <div class="tarjetas">
        <div class="tarjeta"><div class="rotulo">{{ vista.simple ? 'Te deben en total' : 'Crédito colocado' }}</div><div class="valor">{{ dinero(panel.credito_colocado) }}</div><div class="chico suave">{{ panel.clientes_activos }} clientes activos</div></div>
        <div class="tarjeta"><div class="rotulo">{{ vista.simple ? 'Por cobrar, sin atraso' : 'Por cobrar (al día)' }}</div><div class="valor">{{ dinero(panel.por_cobrar) }}</div><div class="chico suave">{{ panel.proximos.length }} {{ vista.simple ? 'cuentas por cobrar' : 'estados de cuenta' }}</div></div>
        <div class="tarjeta" :class="{ alerta: panel.vencidos.length }"><div class="rotulo">{{ vista.simple ? 'Atrasado, con recargo' : 'Vencido, con mora a hoy' }}</div><div class="valor">{{ dinero(panel.vencido_al_dia) }}</div><div class="chico suave">{{ panel.vencidos.length }} {{ vista.simple ? 'cuentas atrasadas' : 'estados de cuenta' }}</div></div>
        <div class="tarjeta"><div class="rotulo">Ventas del mes</div><div class="valor">{{ dinero(panel.ventas_mes.capital) }}</div><div class="chico suave">{{ panel.ventas_mes.cantidad }} ventas</div></div>
      </div>

      <div class="columnas">
        <section class="panel">
          <h2>{{ vista.simple ? 'Pagos atrasados' : 'Vencidos' }}</h2>
          <p v-if="!panel.vencidos.length" class="suave al-dia"><CircleCheck :size="18" /> No hay estados de cuenta vencidos.</p>
          <table v-else>
            <thead><tr><th>Cliente</th><th>{{ vista.simple ? 'Cuenta de' : 'Estado de cuenta' }}</th><th class="num">{{ vista.simple ? 'Días de atraso' : 'Días' }}</th><th class="num">Debe hoy</th><th></th></tr></thead>
            <tbody>
              <tr v-for="v in panel.vencidos" :key="v.id">
                <td><RouterLink :to="`/vendedor/clientes/${v.cliente_id}`">{{ v.cliente }}</RouterLink></td>
                <td>{{ vista.simple ? mayuscula(mes(v.codigo)) : v.codigo }} <span class="suave chico">vencía {{ fecha(v.fecha_pago) }}</span></td>
                <td class="num"><span class="etiqueta error">{{ v.dias_mora }}</span></td>
                <td class="num"><strong>{{ dinero(v.total_hoy, v.moneda) }}</strong></td>
                <td><RouterLink :to="`/vendedor/pagos/nuevo?cliente=${v.cliente_id}`">Cobrar</RouterLink></td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel">
          <h2>Próximos vencimientos</h2>
          <p v-if="!panel.proximos.length" class="suave">No hay estados de cuenta por vencer.</p>
          <table v-else>
            <thead><tr><th>{{ vista.simple ? 'Paga hasta' : 'Vence' }}</th><th>Cliente</th><th>{{ vista.simple ? 'Cuenta de' : 'Estado de cuenta' }}</th><th class="num">Total</th></tr></thead>
            <tbody>
              <tr v-for="p in panel.proximos" :key="p.id">
                <td>{{ fecha(p.fecha_pago) }}</td>
                <td><RouterLink :to="`/vendedor/clientes/${p.cliente_id}`">{{ p.cliente }}</RouterLink></td>
                <td>{{ vista.simple ? mayuscula(mes(p.codigo)) : p.codigo }}</td>
                <td class="num">{{ dinero(p.total, p.moneda) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel">
          <h2>{{ vista.simple ? '¿Quién paga bien?' : 'Clientes por riesgo' }}</h2>
          <table>
            <thead><tr><th>Cliente</th><th>{{ vista.simple ? 'Cómo paga' : 'Score' }}</th><th class="num">{{ vista.simple ? 'Le puedes fiar' : 'Disponible' }}</th><th class="num">{{ vista.simple ? 'Atrasos' : 'Vencidos' }}</th></tr></thead>
            <tbody>
              <tr v-for="c in panel.clientes" :key="c.id">
                <td><RouterLink :to="`/vendedor/clientes/${c.id}`">{{ c.nombre }}</RouterLink></td>
                <td><Semaforo :score="c.score" detalle /></td>
                <td class="num">{{ dinero(c.linea.disponible, c.moneda) }}</td>
                <td class="num">{{ c.estados_vencidos }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel">
          <div class="entre"><h2>Actividad reciente</h2><RouterLink to="/vendedor/actividad" class="chico">Ver todo</RouterLink></div>
          <ul class="actividad">
            <li v-for="a in panel.actividad" :key="a.id">
              <span class="suave chico">{{ hora(a.fecha_hora) }}</span>
              {{ ACCIONES[a.accion] || a.accion }}
              <span v-if="a.automatico" class="etiqueta neutra">automático</span>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 16px; }
h1 { font-size: 22px; }
.columnas { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); align-items: start; }
.al-dia { display: flex; align-items: center; gap: 6px; color: var(--marca); }
.actividad { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
@media (max-width: 500px) { .columnas { grid-template-columns: 1fr; } }
</style>
