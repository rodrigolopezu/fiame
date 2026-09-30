"""Casos de prueba de docs/casos-de-prueba.md. Ejecutar: python3 referencia/casos.py"""
from datetime import date as d
from decimal import Decimal as D

from calculadora import Tasa, cronograma_frances, dias, interes, mora, pct, r2


def fin_de_mes(nombre, capital, fecha, fecha_pago, tasa):
    n = dias(fecha, fecha_pago)
    i = interes(capital, tasa, n)
    print(f"  {fecha:%d/%m} {nombre:<22} capital {capital:>8}  días {n:>3}  "
          f"TE{n}d {pct(tasa.efectiva(n))}  interés {i:>6}  total {capital + i:>8}")
    return capital, i


def cuotas(nombre, capital, fecha, fin_gracia, tasa, n):
    g = dias(fecha, fin_gracia)
    cap = r2(capital * (1 + tasa.efectiva(g)))
    print(f"  {nombre}: capital {capital}, gracia {fecha:%d/%m}->{fin_gracia:%d/%m} = {g} días, "
          f"TE{g}d {pct(tasa.efectiva(g))}, capitalizado {cap}")
    tem, filas = cronograma_frances(cap, tasa, n)
    print(f"  TEM {pct(tem)}")
    for f in filas:
        print(f"    {f['nc']}  SI {f['si']:>8}  int {f['interes']:>6}  cuota {f['cuota']:>7}  "
              f"amort {f['amort']:>7}  SF {f['sf']:>8}")
    return filas


def pago_con_mora(exigible, venc, fecha, comp, morat):
    n = dias(venc, fecha)
    ic, im = mora(exigible, comp, morat, n)
    print(f"  pago {fecha:%d/%m}: {n} días de mora  TE{n}d comp {pct(comp.efectiva(n))} "
          f"-> {ic}  TE{n}d mora {pct(morat.efectiva(n))} -> {im}  total {exigible + ic + im}")
    return ic, im


print("=== CASO 1: Bodega, tasa efectiva ===")
comp = Tasa("efectiva", "anual", D("24"))
morat = Tasa("efectiva", "anual", D("36"))
print(f"TEA comp {pct(comp.tea())}  TEA mora {pct(morat.tea())}")
print("EC set-2026 (corte 20/09, pago 26/09)")
fin_de_mes("Arroz 5 kg", D("22.00"), d(2026, 9, 10), d(2026, 9, 26), comp)
print("Licuadora en 3 cuotas")
c1 = cuotas("Licuadora", D("165.00"), d(2026, 9, 15), d(2026, 9, 26), comp, 3)
pago_con_mora(D("22.21"), d(2026, 9, 26), d(2026, 9, 30), comp, morat)
print("EC oct-2026 (corte 20/10, pago 26/10)")
fin_de_mes("Arroz 5 kg", D("22.00"), d(2026, 9, 22), d(2026, 10, 26), comp)
fin_de_mes("Aceite 1 L", D("9.50"), d(2026, 10, 18), d(2026, 10, 26), comp)

print("\n=== CASO 2: Tienda de belleza, tasa nominal y dólares ===")
comp = Tasa("nominal", "anual", D("30"), "mensual")
morat = Tasa("nominal", "anual", D("36"), "diaria")
print(f"TEA comp {pct(comp.tea())}  TEA mora {pct(morat.tea())}")
tc = D("3.520")
kit = r2(D("49.90") * tc)
print(f"Kit importado US$ 49.90 x TC {tc} = S/ {kit}")
c2 = cuotas("Kit importado", kit, d(2026, 9, 26), d(2026, 11, 5), comp, 4)
print("EC oct-2026 (corte 25/10, pago 05/11)")
fin_de_mes("Limpieza facial", D("80.00"), d(2026, 10, 3), d(2026, 11, 5), comp)
fin_de_mes("Labial", D("35.00"), d(2026, 10, 25), d(2026, 11, 5), comp)
print("EC nov-2026 (corte 25/11, pago 05/12): cuota 1")
pago_con_mora(c2[0]["cuota"], d(2026, 12, 5), d(2026, 12, 15), comp, morat)
