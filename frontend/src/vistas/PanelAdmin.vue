<script setup>
// Panel del dueño de la tienda: registra a su equipo de vendedores y consulta los clientes.
import { onMounted, ref } from 'vue'
import { admin } from '../api'
import MarcoCuenta from '../components/MarcoCuenta.vue'
import { sesion } from '../sesion'
import ClientesAdmin from './ClientesAdmin.vue'

const vendedores = ref([])
const usuario = ref('')
const clave = ref('')
const error = ref('')
const mensaje = ref('')
const cargando = ref(false)
const guardando = ref(false)
const restableciendo = ref(null)
const claveNueva = ref('')

const fechaCorta = (iso) => (iso ? new Date(iso).toLocaleDateString('es-PE') : '—')

async function cargar() {
  cargando.value = true
  try { vendedores.value = await admin.vendedores() }
  catch (e) { error.value = e.message }
  finally { cargando.value = false }
}

async function crear() {
  error.value = ''; mensaje.value = ''; guardando.value = true
  try {
    const nuevo = await admin.crearVendedor({ usuario: usuario.value.trim(), clave: clave.value })
    mensaje.value = `Vendedor ${nuevo.usuario} registrado. Entrégale su usuario y su contraseña inicial.`
    usuario.value = ''; clave.value = ''
    await cargar()
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}

async function alternar(v) {
  error.value = ''; mensaje.value = ''
  try {
    await admin.cambiarEstadoVendedor(v.id, !v.activo)
    mensaje.value = `${v.usuario} ahora está ${v.activo ? 'inactivo y ya no puede ingresar' : 'activo'}.`
    await cargar()
  } catch (e) { error.value = e.message }
}

function abrirRestablecer(v) {
  restableciendo.value = restableciendo.value === v.id ? null : v.id
  claveNueva.value = ''
}

async function restablecer(v) {
  error.value = ''; mensaje.value = ''
  try {
    await admin.restablecerClave(v.id, claveNueva.value)
    mensaje.value = `Se cambió la contraseña de ${v.usuario}. Entrégale la nueva.`
    restableciendo.value = null
  } catch (e) { error.value = e.message }
}

onMounted(cargar)
</script>

<template>
  <MarcoCuenta titulo="Administración de la tienda" :subtitulo="`${sesion.tienda} · ${sesion.usuario}`">
    <p class="aviso info">
      Desde aquí administras a tu equipo. Para vender y cobrar necesitas tu propia cuenta de <strong>vendedor</strong>:
      regístrala abajo y entra con ella. Todos los vendedores ven los mismos clientes, ventas y pagos de la tienda;
      cada venta y cada pago queda a nombre de quien lo registró.
    </p>
    <p v-if="error" class="aviso" role="alert">{{ error }}</p>
    <p v-if="mensaje" class="aviso info" role="status">{{ mensaje }}</p>

    <section class="panel">
      <h2>Registrar vendedor</h2>
      <form class="formulario" @submit.prevent="crear">
        <label class="campo"><span>Usuario</span><input v-model.trim="usuario" required minlength="3" maxlength="60" autocomplete="off" placeholder="Ej.: caja1" /></label>
        <label class="campo"><span>Contraseña inicial <span class="suave">(mínimo 12 caracteres)</span></span><input v-model="clave" type="password" required minlength="12" maxlength="128" autocomplete="new-password" /></label>
        <button class="primario" :disabled="guardando">{{ guardando ? 'Registrando…' : 'Registrar vendedor' }}</button>
      </form>
    </section>

    <section class="panel">
      <h2>Vendedores de mi tienda</h2>
      <p v-if="cargando" class="suave">Cargando…</p>
      <p v-else-if="!vendedores.length" class="suave">Todavía no hay vendedores registrados.</p>
      <div v-else class="tabla-scroll">
        <table>
          <thead><tr><th>Usuario</th><th>Estado</th><th>Registrado</th><th></th></tr></thead>
          <tbody>
            <template v-for="v in vendedores" :key="v.id">
              <tr>
                <td><strong>{{ v.usuario }}</strong></td>
                <td><span class="etiqueta" :class="v.activo ? '' : 'neutra'">{{ v.activo ? 'Activo' : 'Inactivo' }}</span></td>
                <td class="suave">{{ fechaCorta(v.creado_en) }}</td>
                <td class="num">
                  <button class="enlace chico" @click="abrirRestablecer(v)">Restablecer contraseña</button>
                  <button class="enlace chico" @click="alternar(v)">{{ v.activo ? 'Desactivar' : 'Activar' }}</button>
                </td>
              </tr>
              <tr v-if="restableciendo === v.id">
                <td colspan="4">
                  <form class="fila" @submit.prevent="restablecer(v)">
                    <input v-model="claveNueva" class="corto" type="password" minlength="12" maxlength="128" required autocomplete="new-password" placeholder="Contraseña nueva (mínimo 12)" />
                    <button class="primario">Guardar</button>
                    <button type="button" @click="restableciendo = null">Cancelar</button>
                  </form>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <ClientesAdmin />
  </MarcoCuenta>
</template>

<style scoped>
.formulario { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); align-items: end; }
.corto { max-width: 280px; }
</style>
