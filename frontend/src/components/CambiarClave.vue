<script setup>
// Ventana para que cualquier usuario cambie su propia contraseña.
import { ref, watch } from 'vue'
import { cuenta } from '../api'

const abierto = defineModel({ type: Boolean, default: false })
const actual = ref('')
const nueva = ref('')
const repetida = ref('')
const error = ref('')
const listo = ref(false)
const guardando = ref(false)

watch(abierto, (valor) => {
  if (valor) { actual.value = nueva.value = repetida.value = error.value = ''; listo.value = false }
})

async function guardar() {
  error.value = ''
  if (nueva.value !== repetida.value) { error.value = 'La contraseña nueva y su repetición no coinciden.'; return }
  guardando.value = true
  try {
    await cuenta.cambiarClave(actual.value, nueva.value)
    listo.value = true
  } catch (e) { error.value = e.message } finally { guardando.value = false }
}
</script>

<template>
  <div v-if="abierto" class="fondo" @click.self="abierto = false" @keydown.esc="abierto = false">
    <form class="panel ventana" @submit.prevent="guardar">
      <div class="entre"><h2>Cambiar contraseña</h2><button type="button" class="icono" title="Cerrar" @click="abierto = false">✕</button></div>
      <template v-if="!listo">
        <label class="campo"><span>Contraseña actual</span><input v-model="actual" type="password" autocomplete="current-password" required autofocus /></label>
        <label class="campo"><span>Contraseña nueva <span class="suave">(mínimo 12 caracteres)</span></span><input v-model="nueva" type="password" autocomplete="new-password" minlength="12" maxlength="128" required /></label>
        <label class="campo"><span>Repite la contraseña nueva</span><input v-model="repetida" type="password" autocomplete="new-password" required /></label>
        <p v-if="error" class="aviso">{{ error }}</p>
        <div class="fila"><button class="primario" :disabled="guardando">{{ guardando ? 'Guardando…' : 'Guardar contraseña' }}</button><button type="button" @click="abierto = false">Cancelar</button></div>
      </template>
      <template v-else>
        <p class="aviso info">Listo, tu contraseña se cambió. Úsala la próxima vez que ingreses.</p>
        <div class="fila"><button type="button" class="primario" @click="abierto = false">Cerrar</button></div>
      </template>
    </form>
  </div>
</template>

<style scoped>
.fondo { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; padding: 16px; background: rgb(28 26 58 / 0.45); backdrop-filter: blur(2px); }
.ventana { width: min(420px, 100%); box-shadow: var(--sombra-alta); }
</style>
