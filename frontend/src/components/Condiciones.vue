<script setup>
// Condiciones de crédito del cliente: se fijan al registrarlo.
import Ayuda from './Ayuda.vue'
import CampoTasa from './CampoTasa.vue'

const c = defineModel({ type: Object, required: true })
</script>

<template>
  <section class="panel">
    <h2>Condiciones del cliente</h2>
    <div class="grilla">
      <label class="campo">
        <span>Moneda <Ayuda texto="Moneda en la que el cliente debe. Si un producto está en otra moneda, la venta pide el tipo de cambio." /></span>
        <select v-model="c.moneda">
          <option value="PEN">Soles (PEN)</option>
          <option value="USD">Dólares (USD)</option>
        </select>
      </label>
      <label class="campo">
        <span>Límite de crédito <Ayuda texto="Deuda máxima permitida. Una venta consume su precio de lista y se libera al pagar." /></span>
        <input v-model="c.limite_credito" inputmode="decimal" />
      </label>
      <label class="campo">
        <span>Máx. cuotas <Ayuda texto="Número máximo de cuotas que se le puede dar al cliente (1 a 36)." /></span>
        <input v-model.number="c.max_meses" type="number" min="1" max="36" />
      </label>
      <label class="campo">
        <span>Día de corte <Ayuda texto="Día del mes en que se cierra el ciclo (1 a 28). Las compras hasta ese día, inclusive, entran en ese estado de cuenta." /></span>
        <input v-model.number="c.dia_corte" type="number" min="1" max="28" />
      </label>
      <label class="campo">
        <span>Día de pago <Ayuda texto="Día del mes en que vence el estado de cuenta (1 a 28). Es la primera fecha con ese día posterior al corte." /></span>
        <input v-model.number="c.dia_pago" type="number" min="1" max="28" />
      </label>
    </div>
    <CampoTasa v-model="c.tasa_compensatoria" titulo="Tasa compensatoria" />
    <CampoTasa v-model="c.tasa_moratoria" titulo="Tasa moratoria" />
    <label class="check">
      <input v-model="c.bloquear_con_vencido" type="checkbox" />
      Bloquear ventas si tiene un estado de cuenta vencido
      <Ayuda texto="Si está activo, no se registran ventas nuevas mientras el cliente tenga un estado de cuenta vencido sin pagar." />
    </label>
  </section>
</template>
