"""
MCP Server - expone las funciones de análisis (Pasos 2 al 6 del enunciado)
como herramientas ("tools") que el agente conversacional puede invocar.

Ejecutar (normalmente lo invoca el agente automáticamente, no manualmente):
    python3 src/agent/mcp_server.py
"""

import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))

from mcp.server.fastmcp import FastMCP  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import eda            # src/analysis/eda.py
import tendencias      # src/analysis/tendencias.py
import segmentacion    # src/analysis/segmentacion.py
import correlacion     # src/analysis/correlacion.py

mcp = FastMCP("sog2-analista-ventas")


@contextlib.contextmanager
def _silenciar_stdout():
    """Las funciones de análisis usan print() para uso por línea de comandos.
    Con el transporte stdio de MCP, stdout se usa para el protocolo JSON-RPC,
    así que cualquier print() lo corrompe. Se silencia aquí temporalmente."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        yield


def _sanear(obj):
    """Convierte recursivamente tipos numpy/pandas a tipos nativos de Python
    para que cualquier resultado de una herramienta sea JSON-serializable."""
    if isinstance(obj, dict):
        return {str(k): _sanear(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanear(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _df_a_registros(df):
    """Convierte un DataFrame (con índice con nombre) a una lista de dicts JSON-serializable."""
    return df.reset_index().to_dict(orient="records")


# ---------------------------------------------------------------------------
# Paso 2: Análisis exploratorio
# ---------------------------------------------------------------------------

@mcp.tool()
def obtener_estadisticas_basicas() -> dict:
    """Calcula media, mediana, moda y desviación estándar de las variables
    numéricas: edad, venta_total, n_compras, monto_compra y tiempo."""
    df = eda.obtener_datos()
    stats = eda.calcular_estadisticas(df)
    return _sanear({"estadisticas": stats.to_dict(orient="records")})


@mcp.tool()
def obtener_ventas_por_mes() -> dict:
    """Devuelve el monto total de ventas (suma de monto_compra) para cada
    mes del año 2025, útil para ver la distribución de ventas por mes."""
    df = eda.obtener_datos()
    ventas_mes = (
        df.dropna(subset=["fecha_compra"])
        .groupby(df["fecha_compra"].dt.month)["monto_compra"]
        .sum()
        .reindex(range(1, 13), fill_value=0)
    )
    return _sanear({eda.MESES_ES[i - 1]: round(float(v), 2) for i, v in ventas_mes.items()})


@mcp.tool()
def obtener_distribucion_categorica(columna: str) -> dict:
    """Devuelve el conteo de clientes por categoría para una columna dada.
    columna debe ser una de: 'metodo_pago', 'navegador', 'boletin', 'vale', 'genero'."""
    df = eda.obtener_datos()
    if columna not in eda.ETIQUETAS:
        return {"error": f"columna inválida, usa una de: {list(eda.ETIQUETAS.keys())}"}
    conteo = df[columna].map(eda.ETIQUETAS[columna]).value_counts(dropna=True)
    faltantes = int(df[columna].isna().sum())
    return _sanear({"distribucion": conteo.to_dict(), "registros_sin_dato": faltantes})


# ---------------------------------------------------------------------------
# Paso 3: Análisis de tendencias
# ---------------------------------------------------------------------------

@mcp.tool()
def obtener_meses_mayor_menor_venta() -> dict:
    """Identifica el mes con mayores ventas y el mes con menores ventas del año 2025."""
    df = eda.obtener_datos()
    ventas_mes = (
        df.dropna(subset=["fecha_compra"])
        .groupby(df["fecha_compra"].dt.month)["monto_compra"]
        .sum()
        .reindex(range(1, 13), fill_value=0)
    )
    mes_max, mes_min = ventas_mes.idxmax(), ventas_mes.idxmin()
    return _sanear({
        "mes_mayor_venta": eda.MESES_ES[mes_max - 1],
        "monto_mayor_venta": round(float(ventas_mes[mes_max]), 2),
        "mes_menor_venta": eda.MESES_ES[mes_min - 1],
        "monto_menor_venta": round(float(ventas_mes[mes_min]), 2),
    })


@mcp.tool()
def obtener_navegador_preferido() -> dict:
    """Identifica el navegador más preferido y el menos popular entre los clientes."""
    df = eda.obtener_datos()
    conteo = df["navegador"].dropna().map(eda.ETIQUETAS["navegador"]).value_counts()
    return _sanear({
        "mas_preferido": conteo.idxmax(),
        "cantidad_mas_preferido": int(conteo.max()),
        "menos_popular": conteo.idxmin(),
        "cantidad_menos_popular": int(conteo.min()),
        "distribucion_completa": conteo.to_dict(),
    })


@mcp.tool()
def obtener_pago_efectivo_vs_tarjeta() -> dict:
    """Compara el total de ventas pagadas contra entrega/efectivo contra el
    total pagado con tarjeta (crédito + débito combinados)."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        resultado = tendencias.ventas_efectivo(df)
    return _sanear(resultado)


