# 6. Análisis y diseño del sistema

## 6a. Análisis de datos

Todos los montos y tasas se manejan como **decimales exactos** (`Decimal`), nunca como números
de punto flotante (`Float`), para cumplir el redondeo que exige el Anexo A.

### Constantes

| Constante | Descripción | Valor |
|---|---|---|
| DIAS_ANIO | Días del año ordinario para convertir tasas | 360 |
| DIAS_MES | Días del mes comercial (periodo de cada cuota) | 30 |
| DEC_DINERO | Decimales de los montos de dinero | 2 (half-up) |
| DEC_TASA | Decimales de las tasas, expresadas en porcentaje | 7 (half-up) |
| HORA_CORTE | Hora de cierre del día de corte | 23:59:59 |

### Datos de entrada

| Variable | Descripción | Tipo | Rango / tamaño | Formato | Valor por defecto | Restricciones |
|---|---|---|---|---|---|---|
| tipo_tasa | Tipo de la tasa compensatoria pactada | Enum | EFECTIVA, NOMINAL | Texto | Configuración de la tienda | Obligatorio |
| periodo_tasa | Periodo en que se expresa la tasa | Enum | Anual, semestral, cuatrimestral, trimestral, bimestral, mensual, quincenal, diaria | Texto | Anual | Obligatorio |
| valor_tasa | Valor de la tasa compensatoria | Decimal(12,7) | > 0 | #0.0000000 % | Configuración de la tienda | Obligatorio |
| capitalizacion | Periodo de capitalización de la tasa nominal | Enum | Mismas opciones que periodo_tasa | Texto | Diaria | Solo si es NOMINAL; no puede ser mayor que periodo_tasa |
| tasa_moratoria | Tipo, periodo, valor y capitalización de la tasa moratoria | Igual a la compensatoria | Igual a la compensatoria | Igual | Configuración de la tienda | Obligatorio |
| moneda | Moneda del crédito del cliente | Enum | PEN, USD | Texto | PEN | No se puede cambiar si hay deuda pendiente |
| limite_credito | Monto máximo de deuda del cliente | Decimal(12,2) | > 0 | S/ #,##0.00 | Configuración de la tienda | — |
| max_meses | Número máximo de cuotas | Integer | 1 – 36 | # | Configuración de la tienda | — |
| dia_corte | Día del mes en que se cierra el ciclo | Integer | 1 – 28 | # | Configuración de la tienda | No se puede cambiar si hay deuda pendiente |
| dia_pago | Día del mes en que vence el pago | Integer | 1 – 28 | # | Configuración de la tienda | No se puede cambiar si hay deuda pendiente |
| precio_contado | Precio al contado del producto | Decimal(12,2) | > 0 | S/ #,##0.00 | — | — |
| precio_lista | Precio a crédito del producto | Decimal(12,2) | ≥ precio_contado | S/ #,##0.00 | — | Es el precio que se usa en la venta |
| moneda_producto | Moneda del precio del producto | Enum | PEN, USD | Texto | Moneda de la tienda | — |
| permite_cuotas | Si el producto puede venderse en cuotas | Boolean | Sí / No | Casilla | No | Al menos una modalidad habilitada |
| fecha_compra | Fecha y hora de la venta | Timestamp | ≤ ahora | dd/mm/aaaa hh:mm | Ahora | — |
| cantidad | Cantidad vendida de cada producto | Decimal(10,3) | > 0 | #,##0.### | 1 | — |
| modalidad | Forma de pago de la venta | Enum | FIN_DE_MES, CUOTAS | Texto | FIN_DE_MES | CUOTAS solo si todos los productos lo permiten |
| n_cuotas | Número de cuotas | Integer | 1 – max_meses | # | 1 | Solo si la modalidad es CUOTAS |
| tipo_cambio | Tipo de cambio entre la moneda del producto y la del cliente | Decimal(8,3) | > 0 | #0.000 | Valor del día (API) | Solo si las monedas difieren |
| fecha_pago_efectivo | Fecha en que el cliente paga | Date | ≤ hoy | dd/mm/aaaa | Hoy | — |
| medio_pago | Medio con que se pagó | Enum | Efectivo, Yape, Plin, transferencia, otro | Texto | Efectivo | Solo informativo |
| k | Cantidad de estados de cuenta a pagar | Integer | 1 – pendientes | # | 1 | Se pagan completos, del más antiguo al más reciente |

