<script setup>
// Semáforo del score crediticio privado (solo lo ve el vendedor).
defineProps({ score: { type: Object, required: true }, detalle: { type: Boolean, default: false } })

const COLORES = { VERDE: 'verde', AMARILLO: 'amarillo', ROJO: 'rojo', SIN_HISTORIAL: 'gris' }
const TEXTO = { VERDE: 'Buen pagador', AMARILLO: 'Atención', ROJO: 'Riesgo alto', SIN_HISTORIAL: 'Sin historial' }
</script>

<template>
  <span class="semaforo" :class="COLORES[score.semaforo]" :title="`Score ${score.puntaje}/100 · ${TEXTO[score.semaforo]}`">
    <span class="luz" /> {{ score.puntaje }}<span v-if="detalle" class="texto">· {{ TEXTO[score.semaforo] }}</span>
  </span>
</template>

<style scoped>
.semaforo { display: inline-flex; align-items: center; gap: 5px; font-weight: 650; font-variant-numeric: tabular-nums; white-space: nowrap; }
.luz { width: 10px; height: 10px; border-radius: 50%; background: currentColor; }
.texto { font-weight: 500; }
.verde { color: var(--exito); }
.amarillo { color: var(--alerta); }
.rojo { color: var(--error); }
.gris { color: var(--suave); }
</style>
