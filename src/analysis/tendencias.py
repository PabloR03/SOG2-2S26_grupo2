"""
Análisis de tendencias - Paso 3 del enunciado
Curso: Sistemas Organizacionales y Gerenciales 2 - Práctica 1

Punto3

    a. Determinar los meses con mayores y menores ventas.
    b. Identificar el navegador más preferido y el menos popular.
    c. Identificar total de ventas pagadas contra entrega o con pago en efectivo.
    d. Identificar los meses donde se usaron más boletines y vales.

SUPUESTO DE NEGOCIO (punto c): el catálogo de MetodoPago no distingue "contra
entrega" de "efectivo" -> se asume que ambos corresponden al código 0 (Efectivo),
ya que son pagos en persona al recibir/comprar el producto.

Ejecutar:
    python src/analysis/tendencias.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from eda import obtener_datos, ETIQUETAS, MESES_ES, FIG_DIR, _guardar  # noqa: E402


# --- a. Meses con mayores y menores ventas ---
def meses_mayor_menor_venta(df: pd.DataFrame):
    ventas_mes = (
        df.dropna(subset=["fecha_compra"])
        .groupby(df["fecha_compra"].dt.month)["monto_compra"]
        .sum()
        .reindex(range(1, 13), fill_value=0)
    )
    mes_max = ventas_mes.idxmax()
    mes_min = ventas_mes.idxmin()
    print(f"Mes con MAYORES ventas: {MESES_ES[mes_max-1]} (Q{ventas_mes[mes_max]:,.2f})")
    print(f"Mes con MENORES ventas: {MESES_ES[mes_min-1]} (Q{ventas_mes[mes_min]:,.2f})")
    return ventas_mes


# --- b. Navegador más preferido y menos popular ---
def navegador_preferido(df: pd.DataFrame):
    conteo = df["navegador"].dropna().map(ETIQUETAS["navegador"]).value_counts()
    faltantes = df["navegador"].isna().sum()
    print(f"\nNavegador MÁS preferido: {conteo.idxmax()} ({conteo.max()} clientes)")
    print(f"Navegador MENOS popular: {conteo.idxmin()} ({conteo.min()} clientes)")
    print(f"(sin dato: {faltantes} registros, excluidos del conteo)")

    colores = ["#C44E52" if v == conteo.max() or v == conteo.min() else "#8C8C8C"
               for v in conteo.values]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(conteo.index.astype(str), conteo.values, color=colores)
    ax.set_title("Preferencia de navegador (rojo = más y menos popular)")
    ax.set_ylabel("Cantidad de clientes")
    plt.xticks(rotation=20)
    _guardar(fig, "06_navegador_top_bottom.png")
    return conteo


# --- c. Ventas pagadas contra entrega / efectivo ---
def ventas_efectivo(df: pd.DataFrame):
    en_efectivo = df[df["metodo_pago"] == 0]
    total_monto = en_efectivo["monto_compra"].sum()
    total_ventas = en_efectivo["venta_total"].sum()
    n = len(en_efectivo)
    pct = n / df["metodo_pago"].notna().sum() * 100
    print(f"\nVentas pagadas en efectivo / contra entrega (MetodoPago=0):")
    print(f"  Cantidad de transacciones: {n} ({pct:.1f}% de las que sí reportan método)")
    print(f"  Suma de Monto_Compra: Q{total_monto:,.2f}")
    print(f"  Suma de Venta_total:  Q{total_ventas:,.2f}")
    return {
        "n": n,
        "pct": pct,
        "monto_compra_total": total_monto,
        "venta_total_total": total_ventas,
    }


# --- d. Meses con más uso de boletín y vale ---
def boletin_vale_por_mes(df: pd.DataFrame):
    d = df.dropna(subset=["fecha_compra"]).copy()
    d["mes"] = d["fecha_compra"].dt.month
    boletin_mes = d[d["boletin"] == 1].groupby("mes").size().reindex(range(1, 13), fill_value=0)
    vale_mes = d[d["vale"] == 1].groupby("mes").size().reindex(range(1, 13), fill_value=0)

    mes_top_boletin = boletin_mes.idxmax()
    mes_top_vale = vale_mes.idxmax()
    print(f"\nMes con más uso de Boletín: {MESES_ES[mes_top_boletin-1]} ({boletin_mes.max()} usos)")
    print(f"Mes con más uso de Vale:    {MESES_ES[mes_top_vale-1]} ({vale_mes.max()} usos)")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(MESES_ES, boletin_mes.values, marker="o", label="Boletín")
    ax.plot(MESES_ES, vale_mes.values, marker="s", label="Vale")
    ax.set_title("Uso de Boletín y Vale por mes")
    ax.set_ylabel("Cantidad de clientes que lo usaron")
    ax.legend()
    _guardar(fig, "07_boletin_vale_por_mes.png")
    return boletin_mes, vale_mes


def generar_tabla_resumen(ventas_mes, conteo_navegadores, faltantes_navegador,
                          resumen_efectivo, boletin_mes, vale_mes):
    """Genera una imagen con todas las respuestas principales del análisis."""
    mes_mayor = ventas_mes.idxmax()
    mes_menor = ventas_mes.idxmin()
    navegador_mayor = conteo_navegadores.idxmax()
    navegador_menor = conteo_navegadores.idxmin()
    mes_boletin = boletin_mes.idxmax()
    mes_vale = vale_mes.idxmax()

    filas = [
        ["a", "Mes con mayores ventas", MESES_ES[mes_mayor - 1],
         f"Q{ventas_mes[mes_mayor]:,.2f}"],
        ["a", "Mes con menores ventas", MESES_ES[mes_menor - 1],
         f"Q{ventas_mes[mes_menor]:,.2f}"],
        ["b", "Navegador mas preferido", navegador_mayor,
         f"{conteo_navegadores.max()} clientes"],
        ["b", "Navegador menos popular", navegador_menor,
         f"{conteo_navegadores.min()} clientes"],
        ["b", "Registros sin navegador", "Sin dato",
         str(faltantes_navegador)],
        ["c", "Transacciones en efectivo / contra entrega", "MetodoPago = 0",
         f"{resumen_efectivo['n']} ({resumen_efectivo['pct']:.1f}%)"],
        ["c", "Monto total de compra en efectivo", "MetodoPago = 0",
         f"Q{resumen_efectivo['monto_compra_total']:,.2f}"],
        ["c", "Venta total en efectivo", "MetodoPago = 0",
         f"Q{resumen_efectivo['venta_total_total']:,.2f}"],
        ["d", "Mes con mas uso de Boletin", MESES_ES[mes_boletin - 1],
         f"{boletin_mes.max()} usos"],
        ["d", "Mes con mas uso de Vale", MESES_ES[mes_vale - 1],
         f"{vale_mes.max()} usos"],
    ]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.axis("off")
    ax.set_title("Resumen de tendencias de ventas", fontsize=16, fontweight="bold", pad=18)
    tabla = ax.table(
        cellText=filas,
        colLabels=["Punto", "Pregunta", "Resultado", "Valor"],
        colWidths=[0.08, 0.42, 0.25, 0.25],
        cellLoc="left",
        loc="center",
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(10)
    tabla.scale(1, 1.8)

    for (fila, columna), celda in tabla.get_celld().items():
        celda.set_edgecolor("#D9E2F3")
        if fila == 0:
            celda.set_facecolor("#2F5597")
            celda.set_text_props(color="white", weight="bold")
        elif fila % 2 == 0:
            celda.set_facecolor("#F3F6FA")

    _guardar(fig, "08_resumen_tendencias.png")


def main():
    print("Obteniendo datos desde la base de datos...")
    df = obtener_datos()
    print(f"{len(df)} filas obtenidas.\n")

    print("--- a. Meses con mayores/menores ventas ---")
    ventas_mes = meses_mayor_menor_venta(df)

    print("\n--- b. Navegador más y menos popular ---")
    conteo_navegadores = navegador_preferido(df)
    faltantes_navegador = int(df["navegador"].isna().sum())

    print("\n--- c. Ventas en efectivo / contra entrega ---")
    resumen_efectivo = ventas_efectivo(df)

    print("\n--- d. Meses con más uso de Boletín y Vale ---")
    boletin_mes, vale_mes = boletin_vale_por_mes(df)

    generar_tabla_resumen(
        ventas_mes,
        conteo_navegadores,
        faltantes_navegador,
        resumen_efectivo,
        boletin_mes,
        vale_mes,
    )

    print("\nListo. Gráficos y tabla resumen guardados en reports/figures/")


if __name__ == "__main__":
    main()