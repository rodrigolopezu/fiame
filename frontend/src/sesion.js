// Sesión del vendedor: token firmado por el backend, guardado en el navegador.
import { reactive } from 'vue'

const CLAVE = 'fiame.sesion'

function leer() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) || {}
  } catch {
    return {}
  }
}

export const sesion = reactive({ token: null, usuario: null, tienda: null, rol: null, tienda_id: null, ...leer() })

export function iniciar({ token, usuario, tienda, rol, tienda_id }) {
  Object.assign(sesion, { token, usuario, tienda, rol, tienda_id })
  try { localStorage.setItem(CLAVE, JSON.stringify({ token, usuario, tienda, rol, tienda_id })) } catch { /* sin almacenamiento */ }
}

export function cerrar() {
  Object.assign(sesion, { token: null, usuario: null, tienda: null, rol: null, tienda_id: null })
  try { localStorage.removeItem(CLAVE) } catch { /* sin almacenamiento */ }
}