### Datos de salida

| Variable | Descripción | Tipo | Condición | Formato |
|---|---|---|---|---|
| TEA | Tasa efectiva anual equivalente, informada al cliente | Decimal(12,9) | ≥ 0 | #0.0000 % |
| interes_compra | Interés compensatorio de una compra a fin de mes | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| total_compra | Capital + interés de una compra a fin de mes | Decimal(12,2) | > 0 | S/ #,##0.00 |
| cronograma | Plan de pagos: N°, vencimiento, saldo inicial, interés, cuota, amortización, saldo final | Tabla | n filas | Tabla |
| cuota | Monto de cada cuota | Decimal(12,2) | > 0 | S/ #,##0.00 |
| fecha_corte / fecha_pago | Fechas del ciclo de la compra o del estado de cuenta | Date | fecha_pago > fecha_corte | dd/mm/aaaa |
| estado_cuenta | Compras y cuotas del ciclo con capital, interés y total a pagar | Documento | Uno por cliente y corte | Tabla + totales |
| interes_comp_mora | Interés compensatorio por los días de atraso | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| interes_moratorio | Interés moratorio por los días de atraso | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| desglose_pago | Mora, interés compensatorio y capital del pago | Decimal(12,2) × 3 | Suma = total pagado | S/ #,##0.00 |
| credito_disponible | Línea de crédito disponible del cliente | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |

### Datos intermedios

| Variable | Descripción | Tipo | Tamaño | Formato |
|---|---|---|---|---|
| p | Días del periodo de la tasa | Integer | 1 – 360 | # |
| c | Días del periodo de capitalización | Integer | 1 – 360 | # |
| m | Periodos de capitalización en el periodo de la tasa (p / c) | Decimal | > 0 | #,##0.#### |
| TE_n | Tasa efectiva para n días | Decimal(12,9) | ≥ 0 | #0.0000000 % |
| TEM | Tasa efectiva mensual (30 días) | Decimal(12,9) | ≥ 0 | #0.0000000 % |
| dias | Días calendario entre la compra y la fecha de pago | Integer | ≥ 0 | # |
| dias_gracia | Días de gracia total de una venta en cuotas | Integer | ≥ 0 | # |
| capital | Suma de subtotales de la venta, en la moneda del cliente | Decimal(12,2) | > 0 | S/ #,##0.00 |
| capital_capitalizado | Capital más el interés de la gracia | Decimal(12,2) | ≥ capital | S/ #,##0.00 |
| SI_k, I_k, A_k, SF_k | Saldo inicial, interés, amortización y saldo final de la cuota k | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| f | Factor (1 + TEM)^(n − k + 1) | Decimal | > 1 | Sin redondeo |
| libera_k | Parte de la cuota k que libera la línea de crédito | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| credito_usado | Capital de las ventas no anuladas menos lo liberado por pagos | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| exigible | Total a pagar del estado de cuenta en su fecha de pago | Decimal(12,2) | ≥ 0 | S/ #,##0.00 |
| dias_mora | Días calendario entre la fecha de pago y el pago efectivo | Integer | ≥ 0 | # |

## 6b. Diseño de la interfaz

*[Pendiente: capturas del prototipo.]*

Pantallas:

