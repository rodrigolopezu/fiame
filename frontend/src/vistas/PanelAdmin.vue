<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sesion, cerrar } from '../sesion'
import { admin } from '../api'
import ClientesAdmin from './ClientesAdmin.vue'
const router = useRouter()
const vendedores = ref([])
const usuario = ref('')
const clave = ref('')
const error = ref('')
const mensaje = ref('')
const cargando = ref(false)
const guardando = ref(false)
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
    mensaje.value = `Vendedor ${nuevo.usuario} registrado.`
    usuario.value = ''; clave.value = ''
    await cargar()
  } catch (e) { error.value = e.message }
  finally { guardando.value = false }
}
async function alternar(v) {
  error.value = ''; mensaje.value = ''
  try {
    await admin.cambiarEstadoVendedor(v.id, !v.activo)
    mensaje.value = `Estado de ${v.usuario} actualizado.`
    await cargar()
  } catch (e) { error.value = e.message }
}
function salir() { cerrar(); router.replace('/login') }
onMounted(cargar)
</script>
<template>
  <main style="max-width:960px;margin:32px auto;padding:24px">
    <header style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>Administración de tienda</h1><p>{{ sesion.tienda }} · {{ sesion.usuario }}</p></div>
      <button type="button" @click="salir">Cerrar sesión</button>
    </header>
    <p v-if="error" role="alert" style="color:#b91c1c">{{ error }}</p>
    <p v-if="mensaje" role="status" style="color:#166534">{{ mensaje }}</p>
    <section style="border:1px solid #bbb;border-radius:12px;padding:20px;margin:20px 0">
      <h2>Registrar vendedor</h2>
      <form @submit.prevent="crear" style="display:grid;gap:12px;max-width:420px">
        <label>Usuario <input v-model.trim="usuario" required minlength="3" maxlength="60" autocomplete="off" /></label>
        <label>Contraseña inicial <input v-model="clave" type="password" required minlength="12" maxlength="128" autocomplete="new-password" /></label>
        <button type="submit" :disabled="guardando">{{ guardando ? 'Registrando...' : 'Registrar vendedor' }}</button>
      </form>
    </section>
    <section style="border:1px solid #bbb;border-radius:12px;padding:20px">
      <h2>Vendedores de mi tienda</h2>
      <p v-if="cargando">Cargando...</p>
      <p v-else-if="!vendedores.length">No hay vendedores registrados.</p>
      <ul v-else>
        <li v-for="v in vendedores" :key="v.id" style="margin:12px 0">
          {{ v.usuario }} — {{ v.activo ? 'Activo' : 'Inactivo' }}
          <button type="button" style="margin-left:12px" @click="alternar(v)">{{ v.activo ? 'Desactivar' : 'Activar' }}</button>
        </li>
      </ul>
    </section>
    <ClientesAdmin />
  </main>
</template>
