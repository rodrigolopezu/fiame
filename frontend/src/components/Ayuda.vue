<script setup>
// Ícono "?" con la explicación del campo (requisito de ayuda en cada campo).
defineProps({ texto: { type: String, required: true } })
</script>

<template>
  <span class="ayuda" tabindex="0" :aria-label="texto">?<span class="globo" role="tooltip">{{ texto }}</span></span>
</template>

<style scoped>
.ayuda {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: var(--lavanda);
  color: var(--marca-fuerte);
  font-size: 10px;
  font-weight: 700;
  cursor: help;
  flex: none;
}
.globo {
  display: none;
  position: absolute;
  z-index: 20;
  top: 20px;
  left: -8px;
  width: 240px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--texto);
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  text-transform: none;
  white-space: normal;
}
.ayuda:hover .globo, .ayuda:focus .globo { display: block; }
</style>
