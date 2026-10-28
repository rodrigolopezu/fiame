import { createRouter, createWebHistory } from 'vue-router'
import { sesion } from './sesion'

const rutas = [
  { path: '/', component: () => import('./vistas/Inicio.vue') },
  { path: '/login', component: () => import('./vistas/Login.vue') },
  { path: '/portal', component: () => import('./vistas/portal/Portal.vue') },
  { path: '/simulador', component: () => import('./vistas/simulador/SimuladorVista.vue') },
  {
    path: '/vendedor',
    component: () => import('./vistas/vendedor/Layout.vue'),
    meta: { requiereSesion: true },
    children: [
      { path: '', component: () => import('./vistas/vendedor/MenuCircular.vue') },
      { path: 'panel', component: () => import('./vistas/vendedor/Panel.vue') },
      { path: 'clientes', component: () => import('./vistas/vendedor/Clientes.vue') },
      { path: 'clientes/nuevo', component: () => import('./vistas/vendedor/ClienteForm.vue') },
      { path: 'clientes/:id', component: () => import('./vistas/vendedor/ClienteDetalle.vue'), props: true },
      { path: 'clientes/:id/editar', component: () => import('./vistas/vendedor/ClienteForm.vue'), props: true },
      { path: 'ventas', component: () => import('./vistas/vendedor/Ventas.vue') },
      { path: 'ventas/nueva', component: () => import('./vistas/vendedor/NuevaVenta.vue') },
      { path: 'pagos', component: () => import('./vistas/vendedor/Pagos.vue') },
      { path: 'pagos/nuevo', component: () => import('./vistas/vendedor/RegistrarPago.vue') },
      { path: 'estados-cuenta', component: () => import('./vistas/vendedor/EstadosCuenta.vue') },
      { path: 'catalogo', component: () => import('./vistas/vendedor/Catalogo.vue') },
      { path: 'configuracion', component: () => import('./vistas/vendedor/Configuracion.vue') },
      { path: 'actividad', component: () => import('./vistas/vendedor/Actividad.vue') },
    ],
  },
  { path: '/:ruta(.*)*', redirect: '/' },
]

export const router = createRouter({ history: createWebHistory(), routes: rutas })

router.beforeEach((destino) => {
  if (destino.matched.some((r) => r.meta.requiereSesion) && !sesion.token) {
    return { path: '/login', query: { siguiente: destino.fullPath } }
  }
})
