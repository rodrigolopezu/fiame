<script setup>
// La TEA elevada a la fracción de año: (1 + TEA)^(días/360). Es la única forma en que se
// muestra una tasa para un plazo: nunca como una "tasa efectiva a N días".
import { teaTexto } from '../formato'

defineProps({
  tea: { type: [String, Number], required: true },
  dias: { type: [String, Number], required: true },
  menosUno: { type: Boolean, default: false }, // para calcular el interés: (1 + TEA)^(d/360) − 1
})
</script>

<template>
  <span class="potencia">(1 + {{ teaTexto(tea) }})<sup>{{ dias }}/360</sup><template v-if="menosUno"> − 1</template></span>
</template>

<style scoped>
.potencia { white-space: nowrap; font-variant-numeric: tabular-nums; }
sup { font-size: 0.75em; line-height: 0; }
</style>
