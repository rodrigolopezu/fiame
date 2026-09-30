<script setup>
import { ref } from 'vue'
import Calculadoras from './components/Calculadoras.vue'
import Simulador from './components/Simulador.vue'

const vista = ref('simulador')
</script>

<template>
  <header class="cabecera">
    <div>
      <h1>FiaMe</h1>
      <p class="suave chico">Simulador del crédito de un cliente · dinero a 2 decimales, tasas a 7 decimales, año de 360 días</p>
    </div>
    <nav class="pestanas">
      <button :class="{ activa: vista === 'simulador' }" @click="vista = 'simulador'">Simulador</button>
      <button :class="{ activa: vista === 'calculadoras' }" @click="vista = 'calculadoras'">Calculadoras</button>
    </nav>
  </header>
  <div class="contenido">
    <Simulador v-show="vista === 'simulador'" />
    <Calculadoras v-if="vista === 'calculadoras'" />
  </div>
</template>

<style scoped>
.cabecera {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
  flex-wrap: wrap;
  padding: 14px 20px 0;
  background: var(--panel);
  border-bottom: 1px solid var(--borde);
}
h1 { font-size: 20px; color: var(--marca); }
.cabecera .pestanas { border-bottom: none; }
.contenido { padding: 16px 20px 40px; max-width: 1600px; margin: 0 auto; }
@media (max-width: 600px) { .cabecera, .contenido { padding-left: 12px; padding-right: 12px; } }
</style>
