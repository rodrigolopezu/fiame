# FiaMe — Casos de prueba

Sección 6d del informe. Cada cifra se obtuvo aplicando
[especificacion-financiera.md](especificacion-financiera.md) y puede recalcularse con
`python3 referencia/casos.py`. La aplicación debe producir **exactamente** estos valores.

Notación: `r2` = redondeo a 2 decimales; `TEn` = tasa efectiva para n días, redondeada a
7 decimales en porcentaje.

---

## Caso 1 — Bodega, tasa efectiva

**Qué prueba:** tasa efectiva, compras a fin de mes, cuotas con gracia, compra después del
corte, pago con mora, bloqueo por deuda vencida, venta que excede la línea, pago anticipado
y liberación de la línea con tope en el precio de lista.

### Datos

| Campo | Valor |
|---|---|
| Tienda | Bodega Doña Rosa |
| Cliente | Juan |
| Tasa compensatoria | TEA 24 % |
| Tasa moratoria | TEA 36 % |
| Moneda | Soles |
| Límite de crédito | S/ 500.00 |
| Máximo de meses | 3 |
| Corte / pago | Día 20 / día 26 |

### Tasas

- `TEM = (1 + 0.24)^(30/360) − 1 = 1.8087582 %`

### Cronología

| # | Fecha | Evento | Línea usada | Disponible |
|---|---|---|---|---|
| 1 | 10/09 | Arroz 5 kg S/ 22.00, fin de mes | 22.00 | 478.00 |
| 2 | 15/09 | Licuadora S/ 165.00, 3 cuotas | 187.00 | 313.00 |
| 3 | 20/09 | **Corte** → EC set-2026 | | |
| 4 | 22/09 | Arroz 5 kg S/ 22.00, fin de mes (después del corte → EC oct) | 209.00 | 291.00 |
| 5 | 28/09 | Intenta comprar gaseosa S/ 12.00 → **rechazada**: EC set-2026 vencido | 209.00 | 291.00 |
| 6 | 30/09 | Paga EC set-2026 con 4 días de mora: S/ 22.34 | 187.00 | 313.00 |
| 7 | 16/10 | Intenta comprar TV S/ 400.00 → **rechazada**: excede el disponible (313.00) | 187.00 | 313.00 |
| 8 | 18/10 | Aceite 1 L S/ 9.50, fin de mes | 196.50 | 303.50 |
| 9 | 20/10 | **Corte** → EC oct-2026 | | |
| 10 | 24/10 | Paga EC oct-2026 antes de la fecha de pago: S/ 89.38 | 110.62 | 389.38 |
| 11 | 20/11 | **Corte** → EC nov-2026; paga el 26/11: S/ 57.37 | 55.27 | 444.73 |
| 12 | 20/12 | **Corte** → EC dic-2026; paga el 26/12: S/ 57.38 | 0.00 | 500.00 |

### Licuadora: gracia y cronograma

- Gracia total: 15/09 → 26/09 = **11 días**
- `TE11 = 1.24^(11/360) − 1 = 0.6594496 %`
- `Capital capitalizado = r2(165.00 × 1.006594496) = 166.09`

| Cuota | Vence | Saldo inicial | Interés | Cuota | Amortización | Saldo final |
|---|---|---|---|---|---|---|
| 1 | 26/10 | 166.09 | 3.00 | 57.38 | 54.38 | 111.71 |
| 2 | 26/11 | 111.71 | 2.02 | 57.37 | 55.35 | 56.36 |
| 3 | 26/12 | 56.36 | 1.02 | 57.38 | 56.36 | 0.00 |

Cuota 1: `r2(166.09 × 0.018087582 × 1.018087582³ / (1.018087582³ − 1)) = 57.38`.
Cuota 3: `56.36 + 1.02 = 57.38`.

### EC set-2026 (corte 20/09, pago 26/09)

| Fecha | Concepto | Capital | Días | Tasa | Interés | Total |
|---|---|---|---|---|---|---|
| 10/09 | Arroz 5 kg | 22.00 | 16 | TE16 = 0.9606353 % | 0.21 | 22.21 |
| | **Total a pagar** | **22.00** | | | **0.21** | **22.21** |

**Pago del 30/09 (4 días de mora)**

| Concepto | Tasa | Monto |
|---|---|---|
| Exigible EC set-2026 | | 22.21 |
| Interés compensatorio por mora | TE4 = 1.24^(4/360) − 1 = 0.2392985 % | 0.05 |
| Interés moratorio | TE4 = 1.36^(4/360) − 1 = 0.3422340 % | 0.08 |
| **Total pagado** | | **22.34** |

Desglose (mora → interés → capital): mora **0.08**, interés **0.26** (0.21 + 0.05), capital **22.00**.
Libera S/ 22.00 de la línea.

### EC oct-2026 (corte 20/10, pago 26/10)

| Fecha | Concepto | Capital | Días | Tasa | Interés | Total |
|---|---|---|---|---|---|---|
| 22/09 | Arroz 5 kg | 22.00 | 34 | TE34 = 2.0523851 % | 0.45 | 22.45 |
| 18/10 | Aceite 1 L | 9.50 | 8 | TE8 = 0.4791697 % | 0.05 | 9.55 |
| 15/09 | Licuadora, cuota 1/3 | 54.38 | | TEM | 3.00 | 57.38 |
| | **Total a pagar** | **85.88** | | | **3.50** | **89.38** |

Informativo: cuota 2/3 S/ 57.37 (26/11) y cuota 3/3 S/ 57.38 (26/12).

**Pago del 24/10 (anticipado):** S/ 89.38, el mismo total. El interés corre hasta el 26/10
aunque pague antes. Desglose: mora 0.00, interés 3.50, capital 85.88. Libera S/ 85.88.

