<script setup>
// Portal del cliente: consulta de solo lectura con el código que le entregó la tienda.
import { computed, ref } from 'vue'
import { portal } from '../../api'
import EstadoCuentaDetalle from '../../components/EstadoCuentaDetalle.vue'
import InterruptorVista from '../../components/InterruptorVista.vue'
import Logo from '../../components/Logo.vue'
import PagoDetalle from '../../components/PagoDetalle.vue'
import Termino from '../../components/Termino.vue'
import { dinero, fecha, tasaCorta } from '../../formato'
import { tasaSimple } from '../../lenguaje'
import { vista as modoVista } from '../../vista'

const codigo = ref('')
const datos = ref(null)
const error = ref('')
const consultando = ref(false)
const vista = ref('estados')

function formatear(valor) {
  const limpio = valor.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8)
  codigo.value = limpio.length > 4 ? `${limpio.slice(0, 4)}-${limpio.slice(4)}` : limpio
}

async function consultar() {
  consultando.value = true
  error.value = ''
  try {
    datos.value = await portal.consultar(codigo.value)
  } catch (e) {
    error.value = e.message
  } finally {
    consultando.value = false
  }
}

function salir() {
  datos.value = null
  codigo.value = ''
}

const moneda = computed(() => datos.value?.cliente.moneda || 'PEN')
const estados = computed(() => datos.value.estados_cuenta.filter((ec) => ec.lineas.length))
const cuotasPendientes = computed(() => datos.value.ventas
  .filter((v) => v.estado === 'VIGENTE')
  .flatMap((v) => v.cuotas.filter((c) => c.estado === 'PENDIENTE').map((c) => ({ ...c, producto: v.items.map((i) => i.descripcion).join(', '), total: v.numero_cuotas })))
  .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento)))
const comprasSinFacturar = computed(() => datos.value.ventas.filter((v) => v.estado === 'VIGENTE' && v.modalidad === 'FIN_DE_MES' && !v.estado_cuenta))
</script>

