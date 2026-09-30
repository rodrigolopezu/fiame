// Cliente de la API. Los montos y tasas viajan como texto: el frontend nunca calcula dinero.

async function post(ruta, cuerpo) {
  const respuesta = await fetch(`/api${ruta}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  })
  const datos = await respuesta.json().catch(() => ({}))
  if (!respuesta.ok) throw new Error(mensajeDeError(datos, respuesta.status))
  return datos
}

function mensajeDeError(datos, estado) {
  if (Array.isArray(datos.detail)) {
    return datos.detail
      .map((d) => `${d.loc.filter((p) => p !== 'body').join(' › ')}: ${d.msg.replace('Value error, ', '')}`)
      .join('\n')
  }
  return datos.detail || `Error ${estado} del servidor`
}

export const api = {
  simular: (solicitud) => post('/simular', solicitud),
  tasa: (s) => post('/calculadora/tasa', s),
  interes: (s) => post('/calculadora/interes', s),
  cronograma: (s) => post('/calculadora/cronograma', s),
  mora: (s) => post('/calculadora/mora', s),
  ciclo: (s) => post('/calculadora/ciclo', s),
}
