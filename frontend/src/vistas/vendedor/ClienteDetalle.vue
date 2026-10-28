<script setup>
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import EstadoCuentaDetalle from '../../components/EstadoCuentaDetalle.vue'
import PagoDetalle from '../../components/PagoDetalle.vue'
import Semaforo from '../../components/Semaforo.vue'
import Termino from '../../components/Termino.vue'
import VentaDetalle from '../../components/VentaDetalle.vue'
import { dinero, fecha, tasa } from '../../formato'
import { tasaSimple } from '../../lenguaje'
import { vista as modoVista } from '../../vista'

const props = defineProps({ id: { type: String, required: true } })
const c = ref(null)
const vista = ref('estados')
const error = ref('')
const aviso = ref('')
const codigo = ref(null)
const ocultarVacios = ref(true)

async function cargar() {
  try { c.value = await vendedor.cliente(props.id) } catch (e) { error.value = e.message }
}
onMounted(cargar)

const estados = computed(() => c.value.estados_cuenta.filter((ec) => !ocultarVacios.value || ec.lineas.length))
const ultimoPagoValido = computed(() => c.value.pagos.find((p) => p.estado === 'VALIDO')?.numero)
const pendientes = computed(() => c.value.estados_cuenta.filter((ec) => ec.estado !== 'PAGADO').length)

async function accion(fn, exito) {
  error.value = ''
  aviso.value = ''
  try {
    await fn()
    aviso.value = exito
    await cargar()
  } catch (e) {
    error.value = e.message
  }
}

async function generarCodigo() {
  if (c.value.tiene_codigo && !confirm('Se generará un código nuevo y el anterior dejará de funcionar. ¿Continuar?')) return
  error.value = ''
  try {
    codigo.value = (await vendedor.generarCodigo(props.id)).codigo
    await cargar()
  } catch (e) { error.value = e.message }
}

const enlaceWhatsApp = computed(() => {
  if (!codigo.value || !c.value.telefono) return null
  const texto = `Hola ${c.value.nombres}, puedes consultar tu estado de cuenta en ${location.origin}/portal con el código ${codigo.value}.`
  const numero = c.value.telefono.startsWith('+') ? c.value.telefono.slice(1) : `51${c.value.telefono}`
  return `https://wa.me/${numero}?text=${encodeURIComponent(texto)}`
})

function anularVenta(v) {
  if (confirm(`¿Anular la venta ${v.numero}? Solo es posible si aún no entró en un estado de cuenta.`)) {
    accion(() => vendedor.anularVenta(v.numero), `Venta ${v.numero} anulada.`)
  }
}

function darDeBaja() {
  if (confirm('¿Dar de baja al cliente? Solo es posible si no tiene deuda.')) {
    accion(() => vendedor.darDeBaja(c.value.id), 'Cliente dado de baja.')
  }
}

function anularPago(p) {
  const motivo = prompt(`Motivo de la anulación del pago ${p.numero}:`)
  if (motivo) accion(() => vendedor.anularPago(p.numero, motivo), `Pago ${p.numero} anulado.`)
}
</script>

