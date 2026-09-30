# FiaMe

Control de créditos (fiados) de tiendas de barrio. Trabajo final de SI642 Finanzas e
Ingeniería Económica.

Esta primera versión implementa **la lógica financiera completa** y un **simulador web** del
crédito de un cliente. Todavía no incluye tiendas, usuarios ni base de datos.

## Estructura

```
docs/                    especificación, funcionamiento, modelo de datos, casos de prueba e informe
backend/
  app/finanzas/          núcleo financiero: tasas, fechas, cronograma, mora (funciones puras)
  app/simulador/         motor que simula ventas, cortes y pagos a lo largo del tiempo
  app/rutas.py           endpoints de la API
  tests/                 ejercicios del libro y casos de prueba
frontend/                simulador web en Vue 3 + Vite
referencia/              calculadora de referencia independiente (oráculo de los casos)
```

## Cómo levantarlo

**Backend** (Python 3.12 o superior):

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

**Tests:**

```bash
cd backend
.venv/bin/pytest -v
```

## Qué se puede hacer en el simulador

- Definir las condiciones del cliente: moneda, límite, máximo de cuotas, días de corte y pago,
  y las tasas compensatoria y moratoria (efectivas o nominales con capitalización).
- Registrar eventos con fecha:
  - ventas a fin de mes o en cuotas, con varios productos y en otra moneda;
  - pagos de uno o varios estados de cuenta;
  - cambios de tasas o de límite;
  - anulaciones de ventas.
- Ver los resultados a una fecha:
  - bitácora con cada operación y la línea disponible;
  - ventas con su cronograma;
  - estados de cuenta generados en cada corte, con la mora al día si están vencidos;
  - pagos con su desglose mora → interés → capital.
- Cargar los dos casos de prueba de `docs/casos-de-prueba.md`.
- Usar las calculadoras (tasas, interés entre fechas, cronograma, mora y ciclo) con ejemplos
  del libro del curso.

La verificación contra el libro está en [docs/verificacion-libro.md](docs/verificacion-libro.md).
