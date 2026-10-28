<script setup>
// Datos de la tienda y valores por defecto para registrar clientes nuevos.
import { onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import CampoTasa from '../../components/CampoTasa.vue'
import { vista } from '../../vista'

const datos = ref(null)
const error = ref('')
const aviso = ref('')

function tasaEntrada(t) {
  return { tipo: t.tipo, periodo: t.periodo, valor: String(t.valor), capitalizacion: t.capitalizacion }
}

onMounted(async () => {
  try {
    const t = await vendedor.tienda()
    datos.value = {
      ...t,
      documento: t.documento || '', telefono: t.telefono || '', direccion: t.direccion || '',
      configuracion: {
        ...t.configuracion,
        tasa_compensatoria: tasaEntrada(t.configuracion.tasa_compensatoria),
        tasa_moratoria: tasaEntrada(t.configuracion.tasa_moratoria),
      },
    }
  } catch (e) { error.value = e.message }
})

async function guardar() {
  error.value = ''
  aviso.value = ''
  try {
    await vendedor.guardarTienda(datos.value)
    aviso.value = 'Configuración guardada. Los valores por defecto se aplican a los clientes nuevos.'
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="pagina">
    <h1>Configuración</h1>
    <p v-if="error" class="aviso">{{ error }}</p>
    <p v-if="aviso" class="aviso info">{{ aviso }}</p>
    <form v-if="datos" class="formulario" @submit.prevent="guardar">
      <section class="panel">
        <h2>Datos de la tienda</h2>
        <div class="grilla">
          <label class="campo"><span>Nombre</span><input v-model="datos.nombre" required /></label>
          <label class="campo"><span>Giro <Ayuda texto="Bodega, frutería, carnicería, peluquería, spa, etc." /></span><input v-model="datos.giro" required /></label>
          <label class="campo"><span>DNI o RUC</span><input v-model="datos.documento" inputmode="numeric" /></label>
          <label class="campo"><span>Teléfono</span><input v-model="datos.telefono" /></label>
          <label class="campo ancho"><span>Dirección</span><input v-model="datos.direccion" /></label>
        </div>
      </section>
      <section class="panel">
        <h2>Valores por defecto para clientes nuevos</h2>
        <p class="suave chico">Se precargan al registrar un cliente y se pueden cambiar según el riesgo de cada uno. Cambiarlos no afecta a los clientes ya registrados.</p>
        <div class="grilla">
          <label class="campo"><span>Moneda</span><select v-model="datos.configuracion.moneda"><option value="PEN">Soles (PEN)</option><option value="USD">Dólares (USD)</option></select></label>
          <label class="campo"><span>Límite de crédito</span><input v-model="datos.configuracion.limite_credito" inputmode="decimal" /></label>
          <label class="campo"><span>Máximo de cuotas</span><input v-model.number="datos.configuracion.max_meses" type="number" min="1" max="36" /></label>
          <label class="campo"><span>Día de corte</span><input v-model.number="datos.configuracion.dia_corte" type="number" min="1" max="28" /></label>
          <label class="campo"><span>Día de pago</span><input v-model.number="datos.configuracion.dia_pago" type="number" min="1" max="28" /></label>
        </div>
        <CampoTasa v-model="datos.configuracion.tasa_compensatoria" :titulo="vista.simple ? 'Interés por el crédito (por defecto)' : 'Tasa compensatoria por defecto'" />
        <CampoTasa v-model="datos.configuracion.tasa_moratoria" :titulo="vista.simple ? 'Recargo por atraso (por defecto)' : 'Tasa moratoria por defecto'" />
        <label class="check">
          <input v-model="datos.configuracion.bloquear_con_vencido" type="checkbox" />
          No vender a clientes con estados de cuenta vencidos
          <Ayuda texto="Si está activo, el sistema rechaza ventas nuevas a un cliente mientras tenga un estado de cuenta vencido." />
        </label>
      </section>
      <div class="fila"><button class="primario">Guardar</button></div>
    </form>
  </div>
</template>

<style scoped>
.pagina, .formulario { display: flex; flex-direction: column; gap: 14px; max-width: 900px; }
h1 { font-size: 22px; }
.ancho { grid-column: span 2; }
</style>