| # | Pantalla | Rol | Contenido |
|---|---|---|---|
| 1 | Inicio de sesión | Todos | Usuario y contraseña |
| 2 | Tiendas | Administrador | Lista de tiendas, alta y baja, creación de credenciales |
| 3 | Panel | Vendedor | Cobros próximos, estados de cuenta vencidos, clientes en mora y semáforo |
| 4 | Configuración | Vendedor | Valores por defecto para nuevos clientes |
| 5 | Catálogo | Vendedor | Lista de productos y formulario con imagen, precios y modalidades |
| 6 | Clientes | Vendedor | Lista y formulario con las condiciones de crédito; muestra la TEA equivalente al escribir la tasa |
| 7 | Detalle del cliente | Vendedor | Línea de crédito, ventas, cuotas, estados de cuenta, pagos y enlace del portal |
| 8 | Nueva venta | Vendedor | Productos, modalidad y cuotas, con vista previa del interés o del cronograma antes de confirmar |
| 9 | Estado de cuenta | Vendedor y cliente | Detalle del ciclo y total a pagar |
| 10 | Registrar pago | Vendedor | Liquidación al día (con mora si corresponde) y desglose |
| 11 | Portal del cliente | Cliente | Vista móvil de sus estados de cuenta, cuotas y constancias |

**Ayuda en cada campo** (requisito del enunciado): cada campo de los formularios tiene un
ícono **?** que muestra una breve explicación del campo, su formato y un ejemplo. Además, el
sistema incluye una página de **Guía de uso** con los pasos de cada proceso.

## 6c. Marco conceptual (fórmulas)

Las fórmulas siguen el libro *Matemática Financiera* (Martín Senmache, 2025); se indica el
número de fórmula del libro cuando corresponde.

**1. Redondeo**

$$r_2(x) = \text{redondeo half-up a 2 decimales} \qquad r_7(x) = \text{redondeo half-up a 7 decimales en porcentaje}$$

Valores:
- Se aplica `r2` a todo monto de dinero en el momento en que se obtiene, y `r7` a toda tasa
  antes de usarla.

**2. Tasa efectiva a tasa efectiva** (Fórmula 19)

$$TEP_2 = (1 + TEP_1)^{\frac{N_2}{N_1}} - 1$$

Valores:
- TEP₁: tasa efectiva dada, expresada en N₁ días.
- TEP₂: tasa efectiva buscada, para N₂ días.

**3. Tasa nominal a tasa efectiva** (Fórmula 18)

$$TEP = \left(1 + \frac{TN}{m}\right)^{n} - 1 \qquad m = \frac{p}{c} \qquad n = \frac{N}{c}$$

Valores:
- TN: tasa nominal, expresada en p días.
- c: días del periodo de capitalización.
- m: número de capitalizaciones en el periodo de la tasa.
- n: número de capitalizaciones en los N días de la tasa efectiva buscada.

La conversión siempre es **directa** al plazo requerido, con un solo exponente; nunca se pasa
primero a tasa diaria.

**4. Tasa efectiva anual equivalente (TEA)**

$$TEA = TEP_{360}$$

Valores:
- Se obtiene con la fórmula 2 o la 3, usando N = 360. Se informa siempre al cliente.

**5. Conversión de moneda**

$$subtotal = r_2(cantidad \times precio\_lista \times TC)$$

Valores:
- TC: tipo de cambio de la venta (TC = 1 si el producto está en la moneda del cliente).

**6. Días entre fechas**

$$d = fecha_{final} - fecha_{inicial} \quad \text{(días calendario exactos)}$$

**7. Interés compensatorio de una compra a fin de mes** (Fórmula 20)

$$I = r_2\left(C \times TE_d\right) \qquad TE_d = TEP\ \text{para } d \text{ días}$$

Valores:
- C: capital de la compra (precio de lista).
- d: días desde la compra hasta la fecha de pago.

**8. Capitalización del periodo de gracia total**

$$C' = r_2\left(C \times (1 + TE_g)\right)$$

