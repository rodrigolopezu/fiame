<script setup>
// Formulario para agregar un evento: venta, pago, cambio de condiciones o anulación.
import { computed, ref } from 'vue'
import Ayuda from './Ayuda.vue'
import CampoTasa from './CampoTasa.vue'

const props = defineProps({
  moneda: { type: String, required: true },
  maxCuotas: { type: Number, required: true },
  ventas: { type: Array, default: () => [] },
  fechaSugerida: { type: String, required: true },
})
const emit = defineEmits(['agregar'])

const tipo = ref('VENTA')
const fecha = ref(props.fechaSugerida)

const nuevoItem = () => ({ descripcion: '', cantidad: '1', precio_lista: '', moneda: props.moneda,
  permite_pago_unico: true, permite_cuotas: true })
const venta = ref({ modalidad: 'FIN_DE_MES', numero_cuotas: 3, tipo_cambio: '', items: [nuevoItem()] })
const pago = ref({ cantidad_estados: 1, medio: 'EFECTIVO' })
const cambio = ref({
  cambiarComp: true, cambiarMora: false, cambiarLimite: false,
  tasa_compensatoria: { tipo: 'EFECTIVA', periodo: 'ANUAL', valor: '30', capitalizacion: null },
  tasa_moratoria: { tipo: 'EFECTIVA', periodo: 'ANUAL', valor: '40', capitalizacion: null },
  limite_credito: '600.00',
})
const anulacion = ref({ venta: null })

const requiereTipoCambio = computed(() => venta.value.items.some((i) => i.moneda !== props.moneda))

function construir() {
  const base = { tipo: tipo.value, fecha: fecha.value }
  if (tipo.value === 'VENTA') {
    const v = venta.value
    return {
      ...base,
      modalidad: v.modalidad,
      numero_cuotas: v.modalidad === 'CUOTAS' ? Number(v.numero_cuotas) : null,
      tipo_cambio: requiereTipoCambio.value && v.tipo_cambio ? v.tipo_cambio : null,
      items: v.items.map((i) => ({ ...i })),
    }
  }
  if (tipo.value === 'PAGO') return { ...base, cantidad_estados: Number(pago.value.cantidad_estados), medio: pago.value.medio }
  if (tipo.value === 'CAMBIO_CONDICIONES') {
    const c = cambio.value
    return {
      ...base,
      tasa_compensatoria: c.cambiarComp ? { ...c.tasa_compensatoria } : null,
      tasa_moratoria: c.cambiarMora ? { ...c.tasa_moratoria } : null,
      limite_credito: c.cambiarLimite ? c.limite_credito : null,
    }
  }
  return { ...base, venta: Number(anulacion.value.venta) }
}

function agregar() {
  emit('agregar', construir())
  if (tipo.value === 'VENTA') venta.value.items = [nuevoItem()]
}
</script>

