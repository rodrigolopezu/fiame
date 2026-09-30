# FiaMe — Funcionamiento

Documento vivo con las decisiones funcionales del sistema. Las reglas de cálculo
(fórmulas, redondeo, conteo de días) se detallan aparte en la especificación financiera.

## Roles

| Rol | Acceso | Qué puede hacer |
|---|---|---|
| Administrador del sistema | Usuario y clave | Dar de alta y de baja a tiendas (tenants) y crear sus credenciales. **No ve** clientes, ventas ni pagos de ninguna tienda. |
| Vendedor (tienda) | Usuario y clave | Gestiona su catálogo, sus clientes, ventas a crédito, cobros y estados de cuenta. Una tienda = un vendedor. |
| Cliente | Enlace único con clave (sin cuenta) | Solo consulta su estado de cuenta, cuotas y fechas de pago. No paga por la plataforma. |

> Pendiente de validar con el profesor: el enunciado (punto 1) menciona acceso del cliente
> con usuario y clave; se propone reemplazarlo por un enlace único.

## Configuración de la tienda (valores predeterminados)

El vendedor define valores por defecto que se precargan al registrar un cliente y que
puede modificar para cada cliente según el riesgo que perciba:

- Límite de crédito
- Tipo de tasa (nominal / efectiva) y su valor; periodo de capitalización si es nominal
- Tasa moratoria (nominal / efectiva)
- Moneda
- Máximo número de meses
- Día de corte y día de pago

Cambiar los valores por defecto no afecta a clientes ya registrados.

## Catálogo

- Productos/servicios con: descripción, marca, proveedor (opcional), unidad de medida,
  imagen, precio contado, precio de lista (crédito) y si permite pago en cuotas.
- Sin inventario ni stock (fuera de alcance según el enunciado).

## Clientes

- Las condiciones de crédito son **por cliente**, no por venta.
- Cada venta a crédito guarda una **copia de las condiciones vigentes** del cliente
  (tipo y valor de tasa, capitalización, tasa moratoria). Si luego se cambian las
  condiciones del cliente, solo afectan a ventas nuevas.

## Moneda

- La moneda del crédito es la del cliente; los precios del catálogo tienen su moneda.
- Si difieren, el vendedor ingresa el **tipo de cambio** al registrar la venta. Se precarga
  como referencia el tipo de cambio compra/venta obtenido de una API externa, y el valor
  usado queda guardado en la venta.

## Ventas

- Solo se registran **ventas a crédito**. Las ventas al contado no pasan por la plataforma.
- Se usa el **precio de lista**.
- Modalidades:
  - **Pago único a fin de mes**: si la compra es antes del corte, se paga en la fecha de pago
    de ese mes; si es después del corte, en la del mes siguiente.
  - **En cuotas** (solo productos que lo permiten): el vendedor elige el número de cuotas al
    registrar la venta, sin exceder el máximo del cliente. Método francés vencido ordinario,
    meses de 30 días, con periodo de gracia total capitalizado hasta la primera fecha de pago.
- No se permite una venta que exceda el crédito disponible.
- Una venta solo puede **anularse antes de ser incluida en un estado de cuenta**.
- Si el cliente tiene un estado de cuenta **vencido**, no se le pueden registrar ventas nuevas.
  La tienda puede desactivar este bloqueo en su configuración.

## Línea de crédito (revolvente)

- Una venta consume de la línea su **precio de lista**.
- La línea **se recupera al pagar**, como en una tarjeta de crédito:
  - Pago a fin de mes: al pagar se libera el precio de lista completo.
  - Cuotas: cada cuota pagada libera su amortización; al pagar la última se libera
    el saldo hasta completar el precio de lista original.

## Pagos

- Solo se paga contra un estado de cuenta ya generado en el corte, y **por su total**.
  No se permiten pagos parciales.
