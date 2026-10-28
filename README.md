# FiaMe

Control de créditos (fiados) de tiendas de barrio. Trabajo final de SI642 Finanzas e
Ingeniería Económica.

La aplicación tiene tres partes:

- **Vendedor** (`/vendedor`): el menú principal es un círculo con el resumen del día al centro y
  un anillo con cada sección (nueva venta, registrar pago, clientes, estados de cuenta, ventas,
  pagos, panel, catálogo, configuración y actividad). Desde cualquier sección se vuelve al
  círculo con el botón **Menú** o la tecla **Esc**. Por ahora hay un único vendedor (una tienda).
- **Vista simple / detallada**: un interruptor general cambia el nivel de detalle con que se
  presenta la información (lenguaje cotidiano o términos financieros con su explicación). Los
  datos y las operaciones son los mismos en ambas vistas.
- **Portal del cliente** (`/portal`): el cliente consulta sus estados de cuenta, cuotas y
  constancias de pago con un código que le entrega el vendedor.
- **Simulador y calculadoras** (`/simulador`): herramienta de verificación de los cálculos,
  independiente de la base de datos.

## Estructura

```
docs/                    especificación, funcionamiento, modelo de datos, casos de prueba e informe
backend/
  app/finanzas/          núcleo financiero: tasas, fechas, cronograma, mora (funciones puras)
  app/dominio.py         reglas de negocio comunes: ventas, liquidación de pagos, score
  app/servicios/         operaciones sobre la base de datos: clientes, ventas, cortes, pagos
  app/simulador/         motor del simulador (sin base de datos)
  app/rutas*.py          endpoints: calculadoras, vendedor y portal
  app/semilla.py         datos de prueba
  tests/                 ejercicios del libro, casos de prueba y aplicación
frontend/                Vue 3 + Vite + Vue Router
referencia/              calculadora de referencia independiente (oráculo de los casos)
```

## Cómo levantarlo

**Backend** (Python 3.12 o superior). En local usa SQLite (`backend/fiame.db`), que se crea con
los datos de prueba la primera vez que arranca:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

La documentación interactiva de la API queda en http://127.0.0.1:8000/docs.

**Frontend** (Node 20 o superior), en otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5180. El frontend redirige `/api` al backend del puerto 8000.

**Tests:** usan su propia base de datos temporal.

```bash
cd backend
.venv/bin/pytest -v
```

**Volver a los datos de prueba** (con el backend detenido):

```bash
cd backend
.venv/bin/python -m app.semilla --reiniciar
```

## Datos de prueba

| Qué | Dato |
|---|---|
| Tienda | Bodega Doña Rosa (TEA 24 %, moratoria TEA 36 %, corte 20, pago 26) |
| Vendedor | usuario `vendedor`, contraseña `fiame2026` |
| Catálogo | 12 productos; la licuadora y el parlante importado (en dólares) permiten cuotas |
| Cliente 1 | Juan Pérez Quispe · TEA 24 % · paga a tiempo salvo una vez · código del portal `J7KQ-M4HP` |
| Cliente 2 | Ana Torres Ríos · TNA 30 % c. mensual · compra en dólares · estado de cuenta vencido · código `A7NT-X4PL` |

El historial de los clientes va de julio a septiembre de 2026. Para ver cortes, vencimientos y
mora sin esperar, el vendedor puede **adelantar la fecha del sistema** desde la barra superior
(solo en desarrollo; la fecha nunca retrocede).

## Verificación

- [docs/verificacion-libro.md](docs/verificacion-libro.md): ejercicios del libro del curso
  recalculados con el núcleo financiero.
- `backend/tests/test_aplicacion.py` compara el historial guardado en la base de datos con el
  simulador: ambos motores dan las mismas cifras.
