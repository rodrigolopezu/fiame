// Cliente de la API. Los montos y tasas viajan como texto: el frontend nunca calcula dinero.
import { cerrar, sesion } from './sesion'

async function pedir(metodo, ruta, cuerpo) {
  const cabeceras = { 'Content-Type': 'application/json' }
  if (sesion.token) cabeceras.Authorization = `Bearer ${sesion.token}`
  const respuesta = await fetch(`/api${ruta}`, {
    method: metodo,
    headers: cabeceras,
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  })
  const datos = await respuesta.json().catch(() => ({}))
  if (respuesta.status === 401 && ruta !== '/auth/login') {
    cerrar()
    if (!location.pathname.startsWith('/login')) location.assign(`/login?siguiente=${encodeURIComponent(location.pathname)}`)
  }
  if (!respuesta.ok) throw new Error(mensajeDeError(datos, respuesta.status))
  return datos
}

function mensajeDeError(datos, estado) {
  if (Array.isArray(datos.detail)) {
    return datos.detail
      .map((d) => {
        const campo = d.loc.filter((p) => p !== 'body' && typeof p === 'string').join(' › ')
        const mensaje = d.msg.replace('Value error, ', '')
        return campo ? `${campo}: ${mensaje}` : mensaje
      })
      .join('\n')
  }
  return datos.detail || `Error ${estado} del servidor`
}

const get = (ruta) => pedir('GET', ruta)
const post = (ruta, cuerpo = {}) => pedir('POST', ruta, cuerpo)
const put = (ruta, cuerpo) => pedir('PUT', ruta, cuerpo)

// Simulador y calculadoras (sin sesión)
export const api = {
  simular: (solicitud) => post('/simular', solicitud),
  tasa: (s) => post('/calculadora/tasa', s),
  interes: (s) => post('/calculadora/interes', s),
  cronograma: (s) => post('/calculadora/cronograma', s),
  mora: (s) => post('/calculadora/mora', s),
  ciclo: (s) => post('/calculadora/ciclo', s),
}

// Vendedor (con sesión)
export const vendedor = {
  login: (usuario, clave) => post('/auth/login', { usuario, clave }),
  sesion: () => get('/sesion'),
  avanzarFecha: (fecha) => post('/sistema/fecha', { fecha }),
  panel: () => get('/panel'),
  tienda: () => get('/tienda'),
  guardarTienda: (datos) => put('/tienda', datos),
  tipoCambio: () => get('/tipo-cambio'),
  productos: () => get('/productos'),
  crearProducto: (datos) => post('/productos', datos),
  editarProducto: (id, datos) => put(`/productos/${id}`, datos),
  clientes: () => get('/clientes'),
  cliente: (id) => get(`/clientes/${id}`),
  crearCliente: (datos) => post('/clientes', datos),
  editarCliente: (id, datos) => put(`/clientes/${id}`, datos),
  darDeBaja: (id) => post(`/clientes/${id}/baja`),
  reactivar: (id) => post(`/clientes/${id}/reactivar`),
  generarCodigo: (id) => post(`/clientes/${id}/codigo`),
  previsualizarVenta: (datos) => post('/ventas/previsualizar', datos),
  registrarVenta: (datos) => post('/ventas', datos),
  ventas: () => get('/ventas'),
  anularVenta: (id) => post(`/ventas/${id}/anular`),
  estadosCuenta: () => get('/estados-cuenta'),
  liquidacion: (clienteId, cantidad) => get(`/clientes/${clienteId}/liquidacion?cantidad=${cantidad}`),
  registrarPago: (datos) => post('/pagos', datos),
  pagos: () => get('/pagos'),
  anularPago: (id, motivo) => post(`/pagos/${id}/anular`, { motivo }),
  actividad: () => get('/actividad?limite=200'),
}

// Portal del cliente (con código)
export const portal = {
  consultar: (codigo) => post('/portal', { codigo }),
}
