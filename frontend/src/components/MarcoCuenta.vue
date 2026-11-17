<script setup>
// Marco de las pantallas de administración (dueño y superadmin): misma barra que la del vendedor.
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { cerrar, sesion } from '../sesion'
import CambiarClave from './CambiarClave.vue'
import Logo from './Logo.vue'

defineProps({ titulo: { type: String, required: true }, subtitulo: { type: String, default: '' } })
const router = useRouter()
const cambiandoClave = ref(false)

function salir() {
  cerrar()
  router.replace('/login')
}
</script>

<template>
  <div class="marco">
    <header class="barra">
      <div class="izquierda">
        <Logo :tamano="30" />
        <span class="suave chico">{{ sesion.tienda || 'Administración general' }}</span>
      </div>
      <div class="fila">
        <span class="suave chico">{{ sesion.usuario }}</span>
        <button class="chico" @click="cambiandoClave = true">Cambiar contraseña</button>
        <button class="chico" @click="salir">Cerrar sesión</button>
      </div>
    </header>
    <main class="contenido">
      <div>
        <h1>{{ titulo }}</h1>
        <p v-if="subtitulo" class="suave">{{ subtitulo }}</p>
      </div>
      <slot />
    </main>
    <CambiarClave v-model="cambiandoClave" />
  </div>
</template>

<style scoped>
.marco { min-height: 100vh; display: flex; flex-direction: column; }
.barra {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 10px 20px; background: rgb(255 255 255 / 0.9); backdrop-filter: blur(8px); border-bottom: 1px solid var(--borde);
  position: sticky; top: 0; z-index: 20;
}
.izquierda { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.contenido { padding: 20px; max-width: 1040px; width: 100%; margin: 0 auto; flex: 1; display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
@media (max-width: 700px) {
  .barra { padding: 8px 12px; }
  .contenido { padding: 14px 12px; }
}
</style>