<template>
  <section class="panel">
    <h2>Agregar evento</h2>
    <div class="pestanas">
      <button v-for="[valor, nombre] in [['VENTA', 'Venta'], ['PAGO', 'Pago'], ['CAMBIO_CONDICIONES', 'Cambiar condiciones'], ['ANULAR_VENTA', 'Anular venta']]"
              :key="valor" :class="{ activa: tipo === valor }" @click="tipo = valor">{{ nombre }}</button>
    </div>

    <label class="campo fecha">
      <span>Fecha <Ayuda texto="Día en que ocurre el evento. Los cortes se generan solos al cierre de cada día de corte." /></span>
      <input v-model="fecha" type="date" />
    </label>

    <template v-if="tipo === 'VENTA'">
      <div class="items">
        <div class="entre">
          <h3>Productos</h3>
          <button class="enlace" @click="venta.items.push(nuevoItem())">+ Agregar producto</button>
        </div>
        <div v-for="(item, i) in venta.items" :key="i" class="item">
          <label class="campo desc">
            <span>Descripción</span>
            <input v-model="item.descripcion" placeholder="Arroz 5 kg" />
          </label>
          <label class="campo">
            <span>Cantidad</span>
            <input v-model="item.cantidad" inputmode="decimal" />
          </label>
          <label class="campo">
            <span>Precio lista <Ayuda texto="Precio a crédito del producto, en su moneda. Es el que se cobra en la venta." /></span>
            <input v-model="item.precio_lista" inputmode="decimal" placeholder="22.00" />
          </label>
          <label class="campo">
            <span>Moneda</span>
            <select v-model="item.moneda"><option>PEN</option><option>USD</option></select>
          </label>
          <div class="permisos">
            <label class="check chico"><input v-model="item.permite_pago_unico" type="checkbox" /> Pago único</label>
            <label class="check chico"><input v-model="item.permite_cuotas" type="checkbox" /> Cuotas</label>
          </div>
          <button class="icono" title="Quitar producto" :disabled="venta.items.length === 1" @click="venta.items.splice(i, 1)">×</button>
        </div>
      </div>
      <div class="grilla">
        <label class="campo">
          <span>Modalidad <Ayuda texto="Fin de mes: un solo pago en la fecha de pago del ciclo. Cuotas: método francés con gracia hasta la fecha de pago." /></span>
          <select v-model="venta.modalidad">
            <option value="FIN_DE_MES">Pago único a fin de mes</option>
            <option value="CUOTAS">En cuotas</option>
          </select>
        </label>
        <label v-if="venta.modalidad === 'CUOTAS'" class="campo">
          <span>N.° de cuotas <Ayuda :texto="`Entre 1 y ${maxCuotas}, el máximo del cliente.`" /></span>
          <input v-model.number="venta.numero_cuotas" type="number" min="1" :max="maxCuotas" />
        </label>
        <label v-if="requiereTipoCambio" class="campo">
          <span>Tipo de cambio <Ayuda texto="Soles por dólar, con 3 decimales. Ej.: 3.520." /></span>
          <input v-model="venta.tipo_cambio" inputmode="decimal" placeholder="3.520" />
        </label>
      </div>
    </template>

    <div v-else-if="tipo === 'PAGO'" class="grilla">
      <label class="campo">
        <span>Estados de cuenta a pagar <Ayuda texto="Se pagan completos y en orden, del más antiguo al más reciente. No hay pagos parciales." /></span>
        <input v-model.number="pago.cantidad_estados" type="number" min="1" />
      </label>
      <label class="campo">
        <span>Medio de pago <Ayuda texto="Solo informativo: el pago ocurre fuera del sistema." /></span>
        <select v-model="pago.medio">
          <option v-for="m in ['EFECTIVO', 'YAPE', 'PLIN', 'TRANSFERENCIA', 'OTRO']" :key="m" :value="m">{{ m[0] + m.slice(1).toLowerCase() }}</option>
        </select>
      </label>
    </div>

    <template v-else-if="tipo === 'CAMBIO_CONDICIONES'">
      <p class="suave chico">Las nuevas condiciones aplican solo a las ventas y cortes posteriores; las ventas anteriores conservan sus tasas.</p>
      <label class="check"><input v-model="cambio.cambiarComp" type="checkbox" /> Cambiar tasa compensatoria</label>
      <CampoTasa v-if="cambio.cambiarComp" v-model="cambio.tasa_compensatoria" titulo="Nueva tasa compensatoria" />
      <label class="check"><input v-model="cambio.cambiarMora" type="checkbox" /> Cambiar tasa moratoria</label>
      <CampoTasa v-if="cambio.cambiarMora" v-model="cambio.tasa_moratoria" titulo="Nueva tasa moratoria" />
      <label class="check"><input v-model="cambio.cambiarLimite" type="checkbox" /> Cambiar límite de crédito</label>
      <label v-if="cambio.cambiarLimite" class="campo limite">
        <span>Nuevo límite</span>
        <input v-model="cambio.limite_credito" inputmode="decimal" />
      </label>
    </template>

    <div v-else class="grilla">
      <label class="campo">
        <span>Venta a anular <Ayuda texto="Solo se puede anular una venta que todavía no fue incluida en un estado de cuenta." /></span>
        <select v-model="anulacion.venta">
          <option :value="null" disabled>Elegir…</option>
          <option v-for="v in ventas" :key="v.numero" :value="v.numero">
            Venta {{ v.numero }} · {{ v.fecha }} · {{ v.items.map((i) => i.descripcion).join(', ') }}
          </option>
        </select>
      </label>
    </div>

    <div class="fila">
      <button class="primario" @click="agregar">Agregar {{ tipo === 'VENTA' ? 'venta' : tipo === 'PAGO' ? 'pago' : tipo === 'CAMBIO_CONDICIONES' ? 'cambio' : 'anulación' }}</button>
    </div>
  </section>
</template>

<style scoped>
.fecha { max-width: 180px; }
.limite { max-width: 180px; }
.items { display: flex; flex-direction: column; gap: 8px; }
.item {
  display: grid;
  grid-template-columns: 0.8fr 1fr 0.9fr auto auto;
  gap: 8px;
  align-items: end;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--borde);
}
.item .desc { grid-column: 1 / -1; }
.permisos { display: flex; flex-direction: column; gap: 2px; padding-bottom: 2px; }
@media (max-width: 420px) {
  .item { grid-template-columns: 1fr 1fr; }
}
</style>
