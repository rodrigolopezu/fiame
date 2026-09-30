# Reglas extraídas del libro del profesor

Fuente: Martín Senmache Sarmiento, J. M. (2025). *Matemática Financiera* (5.ª ed.).
T-Asesora con Precisión S.A.C. / e-financebook.com. Lima, Perú.

Resumen de las fórmulas y convenciones del libro que aplican a FiaMe, con la página
donde aparecen, para citarlas en el informe. Las fórmulas se escriben con la notación
del libro. Cada regla se verificó recalculando respuestas de ejercicios del libro.

## 1. Convenciones generales

| # | Regla | Pág. | Verificación |
|---|---|---|---|
| L1 | El año puede ser ordinario (360) o exacto (365); nunca 366, aunque sea bisiesto. FiaMe usa 360 por el Anexo A. | 20–21 | — |
| L2 | El tiempo entre dos fechas se cuenta en **días calendario exactos**. | 44 (ej. 3-3) | 14/02/2010 → 13/09/2011 = 576 días reales; con TNA 18.5 % c.d. da S/ 4,033.10, igual que el libro. Con 30/360 (569 días) daría S/ 4,018.63. |
| L3 | La tasa y el tiempo deben expresarse en la misma unidad antes de operar. | 18 | — |
| L4 | Si una tasa nominal no indica capitalización, el libro asume **capitalización diaria**. | 81 (ej. 4-11), 83 (ej. 4-23) | TNS 4 % → TEM 0.66881927 %, solo cuadra con c.d. |
| L5 | Las tasas se reportan con 7 a 9 decimales en porcentaje (p. ej. 0.9488793 %, 26.97346485 %). | 80–83 | — |
| L6 | Cada monto de interés se redondea a 2 decimales **antes** de sumarlo al total. | 129 (ej. 5-36c) | Ic 77.91 + Im 183.62 + costos → S/ 20,331.53, igual que el libro. Sin redondear saldría 20,331.52. |

## 2. Tasa nominal (capítulo 3)

- `m` = días del periodo de la tasa ÷ días del periodo de capitalización. (p. 36)
- `n` = días del tiempo transcurrido ÷ días del periodo de capitalización. (p. 36)
- `i' = TN / m` (Fórmula 8, p. 36)
- `S = C · (1 + TN/m)^n` (Fórmula 9, p. 41)

## 3. Tasa efectiva (capítulo 4)

- Tercer principio fundamental: `TEP = S/C − 1`. (p. 71)
- **Nominal → efectiva**: `TEP = (1 + TN/m)^n − 1`, con `n` = días de la TEP buscada ÷
  días de capitalización. (Fórmula 18, p. 75)
- **Efectiva → nominal**: `TN = m · [(1 + TEP)^(1/n) − 1]`. (Fórmula 17, p. 75)
- **Efectiva → efectiva**: `TEP₂ = (1 + TEP₁)^(N° días TEP₂ / N° días TEP₁) − 1`.
  Ejemplo del propio libro: `TEM = (1 + TEA)^(30/360) − 1`. (Fórmula 19, pp. 73 y 76)
- **Valor futuro con tasa efectiva**: `S = C · (1 + TEP)^(N° días a trasladar / N° días TEP)`.
  (Fórmula 20, p. 76)

La conversión es siempre **directa** entre el periodo dado y el requerido, con un solo
exponente de días (coincide con la regla R12 de la especificación).

## 4. Interés compensatorio y moratorio después del vencimiento (capítulo 5)

- **Interés compensatorio (Ic)**: se sigue cobrando por los días transcurridos después
  del vencimiento, sobre el valor a pagar en el vencimiento. (Fórmulas 34 y 35, p. 114)
- **Interés moratorio (Im)**: se cobra por esos mismos días, sobre el mismo valor, con la
  tasa moratoria (efectiva o nominal con su capitalización). (Fórmulas 36 y 37, pp. 114–115)
- En mora se cobran **ambos a la vez**: "además de los clásicos intereses compensatorios,
  intereses moratorios". (ej. 5-39, p. 131)
- Fórmulas (reconstruidas y verificadas con el ej. 5-36c, p. 129):

      Ic = Valor a pagar · [(1 + TEPc)^(días de mora / N° días TEPc) − 1]
      Im = Valor a pagar · [(1 + TEPm)^(días de mora / N° días TEPm) − 1]

- Los costos fijos (portes, gastos) no generan interés moratorio. (p. 129)
- **TCEA**: se calcula como la TIR de los flujos, anualizada con 360 días. (Fórmulas 38–39,
  p. 115; p. 214)

## 5. Anualidades / método francés (capítulos 7 y 8)

- **Cuota vencida**: `R = C · [TEP · (1 + TEP)^n] / [(1 + TEP)^n − 1]`. (Fórmulas 49–50, p. 168)
- **Gracia total**: no se paga interés ni amortización; el interés se capitaliza y
  aumenta el saldo. (pp. 179, 212)
- **Gracia parcial**: solo se paga el interés; el saldo no cambia. (p. 212)
- **Cuota del periodo sobre el saldo inicial** (Fórmula 67, p. 209–210):

      R = SI · [TEP · (1 + TEP)^(n − nc + 1)] / [(1 + TEP)^(n − nc + 1) − 1]

  El libro recalcula la cuota **en cada periodo** con esta fórmula a partir del saldo
  inicial del periodo.
- **Algoritmo del cronograma francés** (metodología Interbank, pp. 211–214), por periodo:
  1. `TEP = (1 + TEA)^(frecuencia / días por año) − 1`
  2. Saldo inicial = monto del préstamo (periodo 1) o saldo final del periodo anterior.
  3. Interés = saldo inicial · TEP
  4. Cuota: 0 si hay gracia total; = interés si hay gracia parcial; Fórmula 67 si no hay gracia.
  5. Amortización = cuota − interés (0 si hay gracia).
  6. Saldo final: saldo inicial + interés (gracia total); saldo inicial (gracia parcial);
     saldo inicial − amortización (sin gracia).
  7. Totales: la suma de amortizaciones debe ser igual al monto del préstamo.
  8. TCEA = TIR de la columna de flujos, anualizada.

## 6. Marco legal citado por el libro (pp. 14–16)

- Ley de Títulos Valores, Ley N.° 27287.
- Ley General del Sistema Financiero y de Seguros y Orgánica de la SBS, Ley N.° 26702.
- Reglamento de Transparencia de Información y Contratación con Usuarios del Sistema
  Financiero, Res. SBS N.° 8181-2012 (modificada por Res. SBS N.° 2668-2013).
- Reglamento de Tarjetas de Crédito, Res. SBS N.° 0264-2008 (mod. Res. SBS N.° 9605-2012).
- Código de Protección y Defensa del Consumidor, Ley N.° 29571.

## 7. Lo que el libro no cubre

- **Redondeo**: el libro no da una regla explícita (0 menciones). Rige el Anexo A.
- **Orden de imputación de pagos** (mora → interés → capital): no aparece. Rige el Anexo A.
- **Ciclo de corte y pago**: no aparece. Rige el enunciado y las decisiones del equipo.
