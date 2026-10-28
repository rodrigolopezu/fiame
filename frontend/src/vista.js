// Modo de presentación: "simple" (lenguaje cotidiano) o "detallada" (cifras y términos
// financieros). Solo cambia qué se muestra y cómo se dice: los datos y las operaciones
// disponibles son los mismos en ambos modos.
import { computed, reactive, watch } from 'vue'

const CLAVE = 'fiame.vista'

function leer() {
  try { return localStorage.getItem(CLAVE) !== 'detallada' } catch { return true }
}

export const vista = reactive({ simple: leer() })

watch(() => vista.simple, (simple) => {
  try { localStorage.setItem(CLAVE, simple ? 'simple' : 'detallada') } catch { /* sin almacenamiento */ }
})

// Un componente puede fijar su modo con la prop `modo` (p. ej. el simulador, siempre detallado).
export function usarSimple(props) {
  return computed(() => (props.modo ? props.modo === 'simple' : vista.simple))
}
