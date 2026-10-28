<script setup>
// Menú principal del vendedor: resumen del día al centro y un anillo exterior
// segmentado con cada sección del sistema.
import { computed, markRaw, onMounted, ref } from 'vue'
import {
  FileText, HandCoins, History, LayoutDashboard, Package, Receipt, Settings, ShoppingCart, Users, Wallet,
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { vendedor } from '../../api'
import Logo from '../../components/Logo.vue'
import { dinero, fecha } from '../../formato'
import { sesion } from '../../sesion'
import { vista } from '../../vista'

const router = useRouter()
const panel = ref(null)
const error = ref('')
const activo = ref(null)

onMounted(async () => {
  try { panel.value = await vendedor.panel() } catch (e) { error.value = e.message }
})

// Agrupadas por tipo: operaciones del día, consultas y gestión.
const SECCIONES = [
  { ruta: '/vendedor/ventas/nueva', nombre: ['Nueva', 'venta'], icono: markRaw(ShoppingCart), grupo: 'operacion', ayuda: 'Registrar una venta al crédito' },
  { ruta: '/vendedor/pagos/nuevo', nombre: ['Registrar', 'pago'], icono: markRaw(HandCoins), grupo: 'operacion', ayuda: 'Cobrar estados de cuenta', indicador: 'vencidos' },
  { ruta: '/vendedor/clientes', nombre: ['Clientes'], icono: markRaw(Users), grupo: 'consulta', ayuda: 'Condiciones, línea de crédito y score', indicador: 'clientes' },
  { ruta: '/vendedor/estados-cuenta', nombre: ['Estados', 'de cuenta'], icono: markRaw(FileText), grupo: 'consulta', ayuda: 'Generados en cada corte', indicador: 'porCobrar' },
  { ruta: '/vendedor/ventas', nombre: ['Ventas'], icono: markRaw(Receipt), grupo: 'consulta', ayuda: 'Historial de ventas y cronogramas' },
  { ruta: '/vendedor/pagos', nombre: ['Pagos'], icono: markRaw(Wallet), grupo: 'consulta', ayuda: 'Constancias y anulaciones' },
  { ruta: '/vendedor/panel', nombre: ['Panel'], icono: markRaw(LayoutDashboard), grupo: 'gestion', ayuda: 'Vencidos, próximos cobros y riesgo' },
  { ruta: '/vendedor/catalogo', nombre: ['Catálogo'], icono: markRaw(Package), grupo: 'gestion', ayuda: 'Productos, precios y modalidades' },
  { ruta: '/vendedor/configuracion', nombre: ['Configu-', 'ración'], icono: markRaw(Settings), grupo: 'gestion', ayuda: 'Datos de la tienda y valores por defecto' },
  { ruta: '/vendedor/actividad', nombre: ['Actividad'], icono: markRaw(History), grupo: 'gestion', ayuda: 'Bitácora de operaciones' },
]

const C = 300 // centro del SVG
const R_EXT = 292
const R_INT = 178
const R_TEXTO = (R_EXT + R_INT) / 2

function punto(radio, grados) {
  const rad = (grados * Math.PI) / 180
  return [C + radio * Math.cos(rad), C + radio * Math.sin(rad)]
}

const segmentos = computed(() => {
  const paso = 360 / SECCIONES.length
  return SECCIONES.map((s, i) => {
    const desde = -90 - paso / 2 + i * paso
    const hasta = desde + paso
    const [x1, y1] = punto(R_EXT, desde)
    const [x2, y2] = punto(R_EXT, hasta)
    const [x3, y3] = punto(R_INT, hasta)
    const [x4, y4] = punto(R_INT, desde)
    const [tx, ty] = punto(R_TEXTO, desde + paso / 2)
    return {
      ...s,
      d: `M ${x1} ${y1} A ${R_EXT} ${R_EXT} 0 0 1 ${x2} ${y2} L ${x3} ${y3} A ${R_INT} ${R_INT} 0 0 0 ${x4} ${y4} Z`,
      tx, ty, retraso: `${i * 35}ms`,
    }
  })
})

const indicadores = computed(() => {
  if (!panel.value) return {}
  return {
    vencidos: panel.value.vencidos.length ? { valor: panel.value.vencidos.length, alerta: true } : null,
    clientes: { valor: panel.value.clientes_activos },
    porCobrar: panel.value.proximos.length + panel.value.vencidos.length
      ? { valor: panel.value.proximos.length + panel.value.vencidos.length, alerta: !!panel.value.vencidos.length }
      : null,
  }
})

const seccionActiva = computed(() => SECCIONES.find((s) => s.ruta === activo.value))

function ir(ruta) {
  router.push(ruta)
}
</script>

<template>
  <div class="menu">
    <p v-if="error" class="aviso">{{ error }}</p>

    <div class="rueda">
      <svg viewBox="0 0 600 600" role="navigation" aria-label="Menú principal">
        <defs>
          <linearGradient id="menu-operacion" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#7457ff" />
            <stop offset="1" stop-color="#4527d9" />
          </linearGradient>
        </defs>
        <g v-for="s in segmentos" :key="s.ruta" class="segmento" :class="s.grupo" :style="{ animationDelay: s.retraso }"
           role="link" tabindex="0" :aria-label="`${s.nombre.join(' ')}: ${s.ayuda}`"
           @click="ir(s.ruta)" @keydown.enter="ir(s.ruta)" @keydown.space.prevent="ir(s.ruta)"
           @mouseenter="activo = s.ruta" @mouseleave="activo = null" @focus="activo = s.ruta" @blur="activo = null">
          <path :d="s.d" />
          <component :is="s.icono" :x="s.tx - 13" :y="s.ty - 40" :size="26" :stroke-width="1.8" class="icono" aria-hidden="true" />
          <text :x="s.tx" :y="s.ty + (s.nombre.length > 1 ? 10 : 18)" class="nombre">
            <tspan v-for="(linea, n) in s.nombre" :key="n" :x="s.tx" :dy="n ? 16 : 0">{{ linea }}</tspan>
          </text>
          <g v-if="s.indicador && indicadores[s.indicador]" class="indicador" :class="{ alerta: indicadores[s.indicador].alerta }">
            <circle :cx="s.tx + 30" :cy="s.ty - 30" r="12" />
            <text :x="s.tx + 30" :y="s.ty - 26">{{ indicadores[s.indicador].valor }}</text>
          </g>
        </g>
      </svg>

      <div class="centro">
        <template v-if="seccionActiva">
          <span class="icono-centro"><component :is="seccionActiva.icono" :size="22" :stroke-width="1.9" aria-hidden="true" /></span>
          <strong class="titulo">{{ seccionActiva.nombre.join(' ').replace('- ', '') }}</strong>
          <span class="suave">{{ seccionActiva.ayuda }}</span>
        </template>
        <template v-else-if="panel">
          <Logo :tamano="26" :texto="false" />
          <span class="suave chico">{{ sesion.tienda }} · {{ fecha(panel.hoy) }}</span>
          <span class="rotulo">{{ vista.simple ? 'Te deben en total' : 'Crédito colocado' }}</span>
          <strong class="cifra">{{ dinero(panel.credito_colocado) }}</strong>
          <div class="dos">
            <div>
              <span class="rotulo">Por cobrar</span>
              <strong>{{ dinero(panel.por_cobrar) }}</strong>
            </div>
            <div :class="{ rojo: panel.vencidos.length }">
              <span class="rotulo">{{ vista.simple ? 'Atrasado' : 'Vencido hoy' }}</span>
              <strong>{{ dinero(panel.vencido_al_dia) }}</strong>
            </div>
          </div>
          <span class="suave chico">
            {{ panel.clientes_activos }} clientes · {{ panel.ventas_mes.cantidad }} ventas este mes
          </span>
        </template>
        <span v-else class="suave">Cargando…</span>
      </div>
    </div>

    <div class="leyenda chico suave">
      <span><i class="operacion" /> Operaciones del día</span>
      <span><i class="consulta" /> Consultas</span>
      <span><i class="gestion" /> Gestión</span>
    </div>
  </div>
</template>

<style scoped>
.menu { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 8px 0 24px; }
.rueda { position: relative; width: min(640px, 94vw); aspect-ratio: 1; }
svg { width: 100%; height: 100%; overflow: visible; }

.segmento { cursor: pointer; outline: none; transform-origin: 300px 300px; animation: aparecer 0.45s ease-out backwards; }
.segmento path { stroke: var(--fondo); stroke-width: 5; transition: fill 0.15s, transform 0.15s; transform-origin: 300px 300px; }
.segmento.operacion path { fill: url(#menu-operacion); }
.segmento.consulta path { fill: var(--lavanda); }
.segmento.gestion path { fill: var(--panel); }
.segmento:hover path, .segmento:focus-visible path { transform: scale(1.03); }
.segmento.operacion:hover path, .segmento.operacion:focus-visible path { fill: var(--marca-fuerte); }
.segmento.consulta:hover path, .segmento.consulta:focus-visible path { fill: var(--lavanda-fuerte); }
.segmento.gestion:hover path, .segmento.gestion:focus-visible path { fill: var(--marca-suave); }
.segmento:focus-visible path { stroke: var(--marca); }

text { text-anchor: middle; pointer-events: none; font-family: inherit; }
.icono { color: var(--marca); pointer-events: none; }
.operacion .icono { color: #fff; }
.nombre { font-size: 14px; font-weight: 700; fill: var(--texto); letter-spacing: -0.01em; }
.operacion .nombre { fill: #fff; }
.indicador circle { fill: var(--marca-fuerte); stroke: #fff; stroke-width: 2; }
.indicador.alerta circle { fill: var(--error); }
.operacion .indicador circle { fill: #fff; }
.operacion .indicador text { fill: var(--marca-fuerte); }
.operacion .indicador.alerta circle { fill: var(--error); }
.operacion .indicador.alerta text { fill: #fff; }
.indicador text { font-size: 12px; font-weight: 700; fill: #fff; }

.centro {
  position: absolute; inset: 22%; border-radius: 50%;
  background: radial-gradient(circle at 50% 30%, #ffffff 0%, var(--panel-suave) 100%);
  border: 1px solid var(--borde); box-shadow: var(--sombra-alta);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
  text-align: center; padding: 8%;
}
.cifra { font-size: clamp(20px, 4.4vw, 32px); font-weight: 800; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; color: var(--texto); }
.rotulo { font-size: 12px; color: var(--suave); display: block; }
.dos { display: flex; gap: 18px; font-variant-numeric: tabular-nums; }
.dos strong { font-size: clamp(13px, 2.4vw, 16px); }
.rojo strong, .rojo .rotulo { color: var(--error); }
.icono-centro { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 14px; background: var(--marca-suave); color: var(--marca); }
.titulo { font-size: 20px; }

.leyenda { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }
.leyenda i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 4px; border: 1px solid var(--borde); vertical-align: -1px; }
.leyenda .operacion { background: var(--marca-degradado); }
.leyenda .consulta { background: var(--lavanda); }
.leyenda .gestion { background: var(--panel); }

@keyframes aparecer { from { opacity: 0; transform: scale(0.92) rotate(-6deg); } }
@media (prefers-reduced-motion: reduce) { .segmento { animation: none; } }
@media (max-width: 480px) {
  .nombre { font-size: 17px; }
  .dos { flex-direction: column; gap: 4px; }
}
</style>
