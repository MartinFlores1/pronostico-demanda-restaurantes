"""
Genera dos años de ventas diarias ficticias para 4 sedes de restaurante.

La demanda se construye con patrones que se ven en la operación real:
- fines de semana más fuertes que los días de semana
- temporada alta en verano (enero a marzo) y en julio
- feriados peruanos con picos (Fiestas Patrias, Navidad, Día de la Madre...)
- días de promoción que suben las ventas
- una tendencia leve de crecimiento y ruido aleatorio

Salida: data/ventas_diarias.csv  (fecha, sede, tickets, venta_soles, promo, feriado)
Todos los datos son inventados.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2026
rng = np.random.default_rng(SEMILLA)
CARPETA = Path(__file__).parent / "data"

SEDES = {  # tickets base por día y ticket promedio en soles
    "Sede Centro": (180, 38.0),
    "Sede Norte": (140, 34.5),
    "Sede Sur": (120, 36.0),
    "Sede Playa": (90, 42.0),
}
FACTOR_DIA = {0: 0.80, 1: 0.82, 2: 0.88, 3: 0.95, 4: 1.20, 5: 1.40, 6: 1.30}
FACTOR_MES = {1: 1.15, 2: 1.18, 3: 1.08, 4: 0.95, 5: 0.97, 6: 0.93,
              7: 1.10, 8: 0.95, 9: 0.94, 10: 0.97, 11: 1.00, 12: 1.12}


def feriados(anios: list[int]) -> dict[pd.Timestamp, float]:
    """Feriados y fechas comerciales con su efecto sobre la demanda."""
    efecto = {}
    for a in anios:
        for mes, dia, f in [(1, 1, 0.70), (5, 1, 1.15), (6, 29, 1.20), (7, 28, 1.35), (7, 29, 1.30),
                            (8, 30, 1.15), (10, 8, 1.15), (11, 1, 1.15), (12, 8, 1.15),
                            (12, 24, 1.25), (12, 25, 0.75), (12, 31, 1.20)]:
            efecto[pd.Timestamp(a, mes, dia)] = f
        # Día de la Madre: segundo domingo de mayo / Día del Padre: tercer domingo de junio
        mayo = pd.date_range(f"{a}-05-01", f"{a}-05-31", freq="W-SUN")
        junio = pd.date_range(f"{a}-06-01", f"{a}-06-30", freq="W-SUN")
        efecto[mayo[1]] = 1.60
        efecto[junio[2]] = 1.35
    return efecto


def main() -> None:
    CARPETA.mkdir(exist_ok=True)
    fechas = pd.date_range("2024-10-01", "2026-09-30", freq="D")
    efecto_feriado = feriados([2024, 2025, 2026])

    filas = []
    for sede, (base, ticket_prom) in SEDES.items():
        es_playa = sede == "Sede Playa"
        for i, fecha in enumerate(fechas):
            factor_mes = FACTOR_MES[fecha.month]
            if es_playa:  # la sede de playa depende mucho más del verano
                factor_mes = factor_mes ** 2.5
            tendencia = 1 + 0.10 * i / len(fechas)
            feriado = efecto_feriado.get(fecha, 1.0)
            promo = rng.random() < 0.07
            esperado = (base * FACTOR_DIA[fecha.day_of_week] * factor_mes * tendencia
                        * feriado * (1.22 if promo else 1.0))
            tickets = max(0, int(rng.normal(esperado, esperado * 0.08)))
            venta = round(tickets * ticket_prom * rng.normal(1, 0.04), 2)
            filas.append({"fecha": fecha.date(), "sede": sede, "tickets": tickets,
                          "venta_soles": venta, "promo": int(promo), "feriado": int(feriado != 1.0)})

    df = pd.DataFrame(filas)
    df.to_csv(CARPETA / "ventas_diarias.csv", index=False)
    print(f"{len(df)} filas | {df['fecha'].min()} a {df['fecha'].max()} | {df['sede'].nunique()} sedes")


if __name__ == "__main__":
    main()