@mcp.tool()
def obtener_boletin_vale_por_mes() -> dict:
    """Devuelve, para cada mes de 2025, cuántos clientes usaron Boletín y
    cuántos usaron Vale, e identifica los meses con mayor uso de cada uno."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        boletin_mes, vale_mes = tendencias.boletin_vale_por_mes(df)
    return _sanear({
        "boletin_por_mes": {eda.MESES_ES[i - 1]: int(v) for i, v in boletin_mes.items()},
        "vale_por_mes": {eda.MESES_ES[i - 1]: int(v) for i, v in vale_mes.items()},
        "mes_top_boletin": eda.MESES_ES[boletin_mes.idxmax() - 1],
        "mes_top_vale": eda.MESES_ES[vale_mes.idxmax() - 1],
    })


# ---------------------------------------------------------------------------
# Paso 4: Segmentación de clientes
# ---------------------------------------------------------------------------

@mcp.tool()
def obtener_segmentacion_por_edad() -> dict:
    """Agrupa a los clientes por rango de edad (<18, 18-25, 26-35, 36-45,
    46-55, 56-65, 66+) y calcula sus patrones de compra promedio."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        resumen = segmentacion.segmentar_por_edad(df)
    return _sanear({"por_grupo_edad": _df_a_registros(resumen)})


@mcp.tool()
def obtener_comparacion_por_genero() -> dict:
    """Compara el comportamiento de compra promedio (venta_total, n_compras,
    monto_compra, tiempo) entre clientes Femenino y Masculino."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        resumen = segmentacion.comparar_por_genero(df)
    return _sanear({"por_genero": _df_a_registros(resumen)})


@mcp.tool()
def obtener_segmentacion_boletin_vale() -> dict:
    """Agrupa a los clientes por las 4 combinaciones de uso de Boletín y Vale
    (Sí/No cada uno) y calcula sus patrones de compra promedio."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        resumen = segmentacion.segmentar_por_boletin_vale(df)
    return _sanear({"por_boletin_vale": _df_a_registros(resumen)})


# ---------------------------------------------------------------------------
# Paso 5: Análisis de correlación
# ---------------------------------------------------------------------------

@mcp.tool()
def obtener_correlacion_edad_venta() -> dict:
    """Calcula la correlación de Pearson entre la edad del cliente y el
    total de la venta (Venta_total), con su significancia estadística."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        r, p = correlacion.correlacion_venta_edad(df)
    return _sanear({"coeficiente_pearson_r": round(float(r), 3), "p_valor": round(float(p), 4),
            "interpretacion": correlacion._interpretar_r(r),
            "significativo_al_95pct": bool(p < 0.05)})


@mcp.tool()
def obtener_correlacion_genero_metodo_pago() -> dict:
    """Examina si existe asociación entre el género del cliente y el método
    de pago preferido, usando la prueba Chi-cuadrado y Cramér's V."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        tabla, v, p = correlacion.correlacion_genero_pago(df)
    return _sanear({"tabla_contingencia": tabla.astype(int).to_dict(), "cramers_v": round(float(v), 3),
            "p_valor": round(float(p), 4), "significativo_al_95pct": bool(p < 0.05)})


@mcp.tool()
def obtener_correlacion_boletin_vale() -> dict:
    """Investiga si existe correlación entre los clientes que utilizan
    Boletín y los que utilizan Vale (coeficiente phi y Chi-cuadrado)."""
    df = eda.obtener_datos()
    with _silenciar_stdout():
        tabla, r, p = correlacion.correlacion_boletin_vale(df)
    return _sanear({"tabla_contingencia": tabla.astype(int).to_dict(), "coeficiente_phi": round(float(r), 3),
            "p_valor": round(float(p), 4), "significativo_al_95pct": bool(p < 0.05)})


# ---------------------------------------------------------------------------
# Paso 6: Visualización (lista de gráficos ya generados)
# ---------------------------------------------------------------------------

@mcp.tool()
def listar_graficos_disponibles() -> dict:
    """Lista los archivos de gráficos (.png) ya generados en reports/figures/,
    con una breve descripción de qué muestra cada uno."""
    descripciones = {
        "01_ventas_por_mes.png": "Distribución de ventas por mes",
        "02_metodo_pago.png": "Distribución por método de pago",
        "03_navegador.png": "Distribución por navegador",
        "04_boletin.png": "Distribución por uso de Boletín",
        "05_vale.png": "Distribución por uso de Vale",
        "06_navegador_top_bottom.png": "Navegador más y menos popular",
        "07_boletin_vale_por_mes.png": "Uso de Boletín y Vale por mes",
        "08_pago_efectivo_vs_tarjeta.png": "Monto: contra entrega vs. tarjeta",
        "09_venta_promedio_por_edad.png": "Venta promedio por grupo de edad",
        "10_comportamiento_por_genero.png": "Comportamiento de compra por género",
        "11_venta_por_boletin_vale.png": "Venta promedio por Boletín/Vale",
        "12_correlacion_edad_venta.png": "Correlación edad vs. venta_total",
        "13_genero_vs_metodopago.png": "Método de pago preferido por género",
        "14_boletin_vs_vale.png": "Relación entre uso de Boletín y Vale",
    }
    fig_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "figures")
    existentes = set(os.listdir(fig_dir)) if os.path.isdir(fig_dir) else set()
    return {
        nombre: {"descripcion": desc, "existe": nombre in existentes}
        for nombre, desc in descripciones.items()
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")