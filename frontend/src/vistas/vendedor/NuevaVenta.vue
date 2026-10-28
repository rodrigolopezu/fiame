<script setup>
// Registrar una venta al crédito: elegir cliente y productos, ver el cálculo y confirmar.
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import Semaforo from '../../components/Semaforo.vue'
import VentaDetalle from '../../components/VentaDetalle.vue'
import { dinero } from '../../formato'

const ruta = useRoute()
const router = useRouter()
const clientes = ref([])
const productos = ref([])
const clienteId = ref(ruta.query.cliente ? Number(ruta.query.cliente) : null)
const carrito = ref([]) // { producto, cantidad }
const modalidad = ref('FIN_DE_MES')
const numeroCuotas = ref(3)
const tipoCambio = ref('')
const referenciaTC = ref(null)
const buscar = ref('')
const previa = ref(null)
const errorPrevia = ref('')
const error = ref('')
const guardando = ref(false)

onMounted(async () => {
  try {
    const [cl, pr, tc] = await Promise.all([vendedor.clientes(), vendedor.productos(), vendedor.tipoCambio()])
    clientes.value = cl.filter((c) => c.estado === 'ACTIVO')
    productos.value = pr.filter((p) => p.activo)
    referenciaTC.value = tc
    if (tc) tipoCambio.value = tc.venta
  } catch (e) { error.value = e.message }
})

const cliente = computed(() => clientes.value.find((c) => c.id === clienteId.value))
const visibles = computed(() => {
  const q = buscar.value.trim().toLowerCase()
  return productos.value.filter((p) => !q || `${p.nombre} ${p.marca || ''}`.toLowerCase().includes(q))
})
const permiteUnico = computed(() => carrito.value.every((l) => l.producto.permite_pago_unico))
const permiteCuotas = computed(() => carrito.value.length && carrito.value.every((l) => l.producto.permite_cuotas))
const otraMoneda = computed(() => cliente.value && carrito.value.some((l) => l.producto.moneda !== cliente.value.moneda))

watch(permiteCuotas, (si) => { if (!si && modalidad.value === 'CUOTAS') modalidad.value = 'FIN_DE_MES' })
watch(permiteUnico, (si) => { if (!si && permiteCuotas.value) modalidad.value = 'CUOTAS' })

function agregar(p) {
  const linea = carrito.value.find((l) => l.producto.id === p.id)
  if (linea) linea.cantidad = String(Number(linea.cantidad) + 1)
  else carrito.value.push({ producto: p, cantidad: '1' })
}

function pedido() {
  return {
    cliente_id: clienteId.value,
    items: carrito.value.map((l) => ({ producto_id: l.producto.id, cantidad: l.cantidad })),
    modalidad: modalidad.value,
    numero_cuotas: modalidad.value === 'CUOTAS' ? Number(numeroCuotas.value) : null,
    tipo_cambio: otraMoneda.value && tipoCambio.value ? tipoCambio.value : null,
  }
}

// Vista previa calculada por el backend cada vez que cambia algo.
let temporizador
watch([clienteId, carrito, modalidad, numeroCuotas, tipoCambio], () => {
  clearTimeout(temporizador)
  previa.value = null
  errorPrevia.value = ''
  if (!clienteId.value || !carrito.value.length) return
  temporizador = setTimeout(async () => {
    try { previa.value = await vendedor.previsualizarVenta(pedido()) } catch (e) { errorPrevia.value = e.message }
  }, 250)
}, { deep: true })