- Si hay varios estados pendientes, se paga **primero el más antiguo**. Se puede pagar solo
  ese o varios juntos, siempre completos y en orden.
- El monto lo calcula el sistema según la fecha del pago; el vendedor no lo escribe:
  - Hasta la fecha de pago (inclusive): el total del estado de cuenta. El interés
    compensatorio va hasta la fecha de pago pactada, aunque el cliente pague antes.
  - Después de la fecha de pago: el total más los **intereses por mora** (compensatorio
    por mora + moratorio) calculados con los días reales de atraso.
- Cada pago se guarda desglosado según el orden de imputación del Anexo A:
  - **Mora**: interés moratorio.
  - **Interés compensatorio**: interés de las compras y cuotas, más el compensatorio por mora.
  - **Capital**: precio de lista de las compras a fin de mes y amortización de las cuotas.
- La parte de capital libera la línea de crédito.
- Medio de pago (efectivo, Yape/Plin, transferencia): solo informativo, el pago ocurre
  fuera de la app.
- Cada pago genera una **constancia** con el desglose, visible para el cliente.
- Un pago no se borra: se **anula** indicando el motivo (queda registrado).
- Fuera de alcance por ahora: adelantar pagos de compras que aún no entran en un corte
  y prepagar cuotas.

## Panel del vendedor

- **Vista general**: cuánto debe cobrar y en qué fechas, deuda vencida, clientes en mora.
- **Vista por cliente**: compras, cuotas, pagos, estado de cuenta e historial.

## Score crediticio privado

- Puntaje de 0 a 100 por cliente, visible **solo para el vendedor de esa tienda**, con un
  semáforo (verde / amarillo / rojo) derivado del puntaje.
- Sirve para decidir si bajar el límite o subir la tasa en el siguiente periodo.
- Ranking de clientes que más se demoran o que están vencidos.
- *Pendiente*: definir los factores y sus pesos (puntualidad, días de mora promedio,
  deuda vencida actual, uso de la línea, antigüedad) y los umbrales del semáforo.

## Estado de cuenta (EC)

- Se genera **automáticamente** al cierre del día de corte (23:59:59), uno por cliente activo,
  **aunque no tenga nada que pagar** (en ese caso muestra total S/ 0.00 y nace como pagado),
  para que el cliente tenga su historial mensual.
- Guarda las **tasas vigentes del cliente al corte**; con ellas se calculan los intereses por
  mora si se paga tarde.
- Una vez generado **queda congelado**: no se edita. Refleja solo hechos conocidos al corte.
- Contenido:
  1. Cabecera: cliente, periodo, fecha de corte, fecha de pago, moneda, TEA compensatoria y
     moratoria, línea de crédito (total, usada, disponible).
  2. Compras a fin de mes del periodo, ordenadas por fecha: capital, días hasta la fecha de
     pago, interés compensatorio y total.
  3. Cuotas que vencen en esta fecha de pago: número de cuota, capital, interés y total.
  4. Totales: capital, interés compensatorio y **total a pagar**.
  5. Informativo: cuotas futuras pendientes, compras posteriores al corte (irán al siguiente EC)
     y **estados anteriores vencidos**, con su monto exigible y los días de atraso a la fecha
     de corte. No se proyecta mora a futuro.
- **Estados**: pendiente → pagado, o pendiente → vencido → pagado con mora.
- Un EC vencido sigue siendo su propio documento. El monto para pagarlo se calcula **al día**
  (exigible + intereses por mora hasta hoy). Cuando se paga, los intereses por mora aparecen
  como **ítem separado** en la liquidación y en la constancia.

## Portal del cliente (enlace)

- Estados de cuenta (todos, incluidos los de S/ 0.00) y su estado.
- Si tiene un EC vencido: cuánto debe **a hoy**, con el detalle de los intereses por mora.
- Resumen en vivo: línea disponible, compras del periodo en curso y cronograma de cuotas.
- Constancias de pago.