### EC nov-2026 y dic-2026

- **EC nov-2026:** cuota 2/3 = S/ 57.37 (capital 55.35 + interés 2.02). Pagado el 26/11. Libera 55.35.
- **EC dic-2026:** cuota 3/3 = S/ 57.38 (capital 56.36 + interés 1.02). Pagado el 26/12.
  Libera **55.27**, no 56.36: la línea solo recupera hasta completar el precio de lista
  (165.00 − 54.38 − 55.35 = 55.27). La diferencia de 1.09 es el interés de la gracia
  capitalizado.

---

## Caso 2 — Tienda de belleza, tasa nominal y dólares

**Qué prueba:** tasa nominal con dos capitalizaciones distintas, conversión de moneda,
corte con pago en el mes siguiente, compra en cuotas después del corte, compra el mismo
día del corte, pago anticipado y cuota pagada con mora.

### Datos

| Campo | Valor |
|---|---|
| Tienda | Belleza Carla |
| Cliente | Ana |
| Tasa compensatoria | TNA 30 % con capitalización mensual |
| Tasa moratoria | TNA 36 % con capitalización diaria |
| Moneda | Soles |
| Límite de crédito | S/ 800.00 |
| Máximo de meses | 6 |
| Corte / pago | Día 25 / día 5 del mes siguiente |

### Tasas

- Compensatoria: `m = 360/30 = 12`, `i' = 30 %/12 = 2.5 %`
  - `TEM = (1 + 0.025)^(30/30) − 1 = 2.5000000 %`
  - `TEA = (1 + 0.025)^(360/30) − 1 = 34.4888824 %` (se informa a la clienta, R14)
- Moratoria: `m = 360/1 = 360`, `i' = 36 %/360 = 0.1 %`
  - `TEA = (1 + 0.001)^360 − 1 = 43.3071610 %`

### Cronología

| # | Fecha | Evento | Línea usada | Disponible |
|---|---|---|---|---|
| 1 | 26/09 | Kit importado US$ 49.90 × TC 3.520 = S/ 175.65, 4 cuotas (después del corte del 25/09 → ciclo de octubre) | 175.65 | 624.35 |
| 2 | 03/10 | Limpieza facial S/ 80.00, fin de mes | 255.65 | 544.35 |
| 3 | 25/10 | Labial S/ 35.00, fin de mes (el mismo día del corte: entra en este ciclo) | 290.65 | 509.35 |
| 4 | 25/10 | **Corte** → EC oct-2026, fecha de pago 05/11 | | |
| 5 | 03/11 | Paga EC oct-2026 antes de la fecha de pago: S/ 117.52 | 175.65 | 624.35 |
| 6 | 25/11 | **Corte** → EC nov-2026, fecha de pago 05/12 | | |
| 7 | 15/12 | Paga EC nov-2026 con 10 días de mora: S/ 49.13 | 131.94 | 668.06 |

### Kit importado: conversión, gracia y cronograma

- Conversión: `r2(49.90 × 3.520) = 175.65`
- Gracia total: 26/09 → 05/11 = **40 días**
- `TE40 = (1 + 0.025)^(40/30) − 1 = 3.3471459 %`
- `Capital capitalizado = r2(175.65 × 1.033471459) = 181.53`

| Cuota | Vence | Saldo inicial | Interés | Cuota | Amortización | Saldo final |
|---|---|---|---|---|---|---|
| 1 | 05/12/2026 | 181.53 | 4.54 | 48.25 | 43.71 | 137.82 |
| 2 | 05/01/2027 | 137.82 | 3.45 | 48.26 | 44.81 | 93.01 |
| 3 | 05/02/2027 | 93.01 | 2.33 | 48.26 | 45.93 | 47.08 |
| 4 | 05/03/2027 | 47.08 | 1.18 | 48.26 | 47.08 | 0.00 |

### EC oct-2026 (corte 25/10, pago 05/11)

| Fecha | Concepto | Capital | Días | Tasa | Interés | Total |
|---|---|---|---|---|---|---|
| 03/10 | Limpieza facial | 80.00 | 33 | TE33 = 1.025^(33/30) − 1 = 2.7534120 % | 2.20 | 82.20 |
| 25/10 | Labial | 35.00 | 11 | TE11 = 1.025^(11/30) − 1 = 0.9095069 % | 0.32 | 35.32 |
| | **Total a pagar** | **115.00** | | | **2.52** | **117.52** |

Informativo: kit importado, primera cuota S/ 48.25 el 05/12.

**Pago del 03/11 (anticipado):** S/ 117.52. Desglose: mora 0.00, interés 2.52, capital 115.00.
Libera S/ 115.00.

### EC nov-2026 (corte 25/11, pago 05/12)

| Concepto | Capital | Interés | Total |
|---|---|---|---|
| Kit importado, cuota 1/4 | 43.71 | 4.54 | 48.25 |
| **Total a pagar** | **43.71** | **4.54** | **48.25** |

**Pago del 15/12 (10 días de mora)**

| Concepto | Tasa | Monto |
|---|---|---|
| Exigible EC nov-2026 | | 48.25 |
| Interés compensatorio por mora | TE10 = 1.025^(10/30) − 1 = 0.8264838 % | 0.40 |
| Interés moratorio | TE10 = 1.001^10 − 1 = 1.0045120 % | 0.48 |
| **Total pagado** | | **49.13** |

Desglose: mora **0.48**, interés **4.94** (4.54 + 0.40), capital **43.71**. Libera S/ 43.71.
Entre el 06/12 y el 15/12 Ana no puede comprar (EC vencido).
