<script setup>
// Término financiero con su definición corta (solo en la vista detallada).
import { GLOSARIO } from '../glosario'
import Ayuda from './Ayuda.vue'

defineProps({ clave: { type: String, required: true } })
</script>

<template>
  <span class="termino"><slot /><Ayuda :texto="GLOSARIO[clave]" /></span>
</template>

<style scoped>
.termino { display: inline-flex; align-items: center; gap: 4px; }
</style>
