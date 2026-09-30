# Verificación contra el libro del curso

Martín Senmache, J. M. (2025). *Matemática Financiera* (5.ª ed.). Cada fila es un ejercicio
resuelto del libro, recalculado con el núcleo financiero del backend (`backend/app/finanzas`).
Los mismos casos se ejecutan como tests automáticos en `backend/tests/test_libro.py`.

- **Dinero**: se compara al céntimo (2 decimales).
- **Tasas**: el sistema redondea a 7 decimales en porcentaje (half-up). Si el libro imprime
  más decimales, coincide cuando ambas cifras son redondeos del mismo valor.

## Dinero

| Ejercicio | Qué se calcula | FiaMe | Libro | |
|---|---|---|---|---|
| 3-1 | Valor futuro, TNM 2 % c.d., 900 días | 91,087.73 | 91,087.73 | ✅ |
| 3-2 | Valor futuro, TNA 2.4 % c.m., 2 años | 136,385.65 | 136,385.65 | ✅ |
| 3-3 | Valor futuro, TNA 18.5 % c.d., 14/02/2010 → 13/09/2011 (576 días) | 4,033.10 | 4,033.10 | ✅ |
| 4-23 | Valor futuro, TNA 4 %, 90 días | 60,602.98 | 60,602.98 | ✅ |
| 4-24 | Valor futuro, TNT 1 % c.d., 180 días | 204,040.04 | 204,040.04 | ✅ |
| 5-36c | Mora 7 días: compensatorio TNA 20 % c.d. | 77.91 | 77.91 | ✅ |
| 5-36c | Mora 7 días: moratorio TEA 60 % | 183.62 | 183.62 | ✅ |
| 5-36c | Total a pagar con mora y costos | 20,331.53 | 20,331.53 | ✅ |
| 5-37e | Total a pagar con 6 días de mora (compensatorio + moratorio) | 59,740.32 | 59,740.32 | ✅ |
| 5-39c | Total a pagar con 3 días de mora (compensatorio + moratorio) | 15,016.47 | 15,016.47 | ✅ |
| 5-40c | Total a pagar con 6 días de mora (compensatorio + moratorio) | 142,991.24 | 142,991.24 | ✅ |
| 7-1 | Cuota, TEA 7.5 %, 36 mensuales | 1,046.31 | 1,046.31 | ✅ |
| 7-2 | Cuota, TEA 21.7 %, 9 cuatrimestrales | 439.16 | 439.16 | ✅ |
| 7-3 | Cuota, TEA 12 %, 16 trimestrales | 19,711.09 | 19,711.09 | ✅ |
| 7-5 | Cuota, TEA 19.9 %, 24 bimestrales | 492.61 | 492.61 | ✅ |
| 7-6 | Cuota, TNS 8.4 % c.d., 15 bimestrales | 2,715.63 | 2,715.63 | ✅ |
| 7-13a | Cuota, TEM 2.99 %, 36 mensuales | 205.77 | 205.77 | ✅ |
| 7-13b | Ídem con 6 meses de gracia total | 245.56 | 245.56 | ✅ |
| 7-14a | Cuota, TEA 8.5 %, 10 semestrales | 4,474.64 | 4,474.64 | ✅ |
| 7-14c | Ídem con 1 semestre de gracia | 5,080.93 | 5,080.93 | ✅ |
| 7-16a | Cuota, TEA 7.9 %, 48 mensuales | 1,124.67 | 1,124.67 | ✅ |
| 7-17a | Cuota, TEA 17 %, 12 mensuales | 350.69 | 350.69 | ✅ |
| 7-17b | Ídem con 3 meses de gracia total | 477.06 | 477.06 | ✅ |
| 8-1 | Cuota, TEA 10 %, 9 cuatrimestrales | 14,537.95 | 14,537.95 | ✅ |
| 8-3 | Cuota, TEA 9 %, 8 semestrales | 12,080.78 | 12,080.78 | ✅ |

## Tasas

