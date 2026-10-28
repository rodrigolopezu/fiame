<script setup>
// Marco de la interfaz del vendedor: barra superior con la fecha del sistema y la sesión.
// El menú principal es el círculo de /vendedor; desde cualquier sección se vuelve a él.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { vendedor } from '../../api'
import Ayuda from '../../components/Ayuda.vue'
import InterruptorVista from '../../components/InterruptorVista.vue'
import Logo from '../../components/Logo.vue'
import { fecha } from '../../formato'
import { cerrar, sesion } from '../../sesion'

const router = useRouter()
const ruta = useRoute()
const info = ref(null)
const cambiando = ref(false)
const nuevaFecha = ref('')
const error = ref('')

const SECCIONES = [
  ['/vendedor/ventas/nueva', 'Nueva venta'], ['/vendedor/pagos/nuevo', 'Registrar pago'],
  ['/vendedor/clientes', 'Clientes'], ['/vendedor/estados-cuenta', 'Estados de cuenta'],
  ['/vendedor/ventas', 'Ventas'], ['/vendedor/pagos', 'Pagos'], ['/vendedor/panel', 'Panel'],
  ['/vendedor/catalogo', 'Catálogo'], ['/vendedor/configuracion', 'Configuración'],
  ['/vendedor/actividad', 'Actividad'],
]

const enMenu = computed(() => ruta.path === '/vendedor' || ruta.path === '/vendedor/')
const seccion = computed(() => {
  // La sección más específica que coincide con la ruta actual.
  const coincidencias = SECCIONES.filter(([r]) => ruta.path === r || ruta.path.startsWith(`${r}/`))
  return coincidencias.sort((a, b) => b[0].length - a[0].length)[0]?.[1]
})

function volverAlMenu() {
  router.push('/vendedor')
}

// Esc vuelve al menú principal (salvo mientras se escribe en un campo).
function teclado(evento) {
  const escribiendo = ['INPUT', 'TEXTAREA', 'SELECT'].includes(evento.target.tagName)
  if (evento.key === 'Escape' && !escribiendo && !enMenu.value) volverAlMenu()
}

onMounted(async () => {
  window.addEventListener('keydown', teclado)
  try { info.value = await vendedor.sesion() } catch { /* redirige al login */ }
})
onBeforeUnmount(() => window.removeEventListener('keydown', teclado))

async function adelantar() {
  error.value = ''
  try {
    await vendedor.avanzarFecha(nuevaFecha.value)
    location.reload()
  } catch (e) {
    error.value = e.message
  }
}

function salir() {
  cerrar()
  router.push('/login')
}
</script>

<template>
  <div class="vendedor">
    <header class="barra">
      <div class="izquierda">
        <RouterLink to="/vendedor" class="marca" title="Menú principal"><Logo :tamano="30" /></RouterLink>
        <template v-if="!enMenu">
          <button class="volver" title="Volver al menú principal (Esc)" @click="volverAlMenu">
            <span class="anillo" aria-hidden="true" /> Menú
          </button>
          <span v-if="seccion" class="migas"><span class="suave">/</span> {{ seccion }}</span>
        </template>
        <span v-else class="suave chico">{{ sesion.tienda }}</span>
      </div>
      <div v-if="info" class="fecha">
        <span>Hoy: <strong>{{ fecha(info.hoy) }}</strong></span>
        <span v-if="info.fecha_simulada" class="etiqueta alerta">fecha simulada</span>
        <button class="enlace chico" @click="cambiando = !cambiando; nuevaFecha = info.hoy">Adelantar fecha</button>
        <Ayuda texto="Solo para pruebas: adelanta la fecha del sistema para ver cortes, vencimientos y mora sin esperar. La fecha nunca retrocede." />
      </div>
      <div class="fila">
        <InterruptorVista />
        <span class="suave chico">{{ sesion.usuario }}</span>
        <button class="chico" @click="salir">Cerrar sesión</button>
      </div>
    </header>

    <div v-if="cambiando" class="adelantar">
      <input v-model="nuevaFecha" type="date" :min="info.hoy" />
      <button class="primario" @click="adelantar">Aplicar</button>
      <button @click="cambiando = false">Cancelar</button>
      <span v-if="error" class="error chico">{{ error }}</span>
    </div>

    <main class="contenido" :class="{ 'en-menu': enMenu }">
      <RouterView />
    </main>

    <footer v-if="enMenu" class="pie chico">
      <RouterLink to="/simulador">Simulador y calculadoras</RouterLink>
      <RouterLink to="/portal">Portal del cliente</RouterLink>
    </footer>
  </div>
</template>

<style scoped>
.vendedor { min-height: 100vh; display: flex; flex-direction: column; }
.barra {
  display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 10px 20px; background: rgb(255 255 255 / 0.9); backdrop-filter: blur(8px); border-bottom: 1px solid var(--borde);
  position: sticky; top: 0; z-index: 20;
}
.izquierda { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.marca { display: inline-flex; text-decoration: none; }
.volver { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 5px 14px 5px 7px; background: var(--marca-suave); border-color: transparent; color: var(--marca-fuerte); }
.volver:hover { border-color: var(--marca); }
.anillo { width: 16px; height: 16px; border-radius: 50%; border: 4px solid var(--marca); box-sizing: border-box; }
.migas { font-weight: 600; }
.fecha { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.adelantar { display: flex; gap: 8px; align-items: center; padding: 10px 20px; background: var(--alerta-suave); flex-wrap: wrap; }
.adelantar input { width: auto; }
.error { color: var(--error); }
.contenido { padding: 20px; max-width: 1400px; width: 100%; margin: 0 auto; flex: 1; }
.contenido.en-menu { display: flex; justify-content: center; }
.pie { display: flex; gap: 16px; justify-content: center; padding: 0 0 20px; }
.pie a { color: var(--suave); }
@media (max-width: 700px) {
  .barra { padding: 8px 12px; }
  .contenido { padding: 14px 12px; }
}
</style>