Valores:
- g: días desde la compra hasta la fecha de pago del ciclo.
- C': capital con el que se calcula el cronograma.

**9. Tasa efectiva mensual del cronograma**

$$TEM = TEP\ \text{para } 30 \text{ días}$$

**10. Cuota del método francés vencido ordinario** (Fórmulas 49 y 67)

$$R_k = r_2\left(SI_k \times \frac{TEM \times (1 + TEM)^{\,n-k+1}}{(1 + TEM)^{\,n-k+1} - 1}\right)$$

Valores:
- SI_k: saldo al iniciar el periodo k (SI₁ = C').
- n: número total de cuotas.
- k: número de la cuota que se calcula.
- Para k = 1 coincide con la cuota clásica R = C' · TEM(1+TEM)ⁿ / ((1+TEM)ⁿ − 1).

**11. Interés, amortización y saldo del periodo k**

$$I_k = r_2(SI_k \times TEM) \qquad A_k = R_k - I_k \qquad SF_k = SI_k - A_k \qquad SI_{k+1} = SF_k$$

Valores:
- En la última cuota: R_n = SI_n + I_n, para que el saldo final sea cero.

**12. Liberación de la línea de crédito**

$$L_k = \min\left(A_k,\ C - \sum_{j<k} L_j\right) \qquad Disponible = Límite - \left(\sum C - \sum L\right)$$

Valores:
- L_k: monto de la línea que libera la cuota k; la línea se recupera como máximo hasta el
  precio de lista de la venta.

**13. Intereses por mora** (Fórmulas 34 a 37)

$$I_{cm} = r_2\left(E \times TEc_{d_m}\right) \qquad I_m = r_2\left(E \times TEm_{d_m}\right)$$

Valores:
- E: monto exigible del estado de cuenta.
- d_m: días de mora, desde la fecha de pago hasta el pago efectivo.
- TEc, TEm: tasas compensatoria y moratoria del estado de cuenta, convertidas a d_m días.

**14. Total a pagar y desglose** (orden de imputación del Anexo A)

$$Total = \underbrace{I_m}_{\text{mora}} + \underbrace{(I_{EC} + I_{cm})}_{\text{interés compensatorio}} + \underbrace{C_{EC}}_{\text{capital}}$$

Valores:
- I_EC y C_EC: interés y capital del estado de cuenta.

## 6d. Diseño de datos de prueba

El detalle completo, paso a paso, está en `casos-de-prueba.md`.

### Caso 1: Bodega, tasa efectiva

**Datos de entrada**

| Campo | Valor |
|---|---|
| Tasa compensatoria | TEA 24 % |
| Tasa moratoria | TEA 36 % |
| Moneda / límite | Soles / S/ 500.00 |
| Día de corte / día de pago | 20 / 26 |
| Venta 1 | 10/09/2026 · Arroz S/ 22.00 · fin de mes |
| Venta 2 | 15/09/2026 · Licuadora S/ 165.00 · 3 cuotas |
| Venta 3 | 22/09/2026 · Arroz S/ 22.00 · fin de mes (después del corte) |
| Venta 4 | 18/10/2026 · Aceite S/ 9.50 · fin de mes |
| Pagos | EC set-2026 el 30/09 (4 días de mora) · EC oct-2026 el 24/10 (anticipado) |

**Datos intermedios**

| Variable | Valor |
|---|---|
| TEM | 1.8087582 % |
| Venta 1: días / TE16 | 16 / 0.9606353 % |
| Venta 2: días de gracia / TE11 / capital capitalizado | 11 / 0.6594496 % / 166.09 |
| Venta 3: días / TE34 | 34 / 2.0523851 % |
| Venta 4: días / TE8 | 8 / 0.4791697 % |
| Mora del 30/09: TEc4 / TEm4 | 0.2392985 % / 0.3422340 % |

| Cuota | Vence | Saldo inicial | Interés | Cuota | Amortización | Saldo final |
|---|---|---|---|---|---|---|
| 1 | 26/10/2026 | 166.09 | 3.00 | 57.38 | 54.38 | 111.71 |
| 2 | 26/11/2026 | 111.71 | 2.02 | 57.37 | 55.35 | 56.36 |
| 3 | 26/12/2026 | 56.36 | 1.02 | 57.38 | 56.36 | 0.00 |

**Datos de salida**

| Resultado | Valor |
|---|---|
| EC set-2026 (pago 26/09) | 22.00 + 0.21 = **S/ 22.21** |
| Pago del 30/09 | 22.21 + 0.05 (compensatorio por mora) + 0.08 (moratorio) = **S/ 22.34** |
| Desglose del pago del 30/09 | Mora 0.08 · Interés 0.26 · Capital 22.00 |
| EC oct-2026 (pago 26/10) | 22.45 + 9.55 + 57.38 = **S/ 89.38** |
| Venta de S/ 400.00 el 16/10 | Rechazada: disponible S/ 313.00 |
| Crédito disponible tras la última cuota | S/ 500.00 (la última cuota libera 55.27, no 56.36) |

### Caso 2: Tienda de belleza, tasa nominal y dólares

**Datos de entrada**

| Campo | Valor |
|---|---|
| Tasa compensatoria | TNA 30 % con capitalización mensual |
| Tasa moratoria | TNA 36 % con capitalización diaria |
| Moneda / límite | Soles / S/ 800.00 |
| Día de corte / día de pago | 25 / 5 del mes siguiente |
| Venta 1 | 26/09/2026 · Kit importado US$ 49.90 · TC 3.520 · 4 cuotas |
| Venta 2 | 03/10/2026 · Limpieza facial S/ 80.00 · fin de mes |
| Venta 3 | 25/10/2026 · Labial S/ 35.00 · fin de mes (el mismo día del corte) |
| Pagos | EC oct-2026 el 03/11 (anticipado) · EC nov-2026 el 15/12 (10 días de mora) |

**Datos intermedios**

| Variable | Valor |
|---|---|
| m / i′ compensatoria | 12 / 2.5 % |
| TEM / TEA compensatoria | 2.5000000 % / 34.4888824 % |
| TEA moratoria | 43.3071610 % |
| Venta 1: capital convertido | r2(49.90 × 3.520) = 175.65 |
| Venta 1: días de gracia / TE40 / capital capitalizado | 40 / 3.3471459 % / 181.53 |
| Venta 2: días / TE33 | 33 / 2.7534120 % |
| Venta 3: días / TE11 | 11 / 0.9095069 % |
| Mora del 15/12: TEc10 / TEm10 | 0.8264838 % / 1.0045120 % |

| Cuota | Vence | Saldo inicial | Interés | Cuota | Amortización | Saldo final |
|---|---|---|---|---|---|---|
| 1 | 05/12/2026 | 181.53 | 4.54 | 48.25 | 43.71 | 137.82 |
| 2 | 05/01/2027 | 137.82 | 3.45 | 48.26 | 44.81 | 93.01 |
| 3 | 05/02/2027 | 93.01 | 2.33 | 48.26 | 45.93 | 47.08 |
| 4 | 05/03/2027 | 47.08 | 1.18 | 48.26 | 47.08 | 0.00 |

**Datos de salida**

| Resultado | Valor |
|---|---|
| EC oct-2026 (pago 05/11) | 82.20 + 35.32 = **S/ 117.52** |
| EC nov-2026 (pago 05/12) | Cuota 1/4 = **S/ 48.25** |
| Pago del 15/12 | 48.25 + 0.40 (compensatorio por mora) + 0.48 (moratorio) = **S/ 49.13** |
| Desglose del pago del 15/12 | Mora 0.48 · Interés 4.94 · Capital 43.71 |
| Crédito disponible después del pago | S/ 668.06 |
