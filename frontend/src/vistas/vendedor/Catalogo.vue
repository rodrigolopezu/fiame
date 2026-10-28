<script setup>
// Catálogo de productos y servicios de la tienda (sin inventario: fuera de alcance).
import { computed, onMounted, ref } from 'vue'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import { dinero } from '../../formato'

const productos = ref([])
const editando = ref(null) // null | producto (nuevo sin id)
const error = ref('')
const verInactivos = ref(false)
const IMAGENES = ['arroz', 'aceite', 'azucar', 'leche', 'atun', 'fideos', 'detergente', 'papel', 'gaseosa', 'huevos', 'licuadora', 'parlante']

async function cargar() {
  try { productos.value = await vendedor.productos() } catch (e) { error.value = e.message }
}
onMounted(cargar)

const visibles = computed(() => productos.value.filter((p) => verInactivos.value || p.activo))

function nuevo() {
  editando.value = {
    nombre: '', descripcion: '', marca: '', proveedor: '', unidad_medida: 'unidad', imagen_url: '/productos/arroz.svg',
    moneda: 'PEN', precio_contado: '', precio_lista: '', permite_pago_unico: true, permite_cuotas: false, activo: true,
  }
}

async function guardar() {
  error.value = ''
  const { id, ...datos } = editando.value
  for (const campo of ['descripcion', 'marca', 'proveedor', 'imagen_url']) datos[campo] = datos[campo] || null
  try {
    if (id) await vendedor.editarProducto(id, datos)
    else await vendedor.crearProducto(datos)
    editando.value = null
    await cargar()
  } catch (e) { error.value = e.message }
}

async function alternar(p) {
  const { id, ...datos } = p
  try { await vendedor.editarProducto(id, { ...datos, activo: !p.activo }); await cargar() } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="pagina">
    <div class="entre">
      <h1>Catálogo</h1>
      <div class="fila">
        <label class="check"><input v-model="verInactivos" type="checkbox" /> Ver inactivos</label>
        <button class="primario" @click="nuevo">Nuevo producto</button>
      </div>
    </div>
    <p class="suave chico">La venta al crédito usa el <strong>precio de lista</strong>. El catálogo no maneja inventario ni stock.</p>
    <p v-if="error" class="aviso">{{ error }}</p>

    <section v-if="editando" class="panel">
      <h2>{{ editando.id ? 'Editar producto' : 'Nuevo producto' }}</h2>
      <div class="grilla">
        <label class="campo ancho"><span>Nombre</span><input v-model="editando.nombre" /></label>
        <label class="campo"><span>Marca</span><input v-model="editando.marca" /></label>
        <label class="campo"><span>Proveedor</span><input v-model="editando.proveedor" /></label>
        <label class="campo"><span>Unidad de medida <Ayuda texto="Ej.: unidad, bolsa, kg, litro, paquete, servicio." /></span><input v-model="editando.unidad_medida" /></label>
        <label class="campo"><span>Moneda</span><select v-model="editando.moneda"><option>PEN</option><option>USD</option></select></label>
        <label class="campo"><span>Precio al contado</span><input v-model="editando.precio_contado" inputmode="decimal" /></label>
        <label class="campo"><span>Precio de lista (crédito) <Ayuda texto="Precio que se cobra en la venta al crédito. No puede ser menor que el precio al contado." /></span><input v-model="editando.precio_lista" inputmode="decimal" /></label>
        <label class="campo ancho"><span>Descripción</span><input v-model="editando.descripcion" /></label>
        <label class="campo ancho">
          <span>Imagen <Ayuda texto="URL de la imagen o uno de los íconos incluidos." /></span>
          <div class="imagen">
            <img :src="editando.imagen_url || '/productos/arroz.svg'" alt="" />
            <input v-model="editando.imagen_url" placeholder="https://… o /productos/…" />
            <select @change="editando.imagen_url = `/productos/${$event.target.value}.svg`">
              <option value="" selected disabled>Ícono…</option>
              <option v-for="i in IMAGENES" :key="i" :value="i">{{ i }}</option>
            </select>
          </div>
        </label>
      </div>
      <div class="fila">
        <label class="check"><input v-model="editando.permite_pago_unico" type="checkbox" /> Permite pago único a fin de mes</label>
        <label class="check"><input v-model="editando.permite_cuotas" type="checkbox" /> Permite pago en cuotas</label>
        <label class="check"><input v-model="editando.activo" type="checkbox" /> Activo</label>
      </div>
      <div class="fila">
        <button class="primario" @click="guardar">Guardar</button>
        <button @click="editando = null">Cancelar</button>
      </div>
    </section>

    <div class="catalogo">
      <article v-for="p in visibles" :key="p.id" class="panel producto" :class="{ inactivo: !p.activo }">
        <img :src="p.imagen_url || '/productos/arroz.svg'" :alt="p.nombre" />
        <div>
          <h3>{{ p.nombre }}</h3>
          <p class="suave chico">{{ p.marca }} · {{ p.unidad_medida }}<span v-if="p.proveedor"> · {{ p.proveedor }}</span></p>
        </div>
        <div class="precios">
          <span>Crédito <strong>{{ dinero(p.precio_lista, p.moneda) }}</strong></span>
          <span class="suave chico">Contado {{ dinero(p.precio_contado, p.moneda) }}</span>
        </div>
        <div class="fila">
          <span v-if="p.permite_pago_unico" class="etiqueta neutra">fin de mes</span>
          <span v-if="p.permite_cuotas" class="etiqueta info">cuotas</span>
          <span v-if="!p.activo" class="etiqueta error">inactivo</span>
        </div>
        <div class="fila acciones">
          <button class="enlace chico" @click="editando = { ...p }">Editar</button>
          <button class="enlace chico" @click="alternar(p)">{{ p.activo ? 'Desactivar' : 'Activar' }}</button>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.pagina { display: flex; flex-direction: column; gap: 14px; }
h1 { font-size: 22px; }
.catalogo { display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); }
.producto { gap: 8px; }
.producto img { width: 100%; aspect-ratio: 1.4; object-fit: contain; background: var(--panel-suave); border-radius: 8px; }
.precios { display: flex; flex-direction: column; font-variant-numeric: tabular-nums; }
.inactivo { opacity: 0.55; }
.acciones { margin-top: auto; }
.ancho { grid-column: span 2; }
.imagen { display: flex; gap: 8px; align-items: center; }
.imagen img { width: 40px; height: 40px; border-radius: 6px; flex: none; }
.imagen select { max-width: 120px; }
</style>
