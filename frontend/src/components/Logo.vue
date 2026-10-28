<script setup>
// Marca de FiaMe: un anillo segmentado (como el menú principal) con un segmento en menta,
// que representa lo ya pagado, y la "F" al centro.
import { useId } from 'vue'

defineProps({
  tamano: { type: Number, default: 32 },
  texto: { type: Boolean, default: true },
  claro: { type: Boolean, default: false },
})
const id = useId()
</script>

<template>
  <span class="logo" :class="{ claro }">
    <svg :width="tamano" :height="tamano" viewBox="0 0 40 40" aria-hidden="true">
      <defs>
        <linearGradient :id="`${id}-g`" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#6c4dff" />
          <stop offset="1" stop-color="#4527d9" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" :fill="`url(#${id}-g)`" />
      <g transform="rotate(-90 20 20)" fill="none" stroke-width="3.6" stroke-linecap="round">
        <circle cx="20" cy="20" r="11" stroke="#ffffff" stroke-opacity="0.95" stroke-dasharray="13.2 4.08" />
        <circle cx="20" cy="20" r="11" stroke="#3ee0ae" stroke-dasharray="13.2 55.9" />
      </g>
      <path d="M17.2 15.2h6.2M17.2 15.2v9.6M17.2 19.8h4.6" stroke="#ffffff" stroke-width="2.4"
            stroke-linecap="round" stroke-linejoin="round" fill="none" />
    </svg>
    <span v-if="texto" class="palabra" :style="{ fontSize: `${Math.round(tamano * 0.66)}px` }">Fia<b>Me</b></span>
  </span>
</template>

<style scoped>
.logo { display: inline-flex; align-items: center; gap: 0.45em; text-decoration: none; }
.palabra { font-weight: 800; letter-spacing: -0.03em; color: var(--texto); line-height: 1; }
.palabra b { font-weight: 800; color: var(--marca); }
.claro .palabra { color: #fff; }
.claro .palabra b { color: #bfb2ff; }
</style>
