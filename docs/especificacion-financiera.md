# FiaMe — Especificación financiera

Reglas de cálculo del sistema. Corresponde a las secciones 6c (marco conceptual) y
6d (datos de prueba) del informe. Todas las reglas aplican por igual a cualquier tienda.

## 0. Reglas obligatorias

Estas reglas no se discuten ni se reinterpretan al implementar. Vienen del enunciado
(E), del Anexo A (A), de indicaciones del profesor (P), de su libro (L, ver
[reglas-libro.md](reglas-libro.md)) o de decisiones del equipo (D).

| # | Regla | Origen |
|---|---|---|
| R1 | Año de **360 días**; mes comercial de **30 días**. | A |
| R2 | Conversión entre tasa nominal y efectiva con **fórmula explícita** (sección 1.2). | A |
| R3 | Montos de dinero redondeados a **2 decimales**. | A |
| R4 | Tasas usadas en el cálculo con **al menos 7 decimales**. | A |
| R5 | Orden de imputación de pagos: **mora → interés compensatorio → capital**. | A |
| R6 | Pago en cuotas: **método francés vencido ordinario**, periodos de 30 días. | E |
| R7 | Periodo de **gracia total** desde la compra hasta la fecha de pago; se capitaliza antes de calcular la cuota. | E |
| R8 | Compras a fin de mes: interés compensatorio desde la compra hasta la fecha de pago pactada; interés moratorio por los días de mora. | E |
| R9 | Compras después del corte pasan al mes siguiente. | E |
| R10 | No se permiten compras que excedan el crédito disponible ni pagos parciales. | E |
| R11 | Intereses por mora en un **ítem separado** del estado de cuenta. | E |
| R12 | **Nunca pasar todas las tasas a días y capitalizar día por día.** Cada tasa se convierte **directamente** al plazo que se necesita con un solo exponente. | P |
| R13 | Internamente toda tasa se trabaja como **tasa efectiva**. | D |
| R14 | Al cliente siempre se le informa la **TEA** equivalente. | D |
| R15 | Días entre fechas: **días calendario exactos** (Actual/360). | D, L |
| R16 | Cada monto de dinero se redondea **en el momento en que se obtiene**, y los cálculos siguientes usan el valor ya redondeado. | D, L |
| R17 | En mora se cobran **a la vez** el interés compensatorio y el moratorio por los días de atraso, ambos sobre el monto exigible. | L |
| R18 | En el cronograma francés, la cuota de cada periodo se calcula sobre el **saldo inicial del periodo** (Fórmula 67 del libro). | L |
| R19 | Si una tasa nominal no indica capitalización, se asume **capitalización diaria**. | L |

### Sobre R12
Correcto: la tasa del plazo se obtiene directamente, en un solo paso.

    TE(11 días) = (1 + TEA)^(11/360) − 1
    TEM         = (1 + TEA)^(30/360) − 1

Incorrecto: pasar primero a tasa diaria y luego capitalizar día por día.

    TED         = (1 + TEA)^(1/360) − 1
    TE(11 días) = (1 + TED)^11 − 1          ← no
    TEM         = (1 + TED)^30 − 1          ← no

Aunque sin redondeo den el mismo resultado, no es como opera ninguna entidad
financiera. Además, al redondear la TED a 7 decimales y elevarla después, el error se
acumula.

## 1. Tasas de interés

### 1.1 Registro
Por cliente (y copiado en cada venta):

| Campo | Valores | Obligatorio |
|---|---|---|
| Tipo de tasa | Efectiva / Nominal | Sí |
| Periodo de la tasa | Anual, semestral, cuatrimestral, trimestral, bimestral, mensual, quincenal, diaria | Sí |
| Valor de la tasa | % | Sí |
| Periodo de capitalización | Mismas opciones que el periodo; por defecto **diaria** (R19) | Solo si es nominal |

Lo mismo para la tasa moratoria.

### 1.2 Conversión
Base de 360 días (R1). Cada conversión es directa al plazo requerido (R12).

- Nominal a efectiva: con `p` = días del periodo de la tasa y `c` = días del periodo de
  capitalización, `m = p / c`:

  `TEP(n días) = (1 + TN / m)^(n / c) − 1`

- Efectiva de `p` días a efectiva de `n` días:

  `TEP(n días) = (1 + TE)^(n / p) − 1`

## 2. Conteo de días

- **Días entre fechas**: días calendario exactos (R15). Aplica a la gracia de las compras
  en cuotas, al interés de las compras a fin de mes y a los días de mora.
- **Periodos del cronograma en cuotas**: 30 días cada uno (R1, R6), sin importar los días
  reales entre fechas de pago. Las fechas de pago siguen siendo el mismo día calendario
  de cada mes (por ejemplo, siempre el 26), pero el interés de cada cuota se calcula con
  la TEM.

## 3. Ciclo de corte y pago

- **Hora de corte**: 23:59:59 del día de corte. Una compra hecha el mismo día de corte
  entra en ese ciclo.
- **Fecha de pago de un ciclo**: la primera fecha con el día de pago del cliente que sea
  **posterior** a la fecha de corte.
  - Corte 20, pago 26 → corte 20/09, pago 26/09.
  - Corte 25, pago 5 → corte 25/09, pago 05/10.
