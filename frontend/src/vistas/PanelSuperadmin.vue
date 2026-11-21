<script setup>
// Panel del superadministrador: da de alta y de baja a las tiendas y gestiona a sus administradores.
// No ve clientes, ventas ni pagos de ninguna tienda.
import { onMounted, ref } from 'vue'
import { superadmin } from '../api'
import MarcoCuenta from '../components/MarcoCuenta.vue'

const tiendas = ref([])
const cargando = ref(false)
const guardando = ref(false)
const error = ref('')
const exito = ref('')
const form = ref(nuevoFormulario())
const admins = ref({}) // tienda_id -> administradores
const abierta = ref(null) // tienda cuyos administradores se están viendo
const adminNuevo = ref({ usuario: '', clave: '' })
const restableciendo = ref(null)
const claveNueva = ref('')

function nuevoFormulario() {
  return {
    nombre: '', giro: '', documento: '', telefono: '', direccion: '', moneda: 'PEN',
    limite_credito: '500.00', max_meses: 6, dia_corte: 20, dia_pago: 26,
    tasa_compensatoria_anual: '24', tasa_moratoria_anual: '36', bloquear_con_vencido: true,
    admin_usuario: '', admin_clave: '',
  }
}

async function cargar() {
  cargando.value = true
  try { tiendas.value = await superadmin.tiendas() }
  catch (e) { error.value = e.message }
  finally { cargando.value = false }
}