<template>
  <div v-if="c" class="pagina">
    <div class="entre">
      <div>
        <RouterLink to="/vendedor/clientes" class="chico">← Clientes</RouterLink>
        <h1>{{ c.nombre }} <span v-if="c.estado === 'BAJA'" class="etiqueta neutra">dado de baja</span></h1>
        <p class="suave">{{ c.tipo_documento }} {{ c.numero_documento }} · {{ c.telefono || 'sin teléfono' }} · cliente desde {{ fecha(c.fecha_alta) }}</p>
      </div>
      <div v-if="c.estado === 'ACTIVO'" class="fila">
        <RouterLink :to="`/vendedor/ventas/nueva?cliente=${c.id}`"><button class="primario">Nueva venta</button></RouterLink>
        <RouterLink v-if="pendientes" :to="`/vendedor/pagos/nuevo?cliente=${c.id}`"><button>Registrar pago</button></RouterLink>
        <RouterLink :to="`/vendedor/clientes/${c.id}/editar`"><button>Editar</button></RouterLink>
      </div>
    </div>

    <p v-if="error" class="aviso">{{ error }}</p>
    <p v-if="aviso" class="aviso info">{{ aviso }}</p>

    <div class="tarjetas">
      <div class="tarjeta">
        <div class="rotulo">{{ modoVista.simple ? 'Le puedes fiar' : 'Crédito disponible' }}</div>
        <div class="valor">{{ dinero(c.linea.disponible, c.moneda) }}</div>
        <div class="chico suave">{{ modoVista.simple ? `ya debe ${dinero(c.linea.usado, c.moneda)} de un máximo de ${dinero(c.linea.limite, c.moneda)}` : `usado ${dinero(c.linea.usado, c.moneda)} de ${dinero(c.linea.limite, c.moneda)}` }}</div>
      </div>
      <div class="tarjeta" :class="{ alerta: c.estados_vencidos }">
        <div class="rotulo">{{ c.estados_vencidos ? (modoVista.simple ? 'Debe hoy (con recargo)' : 'Debe hoy (con mora)') : (modoVista.simple ? 'Tiene por pagar' : 'Deuda pendiente') }}</div>
        <div class="valor">{{ dinero(c.estados_vencidos ? c.deuda_al_dia : c.deuda_pendiente, c.moneda) }}</div>
        <div class="chico suave">{{ c.proximo_vencimiento ? `próximo vencimiento ${fecha(c.proximo_vencimiento)}` : 'sin vencimientos próximos' }}</div>
      </div>
      <div class="tarjeta">
        <div class="rotulo">{{ modoVista.simple ? '¿Cómo paga?' : 'Score crediticio' }} <Ayuda texto="Privado de la tienda. Puntualidad (50), días de mora promedio (20), deuda vencida hoy (20) y uso de la línea (10)." /></div>
        <div class="valor"><Semaforo :score="c.score" detalle /></div>
        <div v-if="c.score.detalle.estados_exigibles" class="chico suave">
          <template v-if="modoVista.simple">Pagó a tiempo {{ c.score.detalle.pagos_a_tiempo }} de {{ c.score.detalle.estados_exigibles }} veces</template>
          <template v-else>{{ c.score.detalle.pagos_a_tiempo }} de {{ c.score.detalle.estados_exigibles }} pagados a tiempo · mora promedio {{ c.score.detalle.dias_mora_promedio }} días</template>
        </div>
      </div>
      <div class="tarjeta">
        <div class="rotulo">Condiciones</div>
        <template v-if="modoVista.simple">
          <div>Interés {{ tasaSimple(c.tasa_compensatoria.tea) }} al año</div>
          <div class="chico suave">Recargo por atraso {{ tasaSimple(c.tasa_moratoria.tea) }} al año · cierra el {{ c.dia_corte }} y paga el {{ c.dia_pago }} · hasta {{ c.max_meses }} cuotas</div>
        </template>
        <template v-else>
          <div>{{ c.tasa_compensatoria.descripcion }} <span class="suave chico">(<Termino clave="tea">TEA</Termino> {{ tasa(c.tasa_compensatoria.tea) }})</span></div>
          <div class="chico suave"><Termino clave="moratorio">Mora</Termino> {{ c.tasa_moratoria.descripcion }} · <Termino clave="corte">corte</Termino> día {{ c.dia_corte }} · pago día {{ c.dia_pago }} · hasta {{ c.max_meses }} cuotas</div>
        </template>
      </div>
    </div>

    <section v-if="c.estado === 'ACTIVO'" class="panel portal">
      <div class="entre">
        <div>
          <h3>Acceso al portal del cliente</h3>
          <p class="chico suave">El cliente consulta sus estados de cuenta en <strong>/portal</strong> con un código. Por seguridad el código solo se muestra al generarlo.</p>
        </div>
        <button @click="generarCodigo">{{ c.tiene_codigo ? 'Generar código nuevo' : 'Generar código' }}</button>
      </div>
      <div v-if="codigo" class="codigo">
        <span>Código: <strong>{{ codigo }}</strong></span>
        <a v-if="enlaceWhatsApp" :href="enlaceWhatsApp" target="_blank" rel="noopener">Compartir por WhatsApp</a>
      </div>
    </section>

    <div class="pestanas">
      <button :class="{ activa: vista === 'estados' }" @click="vista = 'estados'">Estados de cuenta ({{ c.estados_cuenta.length }})</button>
      <button :class="{ activa: vista === 'ventas' }" @click="vista = 'ventas'">Ventas ({{ c.ventas.length }})</button>
      <button :class="{ activa: vista === 'pagos' }" @click="vista = 'pagos'">Pagos ({{ c.pagos.length }})</button>
    </div>

    <template v-if="vista === 'estados'">
      <label class="check"><input v-model="ocultarVacios" type="checkbox" /> Ocultar estados de cuenta sin movimientos</label>
      <p v-if="!estados.length" class="panel suave">Todavía no hay estados de cuenta.</p>
      <EstadoCuentaDetalle v-for="ec in estados" :key="ec.id" :ec="{ ...ec, cliente: null }" :nombre="c.nombre" />
    </template>

    <template v-else-if="vista === 'ventas'">
      <p v-if="!c.ventas.length" class="panel suave">Todavía no hay ventas.</p>
      <VentaDetalle v-for="v in c.ventas" :key="v.numero" :venta="{ ...v, cliente: null }">
        <template #acciones>
          <button v-if="v.estado === 'VIGENTE'" class="enlace chico" @click="anularVenta(v)">Anular</button>
        </template>
      </VentaDetalle>
    </template>

    <template v-else>
      <p v-if="!c.pagos.length" class="panel suave">Todavía no hay pagos.</p>
      <PagoDetalle v-for="p in c.pagos" :key="p.numero" :pago="{ ...p, cliente: null }" :moneda="c.moneda">
        <template #acciones>
          <button v-if="p.numero === ultimoPagoValido" class="enlace chico" @click="anularPago(p)">Anular</button>
        </template>
      </PagoDetalle>
    </template>

    <div class="fila baja">
      <button v-if="c.estado === 'ACTIVO'" class="chico" @click="darDeBaja">Dar de baja</button>
      <button v-else class="chico" @click="accion(() => vendedor.reactivar(c.id), 'Cliente reactivado.')">Reactivar cliente</button>
    </div>
  </div>
  <p v-else-if="error" class="aviso">{{ error }}</p>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; margin: 4px 0; }
.portal { gap: 8px; }
.codigo { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; padding: 10px 12px; background: var(--marca-suave); border-radius: 6px; font-size: 16px; }
.codigo strong { letter-spacing: 0.08em; }
.baja { justify-content: flex-end; }
</style>
