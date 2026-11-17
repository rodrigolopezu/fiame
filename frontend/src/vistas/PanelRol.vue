<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sesion, cerrar } from '../sesion'
import { superadmin } from '../api'

const router = useRouter()
const esSuperadmin = computed(() => sesion.rol === 'SUPERADMIN')
const tiendas = ref([])
const cargando = ref(false)
const guardando = ref(false)
const error = ref('')
const exito = ref('')
const form = ref(nuevoFormulario())
const admins = ref({})
const adminExtra = ref({ tiendaId: '', usuario: '', clave: '' })

function nuevoFormulario() {
  return { nombre: '', giro: '', documento: '', telefono: '', direccion: '', moneda: 'PEN',
    limite_credito: '500.00', max_meses: 6, dia_corte: 20, dia_pago: 26,
    tasa_compensatoria_anual: '24', tasa_moratoria_anual: '36', bloquear_con_vencido: true,
    admin_usuario: '', admin_clave: '' }
}
function salir() { cerrar(); router.replace('/login') }
async function cargar() {
  if (!esSuperadmin.value) return
  cargando.value = true
  try { tiendas.value = await superadmin.tiendas() }
  catch (e) { error.value = e.message }
  finally { cargando.value = false }
}
async function crear() {
  error.value = ''; exito.value = ''; guardando.value = true
  try {
    const datos = { ...form.value, documento: form.value.documento || null,
      telefono: form.value.telefono || null, direccion: form.value.direccion || null }
    const resultado = await superadmin.crearTienda(datos)
    exito.value = `Tienda ${resultado.tienda.nombre} creada con administrador ${resultado.administrador.usuario}.`
    form.value = nuevoFormulario()
    await cargar()
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}
async function verAdmins(tiendaId) {
  error.value = ''
  try { admins.value = { ...admins.value, [tiendaId]: await superadmin.administradores(tiendaId) } }
  catch (e) { error.value = e.message }
}
async function crearAdmin() {
  error.value = ''; exito.value = ''; guardando.value = true
  try {
    const id = Number(adminExtra.value.tiendaId)
    const nuevo = await superadmin.crearAdministrador(id, {
      usuario: adminExtra.value.usuario, clave: adminExtra.value.clave
    })
    exito.value = `Administrador ${nuevo.usuario} registrado.`
    adminExtra.value = { tiendaId: '', usuario: '', clave: '' }
    await verAdmins(id)
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}
onMounted(cargar)
</script>

<template>
  <main style="max-width:1040px;margin:32px auto;padding:20px;font-family:inherit">
    <header style="display:flex;justify-content:space-between;align-items:center;gap:12px">
      <div><h1>{{ esSuperadmin ? 'Administración general de FiaMe' : 'Administración de tienda' }}</h1>
        <p>Bienvenido, {{ sesion.usuario }}.</p></div>
      <button type="button" @click="salir">Cerrar sesión</button>
    </header>
    <p v-if="!esSuperadmin">Tienda: {{ sesion.tienda }}. El registro de vendedores se implementará en el paso 5.</p>
    <template v-else>
      <p role="alert" v-if="error" style="color:#b91c1c;white-space:pre-line">{{ error }}</p>
      <p role="status" v-if="exito" style="color:#166534">{{ exito }}</p>
      <section style="border:1px solid #bbb;border-radius:12px;padding:20px;margin:20px 0">
        <h2>Registrar tienda y primer administrador</h2>
        <form @submit.prevent="crear" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px">
          <label>Nombre de tienda *<input v-model.trim="form.nombre" required minlength="2" maxlength="120" /></label>
          <label>Giro *<input v-model.trim="form.giro" required minlength="2" maxlength="40" /></label>
          <label>Documento (RUC)<input v-model.trim="form.documento" maxlength="11" /></label>
          <label>Teléfono<input v-model.trim="form.telefono" maxlength="15" /></label>
          <label>Dirección<input v-model.trim="form.direccion" maxlength="200" /></label>
          <label>Moneda<select v-model="form.moneda"><option value="PEN">Soles (PEN)</option><option value="USD">Dólares (USD)</option></select></label>
          <label>Límite de crédito *<input v-model="form.limite_credito" type="number" step="0.01" min="0.01" required /></label>
          <label>Máximo de meses *<input v-model.number="form.max_meses" type="number" min="1" max="36" required /></label>
          <label>Día de corte *<input v-model.number="form.dia_corte" type="number" min="1" max="28" required /></label>
          <label>Día de pago *<input v-model.number="form.dia_pago" type="number" min="1" max="28" required /></label>
          <label>Tasa efectiva anual compensatoria (%) *<input v-model="form.tasa_compensatoria_anual" type="number" step="0.000001" min="0.000001" required /></label>
          <label>Tasa efectiva anual moratoria (%) *<input v-model="form.tasa_moratoria_anual" type="number" step="0.000001" min="0.000001" required /></label>
          <label>Usuario administrador *<input v-model.trim="form.admin_usuario" required minlength="3" maxlength="60" autocomplete="off" /></label>
          <label>Contraseña inicial *<input v-model="form.admin_clave" type="password" required minlength="12" maxlength="128" autocomplete="new-password" /></label>
          <label style="display:flex;align-items:center;gap:8px"><input v-model="form.bloquear_con_vencido" type="checkbox" /> Bloquear clientes con deuda vencida</label>
          <button type="submit" :disabled="guardando" style="padding:10px">{{ guardando ? 'Guardando...' : 'Crear tienda' }}</button>
        </form>
      </section>
      <section style="border:1px solid #bbb;border-radius:12px;padding:20px;margin:20px 0">
        <h2>Tiendas registradas</h2>
        <p v-if="cargando">Cargando tiendas...</p>
        <p v-else-if="!tiendas.length">Todavía no hay tiendas.</p>
        <div v-for="t in tiendas" :key="t.id" style="border-bottom:1px solid #ddd;padding:10px 0">
          <strong>{{ t.nombre }}</strong> · {{ t.giro }} · {{ t.estado }} · ID {{ t.id }}
          <button type="button" style="margin-left:12px" @click="verAdmins(t.id)">Ver administradores</button>
          <ul v-if="admins[t.id]"><li v-for="a in admins[t.id]" :key="a.id">{{ a.usuario }} · {{ a.activo ? 'Activo' : 'Inactivo' }}</li></ul>
        </div>
      </section>
      <section style="border:1px solid #bbb;border-radius:12px;padding:20px;margin:20px 0">
        <h2>Agregar otro administrador a una tienda</h2>
        <form @submit.prevent="crearAdmin" style="display:grid;gap:12px;max-width:420px">
          <label>Tienda<select v-model="adminExtra.tiendaId" required><option disabled value="">Selecciona una tienda</option><option v-for="t in tiendas.filter(t => t.estado === 'ACTIVA')" :key="t.id" :value="t.id">{{ t.nombre }}</option></select></label>
          <label>Usuario<input v-model.trim="adminExtra.usuario" required minlength="3" maxlength="60" /></label>
          <label>Contraseña inicial<input v-model="adminExtra.clave" type="password" minlength="12" maxlength="128" required autocomplete="new-password" /></label>
          <button type="submit" :disabled="guardando">Registrar administrador</button>
        </form>
      </section>
    </template>
  </main>
</template>