- Días de corte y pago limitados a **1–28**.
- **Compras en cuotas**: la gracia va desde la compra hasta la fecha de pago del ciclo en
  que cae la compra; la primera cuota vence un mes después.
  - Compra 15/09 (corte 20, pago 26) → gracia hasta 26/09, cuotas 26/10, 26/11, 26/12.
  - Compra 22/09 (corte 20, pago 26) → gracia hasta 26/10, cuotas 26/11, 26/12, 26/01.

## 4. Mora

- **Base**: el monto total exigible en la fecha de pago (capital + interés compensatorio de
  las compras a fin de mes, o la cuota completa).
- **Días de mora**: días calendario exactos desde la fecha de pago pactada hasta el pago
  efectivo.
- Las tasas son las que el EC guardó al corte (las vigentes del cliente en ese momento).
- Por esos días se cobran **dos intereses** sobre la misma base (R17):

      Interés compensatorio por mora = base × ((1 + TEA)^(días_mora / 360) − 1)
      Interés moratorio             = base × ((1 + TEA_mora)^(días_mora / 360) − 1)

  Cada uno se redondea a 2 decimales por separado antes de sumarlo (R16).
- Aplica igual a compras a fin de mes y a cuotas vencidas.
- Se muestran en el ítem separado "Intereses por mora" (R11), con las dos líneas.
- La mora **no se proyecta**. Se calcula con los días reales de atraso al momento de
  consultar o pagar. Un EC vencido no se arrastra al siguiente EC como deuda: sigue siendo
  su propio documento, y el nuevo EC solo lo menciona como informativo.
- **Desglose del pago** (R5): el interés moratorio va a *mora*; el compensatorio por mora va
  a *interés compensatorio*.

## 5. Moneda

- Tipo de cambio con **3 decimales**.
- El precio convertido a la moneda del cliente se redondea a 2 decimales al registrar
  la venta (R16).

## 6. Redondeo

### 6.1 Dinero
- 2 decimales, redondeo aritmético (half-up).
- Se redondea cada monto en el momento en que se obtiene (R16): saldo capitalizado tras
  la gracia, cuota, interés de cada cuota, amortización, saldo, interés de cada compra a
  fin de mes e interés moratorio.
- El siguiente cálculo usa el valor ya redondeado.

- **Cuotas**: se calculan en cada periodo sobre el saldo inicial ya redondeado (R18).
  Por eso las cuotas pueden diferir en ±0.01 entre periodos, y la última deja el saldo
  exactamente en cero.

### 6.2 Tasas
- Para el cálculo: **7 decimales en porcentaje** (por ejemplo, TEM = 1.8087582 %, que como
  fracción es 0.018087582).
- Para mostrar en pantalla y reportes: 4 decimales (1.8088 %). **Solo es presentación**;
  nunca se calcula con la tasa de 4 decimales.

### 6.3 Factores
Los factores intermedios que no son ni dinero ni tasa (por ejemplo `(1 + i)^n` en la
fórmula de la cuota) no se redondean.

## 7. Cronograma en cuotas (método francés)

Basado en la metodología del libro (pp. 209–214), adaptada a la gracia por días del
enunciado.

1. **Monto financiado** `C` = precio de lista (convertido a la moneda del cliente si aplica).
2. **Gracia total** (R7): `C' = r2(C · (1 + TEA)^(días_gracia / 360))`, con días de gracia en
   días calendario exactos desde la compra hasta la fecha de pago del ciclo.
3. **TEM** = `r7((1 + TEA)^(30/360) − 1)` (R1, R12).
4. Para cada periodo `nc = 1..n`:
   - `SI` = `C'` si `nc = 1`; si no, el saldo final del periodo anterior.
   - `Interés = r2(SI · TEM)`
   - `Cuota = r2(SI · TEM · (1 + TEM)^(n − nc + 1) / ((1 + TEM)^(n − nc + 1) − 1))` (R18).
     En la última cuota esta fórmula da `SI · (1 + TEM)`; se toma `SI + Interés` para que
     el saldo quede en cero exacto.
   - `Amortización = Cuota − Interés`
   - `Saldo final = SI − Amortización`
5. Fechas de vencimiento: el día de pago del cliente, un mes después de la fecha de fin
   de la gracia y así sucesivamente.

`r2` = redondeo a 2 decimales (half-up); `r7` = redondeo a 7 decimales en porcentaje
(9 como fracción).

### Ejemplo: licuadora S/ 165, TEA 24 %, compra 15/09, pago día 26, 3 cuotas

- Gracia: 11 días → `C' = r2(165 · 1.24^(11/360)) = 166.09`
- `TEM = 1.8087582 %`

| Cuota | Vence | Saldo inicial | Interés | Cuota | Amortización | Saldo final |
|---|---|---|---|---|---|---|
| 1 | 26/10 | 166.09 | 3.00 | 57.38 | 54.38 | 111.71 |
| 2 | 26/11 | 111.71 | 2.02 | 57.37 | 55.35 | 56.36 |
| 3 | 26/12 | 56.36 | 1.02 | 57.38 | 56.36 | 0.00 |
