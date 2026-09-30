# 7. Algoritmo

El algoritmo de solución se presenta mediante diagramas de flujo. Cada diagrama describe un
proceso con sus variables, decisiones y ciclos, siguiendo las reglas de
[especificacion-financiera.md](../especificacion-financiera.md).

## 7.1 Notación

| Símbolo | Significado |
|---|---|
| Óvalo | Inicio o fin |
| Paralelogramo | Entrada o salida de datos |
| Rectángulo | Proceso o asignación (`←`) |
| Rombo | Decisión |
| Rectángulo con doble borde | Llamada a otro algoritmo |

- `r2(x)`: redondeo a 2 decimales, half-up (montos de dinero).
- `r7(x)`: redondeo a 7 decimales en porcentaje (tasas).
- Días: diferencia en días calendario exactos entre dos fechas. Año de 360 días.

## 7.2 Conversión de tasas: `TasaEfectiva(tasa, n)`

Convierte cualquier tasa pactada, nominal o efectiva, en la tasa efectiva para `n` días, en
un solo paso.

```mermaid
flowchart TD
    A(["Inicio: TasaEfectiva(tasa, n)"]) --> D{"¿tipo = EFECTIVA?"}
    D -->|Sí| E["p ← días del periodo de la tasa<br/>TE ← (1 + valor/100)^(n/p) − 1"]
    D -->|No| F["p ← días del periodo de la tasa<br/>c ← días del periodo de capitalización<br/>m ← p / c<br/>TE ← (1 + valor/100/m)^(n/c) − 1"]
    E --> H[/"TE ← r7(TE)<br/>Devolver TE"/]
    F --> H
    H --> J(["Fin"])
```

## 7.3 Ciclo de la compra: `CalcularCiclo`

Determina en qué fecha de corte cae una compra y cuál es su fecha de pago.

```mermaid
flowchart TD
    A(["Inicio: CalcularCiclo(fecha_compra, dia_corte, dia_pago)"]) --> C["corte ← día dia_corte del mes de la compra"]
    C --> D{"¿fecha_compra ≤ corte?"}
    D -->|Sí| F1["pago ← día dia_pago del mes de corte"]
    D -->|No| F2["corte ← corte + 1 mes<br/>pago ← día dia_pago del mes de corte"]
    F1 --> G{"¿pago > corte?"}
    F2 --> G
    G -->|No| H["pago ← pago + 1 mes"]
    G -->|Sí| I[/"Devolver corte y pago"/]
    H --> I
    I --> J(["Fin"])
```

## 7.4 Registro de una venta: `RegistrarVenta`

```mermaid
flowchart TD
    A(["Inicio: RegistrarVenta(cliente, productos,<br/>modalidad, n_cuotas, TC)"]) --> E[["subtotal ← r2(cantidad × precio_lista × TC) por producto<br/>capital ← Σ subtotal<br/>disponible ← límite − crédito usado<br/>corte, pago ← CalcularCiclo(fecha_compra, dia_corte, dia_pago)"]]
    E --> C{"¿Cliente activo y sin<br/>bloqueo por EC vencido?"}
    C -->|No| X[/"Rechazar venta"/]
    C -->|Sí| G{"¿capital ≤ disponible?"}
    G -->|No| X
    G -->|Sí| I{"¿modalidad?"}
    I -->|FIN_DE_MES| J{"¿Productos permiten<br/>pago único?"}
    I -->|CUOTAS| N{"¿Productos permiten cuotas<br/>y 1 ≤ n_cuotas ≤ máximo?"}
    J -->|No| X
    N -->|No| X
    J -->|Sí| K[["días ← pago − fecha_compra<br/>TE ← TasaEfectiva(tasa comp., días)<br/>interés ← r2(capital × TE)<br/>total ← capital + interés"]]
    N -->|Sí| O[["GenerarCronograma(capital, fecha_compra,<br/>corte, pago, n_cuotas)"]]
    K --> P[/"Guardar venta con tasas vigentes,<br/>detalle, cuotas y auditoría"/]
    O --> P
    P --> Z(["Fin"])
    X --> Z
```

## 7.5 Cronograma de cuotas: `GenerarCronograma`

Método francés vencido ordinario, con periodo de gracia total capitalizado y cuota calculada
cada periodo sobre el saldo inicial (Fórmula 67 del libro del profesor).

