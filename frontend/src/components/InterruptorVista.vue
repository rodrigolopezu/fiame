<script setup>
// Interruptor general entre la vista simple y la detallada.
import { vista } from '../vista'
import Ayuda from './Ayuda.vue'
</script>

<template>
  <span class="interruptor" role="group" aria-label="Nivel de detalle">
    <button type="button" :class="{ activo: vista.simple }" :aria-pressed="vista.simple" @click="vista.simple = true">Simple</button>
    <button type="button" :class="{ activo: !vista.simple }" :aria-pressed="!vista.simple" @click="vista.simple = false">Detallada</button>
    <Ayuda texto="Simple: en palabras de todos los días. Detallada: todas las cifras y términos financieros. Los datos y lo que puedes hacer son los mismos." />
  </span>
</template>

<style scoped>
.interruptor { display: inline-flex; align-items: center; gap: 2px; padding: 3px; border-radius: 999px; background: var(--gris-suave); }
button { border: none; background: none; border-radius: 999px; padding: 4px 12px; font-size: 12px; color: var(--suave); box-shadow: none; }
button:hover { color: var(--texto); }
button.activo { background: var(--panel); color: var(--marca-fuerte); box-shadow: 0 1px 3px rgb(28 26 58 / 0.12); }
.interruptor > :last-child { margin: 0 6px 0 4px; }
</style>