| Ejercicio | Conversión | FiaMe (%) | Libro (%) | |
|---|---|---|---|---|
| 3-51 TEM | TNA 12 % c.m. → TEM | 1.0000000 | 1.000 | ✅ |
| 3-51 TET | TNA 12 % c.m. → TET | 3.0301000 | 3.0301 | ✅ |
| 3-51 TEA | TNA 12 % c.m. → TEA | 12.6825030 | 12.682503 | ✅ |
| 3-52a | TNA 18.75 % c.m. → TEA | 20.4482770 | 20.448277 | ✅ |
| 3-52b | TNA 16.98 % c.t. → TEA | 18.0921242 | 18.0921242 | ✅ |
| 3-52c | TNA 17.23 % c.s. → TEA | 17.9721823 | 17.9721822 | ✅ |
| 3-52d | TNA 20 % c.a. → TEA | 20.0000000 | 20.0 | ✅ |
| 4-9 | TNA 24 % c.q. → TEA | 26.9734649 | 26.97346485 | ✅ |
| 4-10 | TNA 28 % c.d. → TEM | 2.3598402 | 2.359840157 | ✅ |
| 4-11 | TNS 4 % (c.d.) → TEM | 0.6688193 | 0.66881927 | ✅ |
| 4-12 | TNC 3 % (c.d.) → TEM | 0.7527251 | 0.752725104 | ✅ |
| 4-13 | TEM 0.89 % → TEA | 11.2186104 | 11.21861036 | ✅ |
| 4-14 | TEA 12 % → TEM | 0.9488793 | 0.9488793 | ✅ |
| 4-15 | TEA 32 % → TEB | 4.7359208 | 4.7359208 | ✅ |
| 4-16 | TEM 0.99 % → TEA | 12.5486957 | 12.5486957 | ✅ |
| 4-17 | TEM 3.9 % → TES | 25.8036626 | 25.80366265 | ✅ |
| 4-21 | TEM 4.5 % → TEA | 69.5881433 | 69.5881433 | ✅ |
| 4-24 TES | TNT 1 % c.d. → TES | 2.0200207 | 2.02002 | ✅ |
| 4-3 | TEM 8 % → TNA c.m. | 96.0000000 | 96 | ✅ |
| 4-8 | TEA 12 % → TNT c.q. | 2.8399169 | 2.83991694 | ✅ |
| 4-19 | TEM 4.5 % → TNA c.q. | 53.4057960 | 53.40579602 | ✅ |
| 4-20 | TEM 8.1 % → TNS c.q. | 47.6537981 | 47.65379813 | ✅ |
| 4-22b | TET 3 % → TNA c.m. | 11.8819609 | 11.88196085 | ✅ |

## Diferencias con el libro

En seis tasas el libro difiere a partir del séptimo decimal. En todos los casos FiaMe
devuelve el valor **exacto** de la fórmula directa, calculado con 50 dígitos de precisión y
redondeado a 7 decimales (verificado en el test `test_diferencias_documentadas`).

| Ejercicio | FiaMe (%) | Libro (%) | Causa |
|---|---|---|---|
| 4-24 TEA | 4.0808461 | 4.080844807 | El libro calcula la TEA a partir de la TES ya redondeada (2.02002 %). FiaMe convierte en un solo paso, como exige la regla R12. |
| 4-23 TET | 1.0049606 | 1.004966666 | Errata del libro: la misma tasa (4 % anual c.d.) en el ej. 4-24 da el valor de FiaMe. |
| 4-23 TES | 2.0200207 | 2.02003298 | Errata del libro: el ej. 4-24 da 2.02002 % para la misma tasa, igual que FiaMe. |
| 4-22a | 12.7474307 | 12.74743055 | Redondeo intermedio del libro; diferencia de 1.4 × 10⁻⁷ puntos porcentuales. |
| 4-4 | 8.2293291 | 8.22932892 | Redondeo intermedio del libro; diferencia de 1.9 × 10⁻⁷ puntos porcentuales. |
| 4-7 | 1.7353656 | 1.73536554 | Redondeo intermedio del libro; diferencia de 6 × 10⁻⁸ puntos porcentuales. |

El ej. 3-52c (17.9721822 % en el libro) sí coincide: el valor exacto es 17.97218225 %, que con
redondeo half-up da 17.9721823 %. El libro lo muestra truncado.

Ninguna de estas diferencias afecta a los montos de dinero: todos los ejercicios de dinero
coinciden al céntimo.