```mermaid
flowchart TD
    A(["Inicio: GenerarCronograma(capital, fecha_compra, corte, pago, n)"]) --> B[["días_gracia ← pago − fecha_compra<br/>TEg ← TasaEfectiva(tasa comp., días_gracia)<br/>SI ← r2(capital × (1 + TEg))<br/>TEM ← TasaEfectiva(tasa comp., 30)<br/>liberado ← 0, k ← 1"]]
    B --> G{"¿k ≤ n?"}
    G -->|No| Z(["Fin"])
    G -->|Sí| H{"¿k = n?"}
    H -->|No| L["I ← r2(SI × TEM)<br/>f ← (1 + TEM)^(n − k + 1)<br/>R ← r2(SI × TEM × f / (f − 1))"]
    H -->|Sí| K["I ← r2(SI × TEM)<br/>R ← SI + I"]
    L --> M["A ← R − I, SF ← SI − A<br/>libera ← mín(A, capital − liberado)<br/>liberado ← liberado + libera<br/>corte_k ← corte + k meses<br/>vencimiento_k ← pago + k meses"]
    K --> M
    M --> P[/"Guardar cuota k<br/>SI ← SF, k ← k + 1"/]
    P --> G
```

## 7.6 Generación del estado de cuenta: `GenerarCorte`

Se ejecuta automáticamente todos los días al cierre (23:59:59).

```mermaid
flowchart TD
    A(["Inicio: GenerarCorte<br/>hoy ← fecha actual"]) --> C{"¿Queda algún cliente activo<br/>con dia_corte = día de hoy?"}
    C -->|No| Z(["Fin"])
    C -->|Sí| E{"¿El siguiente cliente ya<br/>tiene EC con corte = hoy?"}
    E -->|Sí| C
    E -->|No| F["pago ← primera fecha con dia_pago posterior a hoy<br/>ventas ← ventas FIN_DE_MES vigentes con corte = hoy<br/>cuotas ← cuotas pendientes con corte = hoy"]
    F --> I["total_capital ← Σ capital ventas + Σ amortización cuotas<br/>total_interés ← Σ interés ventas + Σ interés cuotas<br/>total ← total_capital + total_interés<br/>foto de la línea y tasas vigentes del cliente"]
    I --> K{"¿total = 0?"}
    K -->|Sí| L["estado ← PAGADO"]
    K -->|No| M["estado ← PENDIENTE"]
    L --> N[/"Guardar EC y auditoría"/]
    M --> N
    N --> C
```

## 7.7 Registro de un pago: `RegistrarPago`

Los estados de cuenta se pagan completos y en orden, del más antiguo al más reciente. Los
intereses por mora se calculan con los días reales de atraso y se desglosan según el orden
de imputación del Anexo A.

```mermaid
flowchart TD
    A(["Inicio: RegistrarPago(cliente, fecha_pago, medio, k)"]) --> C["pendientes ← EC PENDIENTE del cliente,<br/>del más antiguo al más reciente<br/>totales ← 0, i ← 1"]
    C --> D{"¿1 ≤ k ≤ cantidad<br/>de pendientes?"}
    D -->|No| X[/"Rechazar pago"/]
    D -->|Sí| F{"¿i ≤ k?"}
    F -->|No| Q[/"Guardar pago con totales,<br/>detalle y auditoría"/]
    F -->|Sí| G["EC ← pendientes[i]<br/>exigible ← total a pagar del EC<br/>días_mora ← máx(0, fecha_pago − fecha de pago del EC)"]
    G --> H{"¿días_mora > 0?"}
    H -->|No| I["Icm ← 0, Im ← 0"]
    H -->|Sí| K[["Icm ← r2(exigible × TasaEfectiva(tasa comp. del EC, días_mora))<br/>Im ← r2(exigible × TasaEfectiva(tasa mor. del EC, días_mora))"]]
    I --> L["mora ← Im, capital ← capital del EC<br/>interés ← interés del EC + Icm<br/>total ← mora + interés + capital<br/>libera ← Σ capital ventas FIN_DE_MES + Σ libera cuotas<br/>EC ← PAGADO, sus ventas y cuotas ← PAGADA<br/>sumar a totales, i ← i + 1"]
    K --> L
    L --> F
    Q --> Z(["Fin"])
    X --> Z
```
