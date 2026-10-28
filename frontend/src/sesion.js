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

export const sesion = reactive({ token: null, usuario: null, tienda: null, ...leer() })

export function iniciar({ token, usuario, tienda }) {
  Object.assign(sesion, { token, usuario, tienda })
  try { localStorage.setItem(CLAVE, JSON.stringify({ token, usuario, tienda })) } catch { /* sin almacenamiento */ }
}

export function cerrar() {
  Object.assign(sesion, { token: null, usuario: null, tienda: null })
  try { localStorage.removeItem(CLAVE) } catch { /* sin almacenamiento */ }
}
