<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { sesion, cerrar } from '../sesion'
const router = useRouter()
const titulo = computed(() => sesion.rol === 'SUPERADMIN' ? 'Administración general de FiaMe' : 'Administración de tienda')
function salir() { cerrar(); router.replace('/login') }
</script>
<template>
  <main style="max-width:900px;margin:48px auto;padding:24px">
    <h1>{{ titulo }}</h1>
    <p>Bienvenido, {{ sesion.usuario }}.</p>
    <p v-if="sesion.tienda">Tienda: {{ sesion.tienda }}</p>
    <p>Tu sesión funciona. La creación de tiendas y vendedores se implementará en el siguiente paso.</p>
    <button @click="salir">Cerrar sesión</button>
  </main>
</template>
