<script setup>
// Tipo, periodo, valor y capitalización de una tasa (sección 1.1 de la especificación).
import { PERIODOS } from '../formato'
import Ayuda from './Ayuda.vue'

const tasa = defineModel({ type: Object, required: true })
defineProps({ titulo: { type: String, default: 'Tasa' } })

function cambiarTipo(tipo) {
  tasa.value = { ...tasa.value, tipo, capitalizacion: tipo === 'NOMINAL' ? tasa.value.capitalizacion || 'DIARIA' : null }
}
</script>

<template>
  <fieldset class="tasa">
    <legend>{{ titulo }}</legend>
    <div class="grilla">
      <label class="campo">
        <span>Tipo <Ayuda texto="Efectiva: ya incluye la capitalización. Nominal: requiere indicar cada cuánto capitaliza." /></span>
        <select :value="tasa.tipo" @change="cambiarTipo($event.target.value)">
          <option value="EFECTIVA">Efectiva</option>
          <option value="NOMINAL">Nominal</option>
        </select>
      </label>
      <label class="campo">
        <span>Periodo <Ayuda texto="Periodo en que está expresada la tasa. Ej.: anual para una TEA o TNA." /></span>
        <select v-model="tasa.periodo">
          <option v-for="[valor, nombre] in PERIODOS" :key="valor" :value="valor">{{ nombre }}</option>
        </select>
      </label>
      <label class="campo">
        <span>Valor (%) <Ayuda texto="Valor de la tasa en porcentaje, hasta 7 decimales. Ej.: 24 para una TEA de 24 %." /></span>
        <input v-model="tasa.valor" inputmode="decimal" placeholder="24" />
      </label>
      <label v-if="tasa.tipo === 'NOMINAL'" class="campo">
        <span>Capitalización <Ayuda texto="Cada cuánto se capitalizan los intereses. No puede ser mayor que el periodo de la tasa. Por defecto, diaria." /></span>
        <select v-model="tasa.capitalizacion">
          <option v-for="[valor, nombre] in PERIODOS" :key="valor" :value="valor">{{ nombre }}</option>
        </select>
      </label>
    </div>
  </fieldset>
</template>

<style scoped>
.tasa { border: 1px solid var(--borde); border-radius: 6px; padding: 8px 10px 10px; margin: 0; }
legend { font-size: 12px; font-weight: 600; padding: 0 4px; }
</style>
