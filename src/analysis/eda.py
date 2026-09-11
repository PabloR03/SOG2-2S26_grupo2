"""
Análisis exploratorio - Paso 2 del enunciado
Curso: Sistemas Organizacionales y Gerenciales 2 - Práctica 1

Punto2

    a. Obtener los datos de la base de datos.
    b. Calcular estadísticas básicas (media, mediana, moda) para las variables numéricas.
    c. Crear visualizaciones para mostrar la distribución de ventas por mes,
        método de pago, navegador, Boletín y Vale.

Ejecutar:
    python src/analysis/eda.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")  # no requiere pantalla, guarda directo a archivo
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
from db import get_engine  # noqa: E402

FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "figures")

# Etiquetas legibles para las columnas categóricas (para que los gráficos
# se entiendan sin tener que memorizar los códigos numéricos)
ETIQUETAS = {
    "genero": {0: "Masculino", 1: "Femenino"},
    "metodo_pago": {0: "Efectivo", 1: "Tarjeta Crédito", 2: "Tarjeta Débito"},
    "navegador": {0: "Tienda Física", 1: "Navegador 1", 2: "Navegador 2",
                  3: "Navegador 3", 4: "Navegador 4"},
    "boletin": {0: "No", 1: "Sí"},
    "vale": {0: "No", 1: "Sí"},
}

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# --- a. Obtener los datos de la base de datos ---
def obtener_datos() -> pd.DataFrame:
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM ventas", engine, parse_dates=["fecha_compra"])
    return df


# --- b. Estadísticas básicas (media, mediana, moda) ---
def calcular_estadisticas(df: pd.DataFrame) -> pd.DataFrame:
    columnas_numericas = ["edad", "venta_total", "n_compras", "monto_compra", "tiempo"]
    filas = []
    for col in columnas_numericas:
        serie = df[col].dropna()
        moda = serie.mode()
        filas.append({
            "variable": col,
            "media": round(serie.mean(), 2),
            "mediana": round(serie.median(), 2),
            "moda": round(moda.iloc[0], 2) if not moda.empty else None,
            "desv_estandar": round(serie.std(), 2),
            "n_validos": int(serie.count()),
        })
    return pd.DataFrame(filas)


# --- c. Visualizaciones de distribución ---
def _guardar(fig, nombre):
    os.makedirs(FIG_DIR, exist_ok=True)
    ruta = os.path.join(FIG_DIR, nombre)
    fig.savefig(ruta, bbox_inches="tight", dpi=120)
    plt.close(fig)
    print(f"  guardado: {ruta}")


def grafico_ventas_por_mes(df: pd.DataFrame):
    ventas_mes = (
        df.dropna(subset=["fecha_compra"])
        .groupby(df["fecha_compra"].dt.month)["monto_compra"]
        .sum()
        .reindex(range(1, 13), fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(MESES_ES, ventas_mes.values, color="#4C72B0")
    ax.set_title("Distribución de ventas por mes (2025)")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Monto total de compra")
    _guardar(fig, "01_ventas_por_mes.png")


def grafico_categorica(df: pd.DataFrame, columna: str, titulo: str, archivo: str):
    conteo = df[columna].map(ETIQUETAS.get(columna, {})).value_counts(dropna=True)
    faltantes = df[columna].isna().sum()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(conteo.index.astype(str), conteo.values, color="#55A868")
    ax.set_title(f"{titulo}\n(sin dato: {faltantes} registros, excluidos)")
    ax.set_ylabel("Cantidad de clientes")
    plt.xticks(rotation=20)
    _guardar(fig, archivo)


def generar_visualizaciones(df: pd.DataFrame):
    print("Generando gráficos de distribución...")
    grafico_ventas_por_mes(df)
    grafico_categorica(df, "metodo_pago", "Distribución por método de pago", "02_metodo_pago.png")
    grafico_categorica(df, "navegador", "Distribución por navegador", "03_navegador.png")
    grafico_categorica(df, "boletin", "Distribución por uso de Boletín", "04_boletin.png")
    grafico_categorica(df, "vale", "Distribución por uso de Vale", "05_vale.png")


def main():
    print("Obteniendo datos desde la base de datos...")
    df = obtener_datos()
    print(f"{len(df)} filas obtenidas.\n")

    print("--- Estadísticas básicas ---")
    stats = calcular_estadisticas(df)
    print(stats.to_string(index=False))

    os.makedirs(FIG_DIR, exist_ok=True)
    stats.to_csv(os.path.join(FIG_DIR, "..", "estadisticas_basicas.csv"), index=False)

    print()
    generar_visualizaciones(df)
    print("\nListo.")


if __name__ == "__main__":
    main()