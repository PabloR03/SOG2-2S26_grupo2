"""
Segmentación de clientes - Paso 4 del enunciado
Curso: Sistemas Organizacionales y Gerenciales 2 - Práctica 1

Paso 4

  a. Agrupar a los clientes por edad y analizar sus patrones de compra.
  b. Comparar el comportamiento de compra entre géneros.
  c. Agrupar los clientes por boletín y vales y analizar sus patrones de compra.

Ejecutar:
    python src/analysis/segmentacion.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from eda import obtener_datos, ETIQUETAS, FIG_DIR, _guardar  # noqa: E402

RANGOS_EDAD = [0, 17, 25, 35, 45, 55, 65, 150]
ETIQUETAS_EDAD = ["<18 (menor)", "18-25", "26-35", "36-45", "46-55", "56-65", "66+"]

MET_PATRON = ["venta_total", "n_compras", "monto_compra", "tiempo"]


# --- a. Segmentación por edad ---
def segmentar_por_edad(df: pd.DataFrame):
    d = df.dropna(subset=["edad"]).copy()
    d["grupo_edad"] = pd.cut(d["edad"], bins=RANGOS_EDAD, labels=ETIQUETAS_EDAD, right=True)

    resumen = d.groupby("grupo_edad", observed=True)[MET_PATRON].mean().round(2)
    resumen["n_clientes"] = d.groupby("grupo_edad", observed=True).size()

    print("Patrones de compra por grupo de edad:")
    print(resumen.to_string())

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(resumen.index.astype(str), resumen["venta_total"], color="#4C72B0")
    ax.set_title("Venta total promedio por grupo de edad")
    ax.set_ylabel("Venta_total promedio (Q)")
    plt.xticks(rotation=20)
    _guardar(fig, "09_venta_promedio_por_edad.png")

    return resumen


# --- b. Comparación por género ---
def comparar_por_genero(df: pd.DataFrame):
    d = df.dropna(subset=["genero"]).copy()
    d["genero_label"] = d["genero"].map(ETIQUETAS["genero"])

    resumen = d.groupby("genero_label")[MET_PATRON].mean().round(2)
    resumen["n_clientes"] = d.groupby("genero_label").size()

    print("\nPatrones de compra por género:")
    print(resumen.to_string())

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].bar(resumen.index, resumen["venta_total"], color=["#DD8452", "#4C72B0"])
    axes[0].set_title("Venta total promedio")
    axes[1].bar(resumen.index, resumen["n_compras"], color=["#DD8452", "#4C72B0"])
    axes[1].set_title("N° de compras promedio")
    fig.suptitle("Comportamiento de compra por género")
    _guardar(fig, "10_comportamiento_por_genero.png")

    return resumen


# --- c. Segmentación por Boletín y Vale ---
def segmentar_por_boletin_vale(df: pd.DataFrame):
    d = df.dropna(subset=["boletin", "vale"]).copy()
    d["grupo"] = (
        "Boletín " + d["boletin"].map(ETIQUETAS["boletin"]) +
        " / Vale " + d["vale"].map(ETIQUETAS["vale"])
    )

    resumen = d.groupby("grupo")[MET_PATRON].mean().round(2)
    resumen["n_clientes"] = d.groupby("grupo").size()

    print("\nPatrones de compra por combinación Boletín/Vale:")
    print(resumen.to_string())

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(resumen.index, resumen["venta_total"], color="#55A868")
    ax.set_title("Venta total promedio por uso de Boletín/Vale")
    ax.set_ylabel("Venta_total promedio (Q)")
    plt.xticks(rotation=15)
    _guardar(fig, "11_venta_por_boletin_vale.png")

    return resumen


def main():
    print("Obteniendo datos desde la base de datos...")
    df = obtener_datos()
    print(f"{len(df)} filas obtenidas.\n")

    print("--- a. Segmentación por edad ---")
    segmentar_por_edad(df)

    print("\n--- b. Comparación por género ---")
    comparar_por_genero(df)

    print("\n--- c. Segmentación por Boletín/Vale ---")
    segmentar_por_boletin_vale(df)

    print("\nListo. Gráficos 09, 10 y 11 guardados en reports/figures/")


if __name__ == "__main__":
    main()