async function crear() {
  error.value = ''; exito.value = ''; guardando.value = true
  try {
    const datos = {
      ...form.value, documento: form.value.documento || null,
      telefono: form.value.telefono || null, direccion: form.value.direccion || null,
    }
    const r = await superadmin.crearTienda(datos)
    exito.value = `Tienda ${r.tienda.nombre} creada con su administrador ${r.administrador.usuario}.`
    form.value = nuevoFormulario()
    await cargar()
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}

async function verAdmins(id) {
  error.value = ''
  if (abierta.value === id) { abierta.value = null; return }
  try {
    admins.value = { ...admins.value, [id]: await superadmin.administradores(id) }
    abierta.value = id
    adminNuevo.value = { usuario: '', clave: '' }
    restableciendo.value = null
  } catch (e) { error.value = e.message }
}

async function crearAdmin(id) {
  error.value = ''; exito.value = ''; guardando.value = true
  try {
    const nuevo = await superadmin.crearAdministrador(id, { usuario: adminNuevo.value.usuario, clave: adminNuevo.value.clave })
    exito.value = `Administrador ${nuevo.usuario} registrado.`
    adminNuevo.value = { usuario: '', clave: '' }
    admins.value = { ...admins.value, [id]: await superadmin.administradores(id) }
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}

async function restablecer(tiendaId, a) {
  error.value = ''; exito.value = ''
  try {
    await superadmin.restablecerClave(tiendaId, a.id, claveNueva.value)
    exito.value = `Se cambió la contraseña de ${a.usuario}. Entrégale la nueva.`
    restableciendo.value = null; claveNueva.value = ''
  } catch (e) { error.value = e.message }
}

async function cambiarEstado(t) {
  const baja = t.estado === 'ACTIVA'
  const pregunta = baja
    ? `¿Dar de baja a ${t.nombre}? Su personal perderá el acceso de inmediato y el portal de sus clientes quedará bloqueado. No se borra ningún dato y puedes reactivarla.`
    : `¿Reactivar a ${t.nombre}?`
  if (!confirm(pregunta)) return
  error.value = ''; exito.value = ''
  try {
    await superadmin.cambiarEstadoTienda(t.id, !baja)
    exito.value = baja ? `${t.nombre} fue dada de baja.` : `${t.nombre} fue reactivada.`
    await cargar()
  } catch (e) { error.value = e.message }
}

onMounted(cargar)
</script>

<template>
  <MarcoCuenta titulo="Administración general de FiaMe" subtitulo="Das de alta a las tiendas y a sus administradores. No ves los clientes, ventas ni pagos de ninguna tienda.">
    <p v-if="error" class="aviso" role="alert">{{ error }}</p>
    <p v-if="exito" class="aviso info" role="status">{{ exito }}</p>

    <section class="panel">
      <h2>Registrar tienda y su administrador</h2>
      <form class="formulario" @submit.prevent="crear">
        <h4>Datos de la tienda</h4>
        <div class="grilla">
          <label class="campo"><span>Nombre *</span><input v-model.trim="form.nombre" required minlength="2" maxlength="120" /></label>
          <label class="campo"><span>Giro *</span><input v-model.trim="form.giro" required minlength="2" maxlength="40" placeholder="Bodega, frutería…" /></label>
          <label class="campo"><span>DNI o RUC</span><input v-model.trim="form.documento" maxlength="11" inputmode="numeric" /></label>
          <label class="campo"><span>Teléfono</span><input v-model.trim="form.telefono" maxlength="15" /></label>
          <label class="campo ancho"><span>Dirección</span><input v-model.trim="form.direccion" maxlength="200" /></label>
        </div>
        <h4>Valores por defecto del crédito</h4>
        <div class="grilla">
          <label class="campo"><span>Moneda</span><select v-model="form.moneda"><option value="PEN">Soles (PEN)</option><option value="USD">Dólares (USD)</option></select></label>
          <label class="campo"><span>Límite de crédito *</span><input v-model="form.limite_credito" inputmode="decimal" required /></label>
          <label class="campo"><span>Máximo de cuotas *</span><input v-model.number="form.max_meses" type="number" min="1" max="36" required /></label>
          <label class="campo"><span>Día de corte *</span><input v-model.number="form.dia_corte" type="number" min="1" max="28" required /></label>
          <label class="campo"><span>Día de pago *</span><input v-model.number="form.dia_pago" type="number" min="1" max="28" required /></label>
          <label class="campo"><span>TEA compensatoria (%) *</span><input v-model="form.tasa_compensatoria_anual" inputmode="decimal" required /></label>
          <label class="campo"><span>TEA moratoria (%) *</span><input v-model="form.tasa_moratoria_anual" inputmode="decimal" required /></label>
        </div>
        <label class="check"><input v-model="form.bloquear_con_vencido" type="checkbox" /> No vender a clientes con estados de cuenta vencidos</label>
        <h4>Administrador de la tienda (el dueño)</h4>
        <div class="grilla">
          <label class="campo"><span>Usuario *</span><input v-model.trim="form.admin_usuario" required minlength="3" maxlength="60" autocomplete="off" /></label>
          <label class="campo"><span>Contraseña inicial *</span><input v-model="form.admin_clave" type="password" required minlength="12" maxlength="128" autocomplete="new-password" placeholder="Mínimo 12 caracteres" /></label>
        </div>
        <div class="fila"><button class="primario" :disabled="guardando">{{ guardando ? 'Creando…' : 'Crear tienda' }}</button></div>
      </form>
    </section>

    <section class="panel">
      <h2>Tiendas registradas</h2>
      <p v-if="cargando" class="suave">Cargando…</p>
      <p v-else-if="!tiendas.length" class="suave">Todavía no hay tiendas.</p>
      <div v-else class="tabla-scroll">
        <table>
          <thead><tr><th>Tienda</th><th>Giro</th><th>Estado</th><th></th></tr></thead>
          <tbody>
            <template v-for="t in tiendas" :key="t.id">
              <tr>
                <td><strong>{{ t.nombre }}</strong></td>
                <td class="suave">{{ t.giro }}</td>
                <td><span class="etiqueta" :class="t.estado === 'ACTIVA' ? '' : 'error'">{{ t.estado === 'ACTIVA' ? 'Activa' : 'De baja' }}</span></td>
                <td class="num">
                  <button class="enlace chico" @click="verAdmins(t.id)">{{ abierta === t.id ? 'Ocultar administradores' : 'Administradores' }}</button>
                  <button class="enlace chico" @click="cambiarEstado(t)">{{ t.estado === 'ACTIVA' ? 'Dar de baja' : 'Reactivar' }}</button>
                </td>
              </tr>
              <tr v-if="abierta === t.id">
                <td colspan="4">
                  <div class="detalle">
                    <h4>Administradores de {{ t.nombre }}</h4>
                    <p v-if="!admins[t.id]?.length" class="suave chico">Esta tienda no tiene administradores.</p>
                    <ul class="lista">
                      <li v-for="a in admins[t.id]" :key="a.id">
                        <span><strong>{{ a.usuario }}</strong> <span class="etiqueta" :class="a.activo ? '' : 'neutra'">{{ a.activo ? 'Activo' : 'Inactivo' }}</span></span>
                        <span>
                          <form v-if="restableciendo === a.id" class="fila" @submit.prevent="restablecer(t.id, a)">
                            <input v-model="claveNueva" class="corto" type="password" minlength="12" maxlength="128" required autocomplete="new-password" placeholder="Contraseña nueva (mínimo 12)" />
                            <button class="primario">Guardar</button>
                            <button type="button" @click="restableciendo = null">Cancelar</button>
                          </form>
                          <button v-else class="enlace chico" @click="restableciendo = a.id; claveNueva = ''">Restablecer contraseña</button>
                        </span>
                      </li>
                    </ul>
                    <form v-if="t.estado === 'ACTIVA'" class="fila agregar" @submit.prevent="crearAdmin(t.id)">
                      <label class="campo"><span>Nuevo administrador</span><input v-model.trim="adminNuevo.usuario" required minlength="3" maxlength="60" placeholder="Usuario" autocomplete="off" /></label>
                      <label class="campo"><span>Contraseña inicial</span><input v-model="adminNuevo.clave" type="password" minlength="12" maxlength="128" required autocomplete="new-password" placeholder="Mínimo 12 caracteres" /></label>
                      <button class="primario" :disabled="guardando">Agregar</button>
                    </form>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </MarcoCuenta>
</template>

<style scoped>
.formulario { display: flex; flex-direction: column; gap: 12px; }
.formulario .grilla { grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); }
.ancho { grid-column: span 2; }
.detalle { display: flex; flex-direction: column; gap: 10px; padding: 6px 0; }
.lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.lista li { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 8px 0; border-bottom: 1px solid var(--linea); }
.lista li:last-child { border-bottom: none; }
.agregar { align-items: flex-end; }
.corto { max-width: 260px; }
</style>