<template>
  <main class="portal">
    <header>
      <RouterLink to="/" class="marca"><Logo :tamano="30" /></RouterLink>
      <span class="suave">Portal del cliente</span>
    </header>

    <form v-if="!datos" class="panel acceso" @submit.prevent="consultar">
      <h1>Consulta tu estado de cuenta</h1>
      <p class="suave">Ingresa el código que te entregó la tienda.</p>
      <input :value="codigo" class="codigo" placeholder="XXXX-XXXX" autocomplete="off" autofocus
             @input="formatear($event.target.value)" />
      <p v-if="error" class="aviso">{{ error }}</p>
      <button class="primario" :disabled="codigo.length < 9 || consultando">{{ consultando ? 'Consultando…' : 'Consultar' }}</button>
      <p class="chico suave">Datos de prueba: <code>J7KQ-M4HP</code> (Juan) y <code>A7NT-X4PL</code> (Ana).</p>
    </form>

    <template v-else>
      <section class="panel saludo">
        <div class="entre">
          <div>
            <p class="suave chico">{{ datos.tienda.nombre }} · {{ datos.tienda.direccion }}</p>
            <h1>Hola, {{ datos.cliente.nombre }}</h1>
            <p class="suave chico">Información al {{ fecha(datos.hoy) }}</p>
          </div>
          <div class="fila">
            <InterruptorVista />
            <button @click="salir">Salir</button>
          </div>
        </div>
        <div class="tarjetas">
          <div class="tarjeta" :class="{ alerta: datos.estados_vencidos }">
            <div class="rotulo">{{ datos.estados_vencidos ? (modoVista.simple ? 'Debes hoy (con recargo)' : 'Deuda al día (con intereses por mora)') : (modoVista.simple ? 'Por pagar' : 'Deuda pendiente') }}</div>
            <div class="valor">{{ dinero(datos.estados_vencidos ? datos.deuda_al_dia : datos.deuda_pendiente, moneda) }}</div>
            <div class="chico suave">
              {{ datos.estados_vencidos ? (modoVista.simple ? `${datos.estados_vencidos} ${datos.estados_vencidos === 1 ? 'mes atrasado' : 'meses atrasados'}` : `${datos.estados_vencidos} estado(s) de cuenta vencido(s)`) : datos.proximo_vencimiento ? `hasta el ${fecha(datos.proximo_vencimiento)}` : 'no tienes pagos pendientes' }}
            </div>
          </div>
          <div class="tarjeta">
            <div class="rotulo">{{ modoVista.simple ? 'Aún puedes fiar' : 'Línea de crédito disponible' }}</div>
            <div class="valor">{{ dinero(datos.linea.disponible, moneda) }}</div>
            <div class="chico suave">{{ modoVista.simple ? `tu máximo es ${dinero(datos.linea.limite, moneda)}` : `de ${dinero(datos.linea.limite, moneda)}` }}</div>
          </div>
          <div class="tarjeta">
            <template v-if="modoVista.simple">
              <div class="rotulo">Tu interés</div>
              <div class="valor">{{ tasaSimple(datos.tasa_compensatoria.tea) }} al año</div>
              <div class="chico suave">Si te atrasas: {{ tasaSimple(datos.tasa_moratoria.tea) }} al año de recargo</div>
            </template>
            <template v-else>
              <div class="rotulo">Tu tasa de interés</div>
              <div class="valor"><Termino clave="tea">TEA</Termino> {{ tasaCorta(datos.tasa_compensatoria.tea) }}</div>
              <div class="chico suave"><Termino clave="moratorio">Moratoria</Termino>: TEA {{ tasaCorta(datos.tasa_moratoria.tea) }}</div>
            </template>
          </div>
        </div>
        <p v-if="datos.estados_vencidos" class="aviso">
          Tienes pagos vencidos. Mientras no los canceles se suman intereses por mora cada día. Acércate a la tienda para ponerte al día.
        </p>
        <p class="chico suave">Tu ciclo cierra el día {{ datos.cliente.dia_corte }} de cada mes y pagas hasta el día {{ datos.cliente.dia_pago }}.</p>
      </section>

      <div class="pestanas">
        <button :class="{ activa: vista === 'estados' }" @click="vista = 'estados'">Estados de cuenta</button>
        <button :class="{ activa: vista === 'cuotas' }" @click="vista = 'cuotas'">Cuotas y compras ({{ cuotasPendientes.length + comprasSinFacturar.length }})</button>
        <button :class="{ activa: vista === 'pagos' }" @click="vista = 'pagos'">Constancias de pago ({{ datos.pagos.length }})</button>
      </div>

      <template v-if="vista === 'estados'">
        <p v-if="!estados.length" class="panel suave">Todavía no tienes estados de cuenta con movimientos.</p>
        <EstadoCuentaDetalle v-for="ec in estados" :key="ec.id" :ec="{ ...ec, cliente: null }" perspectiva="cliente" />
      </template>

      <template v-else-if="vista === 'cuotas'">
        <section class="panel">
          <h2>Próximas cuotas</h2>
          <p v-if="!cuotasPendientes.length" class="suave">No tienes cuotas pendientes.</p>
          <table v-else>
            <thead><tr><th>Vence</th><th>Producto</th><th>Cuota</th><th class="num">Monto</th></tr></thead>
            <tbody>
              <tr v-for="c in cuotasPendientes" :key="`${c.producto}-${c.numero}-${c.fecha_vencimiento}`">
                <td>{{ fecha(c.fecha_vencimiento) }}</td>
                <td>{{ c.producto }}</td>
                <td>{{ c.numero }}/{{ c.total }}</td>
                <td class="num">{{ dinero(c.cuota, moneda) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Compras del periodo en curso</h2>
          <p class="chico suave">Entrarán en tu próximo estado de cuenta.</p>
          <p v-if="!comprasSinFacturar.length" class="suave">No tienes compras nuevas.</p>
          <table v-else>
            <thead><tr><th>Fecha</th><th>Productos</th><th class="num">Monto</th><th>Pagas hasta</th></tr></thead>
            <tbody>
              <tr v-for="v in comprasSinFacturar" :key="v.numero">
                <td>{{ fecha(v.fecha) }}</td>
                <td>{{ v.items.map((i) => i.descripcion).join(', ') }}</td>
                <td class="num">{{ dinero(v.total, moneda) }}</td>
                <td>{{ fecha(v.fecha_pago) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>

      <template v-else>
        <p v-if="!datos.pagos.length" class="panel suave">Todavía no tienes pagos registrados.</p>
        <PagoDetalle v-for="p in datos.pagos" :key="p.numero" :pago="{ ...p, cliente: null }" :moneda="moneda" />
      </template>
    </template>
  </main>
</template>

<style scoped>
.portal { max-width: 900px; margin: 0 auto; padding: 20px 16px 48px; display: flex; flex-direction: column; gap: 14px; }
header { display: flex; align-items: center; gap: 12px; }
.marca { display: inline-flex; text-decoration: none; }
h1 { font-size: 22px; }
.acceso { max-width: 420px; margin: 40px auto 0; width: 100%; text-align: center; align-items: stretch; }
.codigo { font-size: 24px; text-align: center; letter-spacing: 0.15em; font-weight: 700; padding: 12px; color: var(--marca-fuerte); }
.saludo { background: linear-gradient(160deg, #ffffff 40%, var(--marca-suave) 100%); }
.saludo { gap: 14px; }
</style>
