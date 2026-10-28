<script setup>
import { ref } from 'vue'
import Calculadoras from '../../components/Calculadoras.vue'
import Simulador from '../../components/Simulador.vue'
import Logo from '../../components/Logo.vue'

const vista = ref('simulador')
</script>

<template>
  <header class="cabecera">
    <div>
      <h1><RouterLink to="/" class="marca"><Logo :tamano="28" /></RouterLink> <span class="suave">Simulador</span></h1>
      <p class="suave chico">Herramienta de verificación · dinero a 2 decimales, tasas a 7 decimales, año de 360 días</p>
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
h1 { font-size: 20px; }
.marca { text-decoration: none; display: inline-flex; }
h1 { display: flex; align-items: center; gap: 10px; }
.cabecera .pestanas { border-bottom: none; }
.contenido { padding: 16px 20px 40px; max-width: 1600px; margin: 0 auto; }
@media (max-width: 600px) { .cabecera, .contenido { padding-left: 12px; padding-right: 12px; } }
</style>
