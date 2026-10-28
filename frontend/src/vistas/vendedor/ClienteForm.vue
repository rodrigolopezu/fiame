<script setup>
// Alta y edición de un cliente. Las condiciones de crédito se precargan con los
// valores por defecto de la tienda.
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import CampoTasa from '../../components/CampoTasa.vue'
import { tasa as fTasa } from '../../formato'
import { tasaSimple } from '../../lenguaje'
import { vista } from '../../vista'

const props = defineProps({ id: { type: String, default: null } })
const router = useRouter()
const editando = computed(() => !!props.id)
const datos = ref(null)
const puedeCambiarCiclo = ref(true)
const teas = ref({ compensatoria: null, moratoria: null })
const error = ref('')
const guardando = ref(false)

function tasaEntrada(t) {
  return { tipo: t.tipo, periodo: t.periodo, valor: String(t.valor), capitalizacion: t.capitalizacion }
}

onMounted(async () => {
  try {
    if (editando.value) {
      const c = await vendedor.cliente(props.id)
      puedeCambiarCiclo.value = c.puede_cambiar_ciclo
      datos.value = {
        nombres: c.nombres, apellidos: c.apellidos, tipo_documento: c.tipo_documento,
        numero_documento: c.numero_documento, telefono: c.telefono || '', email: c.email || '',
        direccion: c.direccion || '', moneda: c.moneda, limite_credito: c.limite_credito, max_meses: c.max_meses,
        dia_corte: c.dia_corte, dia_pago: c.dia_pago,
        tasa_compensatoria: tasaEntrada(c.tasa_compensatoria), tasa_moratoria: tasaEntrada(c.tasa_moratoria),
      }
    } else {
      const { configuracion: cfg } = await vendedor.tienda()
      datos.value = {
        nombres: '', apellidos: '', tipo_documento: 'DNI', numero_documento: '', telefono: '', email: '',
        direccion: '', moneda: cfg.moneda, limite_credito: cfg.limite_credito, max_meses: cfg.max_meses,
        dia_corte: cfg.dia_corte, dia_pago: cfg.dia_pago,
        tasa_compensatoria: tasaEntrada(cfg.tasa_compensatoria), tasa_moratoria: tasaEntrada(cfg.tasa_moratoria),
      }
    }
  } catch (e) {
    error.value = e.message
  }
})

// TEA equivalente que se le informará al cliente (R14), calculada por el backend.
let temporizador
watch(() => datos.value && [datos.value.tasa_compensatoria, datos.value.tasa_moratoria], () => {
  clearTimeout(temporizador)
  temporizador = setTimeout(async () => {
    for (const clave of ['compensatoria', 'moratoria']) {
      try {
        const r = await api.tasa({ tasa: datos.value[`tasa_${clave}`], dias: 360 })
        teas.value[clave] = r.tea
      } catch { teas.value[clave] = null }
    }
  }, 300)
}, { deep: true })