async function confirmar() {
  guardando.value = true
  error.value = ''
  try {
    const venta = await vendedor.registrarVenta(pedido())
    router.push({ path: `/vendedor/clientes/${venta.cliente_id}`, query: { venta: venta.numero } })
  } catch (e) {
    error.value = e.message
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <h1>Nueva venta al crédito</h1>
    <p v-if="error" class="aviso">{{ error }}</p>

    <div class="columnas">
      <div class="izquierda">
        <section class="panel">
          <label class="campo">
            <span>Cliente <Ayuda texto="Solo clientes activos. Las condiciones (tasa, corte y pago) son las del cliente." /></span>
            <select v-model="clienteId">
              <option :value="null" disabled>Elegir cliente…</option>
              <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nombre }} · {{ c.numero_documento }}</option>
            </select>
          </label>
          <div v-if="cliente" class="resumen-cliente">
            <span>Disponible: <strong>{{ dinero(cliente.linea.disponible, cliente.moneda) }}</strong></span>
            <Semaforo :score="cliente.score" detalle />
            <span v-if="cliente.estados_vencidos" class="etiqueta error">{{ cliente.estados_vencidos }} estado(s) vencido(s)</span>
          </div>
        </section>

        <section class="panel">
          <div class="entre">
            <h2>Catálogo</h2>
            <input v-model="buscar" class="buscar" placeholder="Buscar producto" />
          </div>
          <div class="catalogo">
            <button v-for="p in visibles" :key="p.id" class="producto" type="button" @click="agregar(p)">
              <img :src="p.imagen_url || '/productos/arroz.svg'" :alt="p.nombre" />
              <span class="nombre">{{ p.nombre }}</span>
              <span class="suave chico">{{ p.marca }} · {{ p.unidad_medida }}</span>
              <span class="precio">{{ dinero(p.precio_lista, p.moneda) }}</span>
              <span class="chico suave">contado {{ dinero(p.precio_contado, p.moneda) }}</span>
              <span class="modos">
                <span v-if="p.permite_pago_unico" class="etiqueta neutra">fin de mes</span>
                <span v-if="p.permite_cuotas" class="etiqueta info">cuotas</span>
              </span>
            </button>
          </div>
        </section>
      </div>

      <div class="derecha">
        <section class="panel">
          <h2>Pedido</h2>
          <p v-if="!carrito.length" class="suave">Elige productos del catálogo.</p>
          <table v-else>
            <thead><tr><th>Producto</th><th>Cant.</th><th class="num">Precio lista</th><th></th></tr></thead>
            <tbody>
              <tr v-for="(l, i) in carrito" :key="l.producto.id">
                <td>{{ l.producto.nombre }}</td>
                <td class="cantidad"><input v-model="l.cantidad" inputmode="decimal" /></td>
                <td class="num">{{ dinero(l.producto.precio_lista, l.producto.moneda) }}</td>
                <td><button class="icono" title="Quitar" @click="carrito.splice(i, 1)">×</button></td>
              </tr>
            </tbody>
          </table>

          <div class="grilla">
            <label class="campo">
              <span>Modalidad <Ayuda texto="Fin de mes: un solo pago en la fecha de pago del ciclo. Cuotas: método francés, con gracia hasta la fecha de pago." /></span>
              <select v-model="modalidad">
                <option value="FIN_DE_MES" :disabled="!permiteUnico">Pago único a fin de mes</option>
                <option value="CUOTAS" :disabled="!permiteCuotas">En cuotas</option>
              </select>
            </label>
            <label v-if="modalidad === 'CUOTAS'" class="campo">
              <span>N.° de cuotas <Ayuda :texto="`Máximo del cliente: ${cliente?.max_meses ?? '—'}`" /></span>
              <input v-model.number="numeroCuotas" type="number" min="1" />
            </label>
            <label v-if="otraMoneda" class="campo">
              <span>Tipo de cambio <Ayuda :texto="`Soles por dólar. Referencia: ${referenciaTC ? `${referenciaTC.venta} (${referenciaTC.fuente})` : 'sin conexión'}.`" /></span>
              <input v-model="tipoCambio" inputmode="decimal" placeholder="3.520" />
            </label>
          </div>
          <p v-if="carrito.length && !permiteCuotas && !permiteUnico" class="aviso">Los productos elegidos no comparten ninguna forma de pago.</p>
        </section>

        <p v-if="errorPrevia" class="aviso">{{ errorPrevia }}</p>
        <template v-if="previa">
          <VentaDetalle :venta="{ ...previa, cliente: null, estado: 'VIGENTE' }" />
          <button class="primario grande" :disabled="guardando" @click="confirmar">
            {{ guardando ? 'Registrando…' : `Confirmar venta · ${dinero(previa.modalidad === 'CUOTAS' ? previa.cuotas[0].cuota : previa.total, previa.moneda)}${previa.modalidad === 'CUOTAS' ? ` × ${previa.numero_cuotas} cuotas` : ''}` }}
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
.columnas { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.izquierda, .derecha { display: flex; flex-direction: column; gap: 14px; }
.resumen-cliente { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.buscar { max-width: 220px; }
.catalogo { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); }
.producto { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; text-align: left; padding: 10px; }
.producto img { width: 56px; height: 56px; border-radius: 8px; margin-bottom: 4px; }
.nombre { font-weight: 600; }
.precio { font-weight: 650; font-variant-numeric: tabular-nums; margin-top: 4px; }
.modos { display: flex; gap: 4px; margin-top: 4px; flex-wrap: wrap; }
.cantidad input { width: 70px; }
.grande { padding: 12px; font-size: 15px; }
@media (max-width: 1000px) { .columnas { grid-template-columns: 1fr; } }
</style>
