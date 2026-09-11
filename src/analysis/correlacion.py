"""
Análisis de correlación - Paso 5 del enunciado
Curso: Sistemas Organizacionales y Gerenciales 2 - Práctica 1

PASO 5

  a. Investigar si existe una relación entre el total de la venta y la edad del cliente.
  b. Examinar si hay una correlación entre el género del cliente y el método de pago preferido.
  c. Investigar si existe una correlación entre los clientes que utilizan boletines y vales.

Notas metodológicas:
  - Para dos variables NUMÉRICAS (a) se usa el coeficiente de correlación de Pearson.
  - Para dos variables CATEGÓRICAS (b, c) el coeficiente de Pearson no aplica bien;
    se usa la prueba Chi-cuadrado de independencia + Cramér's V como medida de
    fuerza de asociación (0 = sin relación, 1 = relación perfecta).

Ejecutar:
    python src/analysis/correlacion.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, chi2_contingency

sys.path.insert(0, os.path.dirname(__file__))
from eda import obtener_datos, ETIQUETAS, FIG_DIR, _guardar  # noqa: E402


def _interpretar_r(r: float) -> str:
    r_abs = abs(r)
    if r_abs < 0.1:
        return "prácticamente nula"
    if r_abs < 0.3:
        return "débil"
    if r_abs < 0.5:
        return "moderada"
    return "fuerte"


def cramers_v(tabla: pd.DataFrame):
    chi2, p, dof, _ = chi2_contingency(tabla)
    n = tabla.values.sum()
    r, k = tabla.shape
    v = np.sqrt((chi2 / n) / (min(r - 1, k - 1)))
    return float(v), chi2, p


# --- a. Venta_total vs Edad (numérica vs numérica) ---
def correlacion_venta_edad(df: pd.DataFrame):
    d = df.dropna(subset=["edad", "venta_total"])
    r, p_valor = pearsonr(d["edad"], d["venta_total"])
    print(f"Correlación de Pearson (Edad vs Venta_total): r = {r:.3f}  (p-valor = {p_valor:.4f})")
    print(f"Interpretación: relación {_interpretar_r(r)} "
          f"({'estadísticamente significativa' if p_valor < 0.05 else 'NO significativa'} al 95%)")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(d["edad"], d["venta_total"], alpha=0.3, s=15, color="#4C72B0")
    m, b = np.polyfit(d["edad"], d["venta_total"], 1)
    xs = np.linspace(d["edad"].min(), d["edad"].max(), 100)
    ax.plot(xs, m * xs + b, color="#C44E52", linewidth=2, label=f"tendencia (r={r:.2f})")
    ax.set_xlabel("Edad")
    ax.set_ylabel("Venta_total")
    ax.set_title("Relación entre Edad y Venta_total")
    ax.legend()
    _guardar(fig, "12_correlacion_edad_venta.png")
    return r, p_valor


# --- b. Género vs Método de pago (categórica vs categórica) ---
def correlacion_genero_pago(df: pd.DataFrame):
    d = df.dropna(subset=["genero", "metodo_pago"]).copy()
    d["genero_label"] = d["genero"].map(ETIQUETAS["genero"])
    d["metodo_label"] = d["metodo_pago"].map(ETIQUETAS["metodo_pago"])

    tabla = pd.crosstab(d["genero_label"], d["metodo_label"])
    v, chi2, p_valor = cramers_v(tabla)
    print("\nTabla de contingencia (Género x Método de pago):")
    print(tabla.to_string())
    print(f"\nChi-cuadrado = {chi2:.3f}  |  p-valor = {p_valor:.4f}  |  Cramér's V = {v:.3f}")
    print(f"Interpretación: asociación {_interpretar_r(v)} "
          f"({'estadísticamente significativa' if p_valor < 0.05 else 'NO significativa'} al 95%)")

    tabla_pct = tabla.div(tabla.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 5))
    tabla_pct.plot(kind="bar", ax=ax, color=["#DD8452", "#4C72B0", "#55A868"])
    ax.set_ylabel("% dentro de cada género")
    ax.set_title("Método de pago preferido por género")
    plt.xticks(rotation=0)
    _guardar(fig, "13_genero_vs_metodopago.png")
    return tabla, v, p_valor


# --- c. Boletín vs Vale (binaria vs binaria) ---
def correlacion_boletin_vale(df: pd.DataFrame):
    d = df.dropna(subset=["boletin", "vale"]).copy()
    tabla = pd.crosstab(d["boletin"].map(ETIQUETAS["boletin"]), d["vale"].map(ETIQUETAS["vale"]))
    v, chi2, p_valor = cramers_v(tabla)
    r_pearson = d["boletin"].corr(d["vale"])  # equivalente al coef. phi en tablas 2x2

    print("\nTabla de contingencia (Boletín x Vale):")
    print(tabla.to_string())
    print(f"\nChi-cuadrado = {chi2:.3f}  |  p-valor = {p_valor:.4f}")
    print(f"Coeficiente phi (=Pearson en binarias) = {r_pearson:.3f}  |  Cramér's V = {v:.3f}")
    print(f"Interpretación: asociación {_interpretar_r(r_pearson)} "
          f"({'estadísticamente significativa' if p_valor < 0.05 else 'NO significativa'} al 95%)")

    fig, ax = plt.subplots(figsize=(6, 5))
    tabla.plot(kind="bar", ax=ax, color=["#DD8452", "#4C72B0"])
    ax.set_ylabel("Cantidad de clientes")
    ax.set_title("Uso de Vale según uso de Boletín")
    plt.xticks(rotation=0)
    _guardar(fig, "14_boletin_vs_vale.png")
    return tabla, r_pearson, p_valor


def main():
    print("Obteniendo datos desde la base de datos...")
    df = obtener_datos()
    print(f"{len(df)} filas obtenidas.\n")

    print("--- a. Venta_total vs Edad ---")
    correlacion_venta_edad(df)

    print("\n--- b. Género vs Método de pago ---")
    correlacion_genero_pago(df)

    print("\n--- c. Boletín vs Vale ---")
    correlacion_boletin_vale(df)

    print("\nListo. Gráficos 12, 13 y 14 guardados en reports/figures/")


if __name__ == "__main__":
    main()