async function guardar() {
  guardando.value = true
  error.value = ''
  try {
    const c = editando.value ? await vendedor.editarCliente(props.id, datos.value) : await vendedor.crearCliente(datos.value)
    router.push(`/vendedor/clientes/${c.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <h1>{{ editando ? 'Editar cliente' : 'Nuevo cliente' }}</h1>
    <p v-if="error" class="aviso">{{ error }}</p>
    <form v-if="datos" class="formulario" @submit.prevent="guardar">
      <section class="panel">
        <h2>Datos personales</h2>
        <div class="grilla">
          <label class="campo"><span>Nombres</span><input v-model="datos.nombres" required /></label>
          <label class="campo"><span>Apellidos</span><input v-model="datos.apellidos" required /></label>
          <label class="campo">
            <span>Tipo de documento</span>
            <select v-model="datos.tipo_documento"><option>DNI</option><option value="CE">Carné de extranjería</option><option>RUC</option></select>
          </label>
          <label class="campo">
            <span>N.° de documento <Ayuda texto="DNI: 8 dígitos. RUC: 11 dígitos. Carné de extranjería: 9 a 12 dígitos. No puede repetirse en la tienda." /></span>
            <input v-model="datos.numero_documento" inputmode="numeric" required />
          </label>
          <label class="campo"><span>Teléfono <Ayuda texto="Para compartirle por WhatsApp el código de su estado de cuenta." /></span><input v-model="datos.telefono" inputmode="tel" /></label>
          <label class="campo"><span>Correo</span><input v-model="datos.email" type="email" /></label>
          <label class="campo ancho"><span>Dirección</span><input v-model="datos.direccion" /></label>
        </div>
      </section>

      <section class="panel">
        <h2>Condiciones de crédito</h2>
        <p v-if="!puedeCambiarCiclo" class="aviso info chico">El cliente tiene deuda pendiente: la moneda y los días de corte y pago no se pueden cambiar hasta que la cancele.</p>
        <div class="grilla">
          <label class="campo">
            <span>Moneda <Ayuda texto="Moneda en la que el cliente debe. Los productos en otra moneda se convierten con el tipo de cambio de la venta." /></span>
            <select v-model="datos.moneda" :disabled="!puedeCambiarCiclo"><option value="PEN">Soles (PEN)</option><option value="USD">Dólares (USD)</option></select>
          </label>
          <label class="campo">
            <span>Límite de crédito <Ayuda texto="Deuda máxima permitida. Cada venta consume su precio de lista y se libera al pagar." /></span>
            <input v-model="datos.limite_credito" inputmode="decimal" required />
          </label>
          <label class="campo">
            <span>Máximo de cuotas <Ayuda texto="Número máximo de cuotas que se le puede dar (1 a 36)." /></span>
            <input v-model.number="datos.max_meses" type="number" min="1" max="36" required />
          </label>
          <label class="campo">
            <span>Día de corte <Ayuda texto="Día del mes en que se cierra su ciclo (1 a 28)." /></span>
            <input v-model.number="datos.dia_corte" type="number" min="1" max="28" :disabled="!puedeCambiarCiclo" required />
          </label>
          <label class="campo">
            <span>Día de pago <Ayuda texto="Día del mes en que vence su estado de cuenta (1 a 28): la primera fecha con ese día después del corte." /></span>
            <input v-model.number="datos.dia_pago" type="number" min="1" max="28" :disabled="!puedeCambiarCiclo" required />
          </label>
        </div>
        <CampoTasa v-model="datos.tasa_compensatoria" :titulo="vista.simple ? 'Interés por el crédito' : 'Tasa compensatoria'" />
        <p class="chico suave">
          <template v-if="vista.simple">Equivale a <strong>{{ teas.compensatoria ? `${tasaSimple(teas.compensatoria)} al año` : '—' }}</strong>; así se le informa al cliente.</template>
          <template v-else>TEA equivalente informada al cliente: <strong>{{ teas.compensatoria ? fTasa(teas.compensatoria) : '—' }}</strong></template>
        </p>
        <CampoTasa v-model="datos.tasa_moratoria" :titulo="vista.simple ? 'Recargo por atraso' : 'Tasa moratoria'" />
        <p class="chico suave">
          <template v-if="vista.simple">Equivale a <strong>{{ teas.moratoria ? `${tasaSimple(teas.moratoria)} al año` : '—' }}</strong>.</template>
          <template v-else>TEA moratoria equivalente: <strong>{{ teas.moratoria ? fTasa(teas.moratoria) : '—' }}</strong></template>
        </p>
        <p v-if="editando" class="chico suave">Si cambias las tasas, solo aplican a las ventas nuevas: las anteriores conservan las condiciones con que se hicieron.</p>
      </section>

      <div class="fila">
        <button class="primario" :disabled="guardando">{{ guardando ? 'Guardando…' : 'Guardar' }}</button>
        <button type="button" @click="router.back()">Cancelar</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.pagina, .formulario { display: flex; flex-direction: column; gap: 14px; max-width: 900px; }
h1 { font-size: 22px; }
.ancho { grid-column: span 2; }
</style>
