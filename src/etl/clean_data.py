"""
ETL - Paso 1: Preparación de datos
Curso: Sistemas Organizacionales y Gerenciales 2 - Práctica 1

Este script:
    a. Extrae los datos del archivo .csv
    b. Verifica valores faltantes y duplicados
    c. Normaliza tipos de datos y corrige formatos inconsistentes
    d. Deja el DataFrame listo para cargarse a la base de datos (load_to_db.py)

Ejecutar:
    python src/etl/clean_data.py data/ventas_online_2025.csv
"""

import sys
import re
import pandas as pd
import numpy as np


# ---------- Reglas de negocio / catálogos válidos según el enunciado ----------
GENERO_VALIDOS = {0, 1}
METODOPAGO_VALIDOS = {0, 1, 2}
NAVEGADOR_VALIDOS = {0, 1, 2, 3, 4}
BOLETIN_VALE_VALIDOS = {0, 1}

# Rango de edad plausible para una persona real (fuera de esto es error de captura)
EDAD_MIN = 0
EDAD_MAX = 100

MAPA_TEXTO_BINARIO = {
    "no": 0, "n": 0, "false": 0, "0": 0,
    "si": 1, "sí": 1, "s": 1, "true": 1, "1": 1,
}

# Genero tiene su propio texto (Femenino=1 / Masculino=0 según el enunciado)
MAPA_TEXTO_GENERO = {
    "femenino": 1, "f": 1,
    "masculino": 0, "m": 0,
}


def parse_money(valor):
    """Convierte strings de dinero con formatos mixtos a float.
    Maneja: '$1751.49', '717,27', '1,397,86', '"558.08"', vacíos, etc.
    Regla de negocio: los montos no pueden ser negativos -> se usa valor absoluto.
    """
    if pd.isna(valor):
        return np.nan
    s = str(valor).strip()
    s = s.replace('"', "").replace("$", "").replace(" ", "")
    if s == "":
        return np.nan

    negativo = s.startswith("-")
    s = s.lstrip("-")

    n_comas = s.count(",")
    n_puntos = s.count(".")

    if n_comas >= 2:
        # ej: "1,397,86" -> la última coma es el separador decimal
        partes = s.split(",")
        entero = "".join(partes[:-1])
        decimal = partes[-1]
        s = f"{entero}.{decimal}"
    elif n_comas == 1 and n_puntos == 0:
        # ej: "717,27" -> coma como separador decimal (formato europeo)
        s = s.replace(",", ".")
    elif n_comas >= 1 and n_puntos >= 1:
        # ej: "1,751.49" -> coma es separador de miles, punto es decimal
        s = s.replace(",", "")
    # si no hay comas, se asume que ya viene con punto decimal estándar

    try:
        valor_float = float(s)
    except ValueError:
        return np.nan

    return abs(valor_float) if negativo else valor_float


def parse_fecha(valor):
    """Normaliza fechas en múltiples formatos a Timestamp (YYYY-MM-DD).
    Formatos detectados en los datos:
        YYYY/MM/DD, YYYY-MM-DD  -> año al inicio
        MM/DD/YYYY (slash, año al final)  -> mes primero (convención EE.UU.)
        DD-MM-YYYY (guion, año al final)  -> día primero
    """
    if pd.isna(valor):
        return pd.NaT
    s = str(valor).strip()

    sep = "/" if "/" in s else ("-" if "-" in s else None)
    if sep is None:
        return pd.NaT

    partes = s.split(sep)
    if len(partes) != 3:
        return pd.NaT

    try:
        if len(partes[0]) == 4:  # año al inicio -> YYYY-MM-DD
            anio, mes, dia = partes
        elif sep == "/":  # slash con año al final -> MM/DD/YYYY
            mes, dia, anio = partes
        else:  # guion con año al final -> DD-MM-YYYY
            dia, mes, anio = partes

        return pd.Timestamp(year=int(anio), month=int(mes), day=int(dia))
    except (ValueError, TypeError):
        return pd.NaT


def limpiar_categorica(serie, valores_validos, mapa_texto=None):
    """Normaliza una columna categórica: mapea texto conocido y marca NaN
    cualquier valor fuera del catálogo válido."""
    def _limpiar(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip().lower()
        if mapa_texto and s in mapa_texto:
            v = mapa_texto[s]
        try:
            v = int(float(v))
        except (ValueError, TypeError):
            return np.nan
        return v if v in valores_validos else np.nan

    return serie.apply(_limpiar)


def limpiar_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Aplica toda la limpieza y devuelve el DataFrame limpio + un reporte."""
    reporte = {}
    df = df.copy()

    # --- b. Duplicados (filas 100% idénticas) ---
    dup = df.duplicated().sum()
    reporte["filas_duplicadas_eliminadas"] = int(dup)
    df = df.drop_duplicates()

    # --- b. Duplicados por Id_cliente (mismo cliente con datos distintos) ---
    # Regla de negocio: Id_cliente debe ser único (es la llave primaria en la BD).
    # Se conserva la primera aparición y se descartan las repeticiones posteriores.
    dup_id = df["Id_cliente"].duplicated().sum()
    reporte["ids_cliente_duplicados_eliminados"] = int(dup_id)
    df = df.drop_duplicates(subset="Id_cliente", keep="first")

    # --- c. Tipos de datos correctos ---

    # Montos
    for col in ["Venta_total", "MontoCompra"]:
        antes_negativos = df[col].astype(str).str.strip().str.startswith("-").sum()
        df[col] = df[col].apply(parse_money)
        reporte[f"{col}_negativos_corregidos"] = int(antes_negativos)

    # Fecha
    df["FechaCompra"] = df["FechaCompra"].apply(parse_fecha)
    reporte["fechas_invalidas"] = int(df["FechaCompra"].isna().sum())

    # Categóricas binarias / con catálogo
    df["Genero"] = limpiar_categorica(df["Genero"], GENERO_VALIDOS, MAPA_TEXTO_GENERO)
    df["MetodoPago"] = limpiar_categorica(df["MetodoPago"], METODOPAGO_VALIDOS, MAPA_TEXTO_BINARIO)
    df["Navegador"] = limpiar_categorica(df["Navegador"], NAVEGADOR_VALIDOS, MAPA_TEXTO_BINARIO)
    df["Boletín"] = limpiar_categorica(df["Boletín"], BOLETIN_VALE_VALIDOS, MAPA_TEXTO_BINARIO)
    df["Vale"] = limpiar_categorica(df["Vale"], BOLETIN_VALE_VALIDOS, MAPA_TEXTO_BINARIO)

    # Numéricos simples
    df["Edad"] = pd.to_numeric(df["Edad"], errors="coerce")
    # Edades imposibles (negativas o mayores a EDAD_MAX) -> inválidas, no solo "atípicas"
    edades_imposibles = ((df["Edad"] < EDAD_MIN) | (df["Edad"] > EDAD_MAX)).sum()
    reporte["edades_imposibles_invalidadas"] = int(edades_imposibles)
    df.loc[(df["Edad"] < EDAD_MIN) | (df["Edad"] > EDAD_MAX), "Edad"] = np.nan

    df["N_Compras"] = pd.to_numeric(df["N_Compras"], errors="coerce")
    df["Tiempo"] = pd.to_numeric(df["Tiempo"], errors="coerce")
    df["Id_cliente"] = pd.to_numeric(df["Id_cliente"], errors="coerce").astype("Int64")

    # Bandera de edad atípica: menor de edad, pero dentro de un rango plausible
    # (ya no incluye los valores imposibles, que ahora son NaN)
    df["edad_atipica"] = df["Edad"] < 18
    reporte["clientes_edad_atipica"] = int(df["edad_atipica"].sum())

    # --- b. Valores faltantes (conteo por columna, después de limpiar) ---
    faltantes = df.isna().sum()
    reporte["valores_faltantes_por_columna"] = faltantes[faltantes > 0].to_dict()

    return df, reporte


def generar_reporte_txt(reporte: dict, filas_originales: int, filas_finales: int, ruta_csv_limpio: str, ruta_reporte: str):
    """Guarda un resumen legible de las transformaciones aplicadas."""
    faltantes = reporte.get("valores_faltantes_por_columna", {})

    lineas = [
        "REPORTE DE LIMPIEZA ETL",
        "=======================",
        "",
        "Resumen del proceso",
        f"Filas originales: {filas_originales}",
        f"Filas finales: {filas_finales}",
        f"Filas eliminadas por duplicado exacto: {reporte.get('filas_duplicadas_eliminadas', 0)}",
        f"IDs de cliente duplicados eliminados: {reporte.get('ids_cliente_duplicados_eliminados', 0)}",
        "",
        "Limpieza realizada",
        "- Montos monetarios normalizados a valores numericos.",
        f"- Negativos corregidos en Venta_total: {reporte.get('Venta_total_negativos_corregidos', 0)}",
        f"- Negativos corregidos en MontoCompra: {reporte.get('MontoCompra_negativos_corregidos', 0)}",
        "- Fechas convertidas a formato YYYY-MM-DD.",
        f"- Fechas invalidas encontradas: {reporte.get('fechas_invalidas', 0)}",
        "- Categorias normalizadas segun los catalogos validos.",
        f"- Edades imposibles invalidadas: {reporte.get('edades_imposibles_invalidadas', 0)}",
        f"- Clientes menores de edad marcados como atipicos: {reporte.get('clientes_edad_atipica', 0)}",
        "",
        "Valores faltantes despues de la limpieza",
    ]

    if faltantes:
        lineas.extend(f"- {columna}: {cantidad}" for columna, cantidad in faltantes.items())
    else:
        lineas.append("- No quedaron valores faltantes.")

    lineas.extend([
        "",
        "Archivos generados",
        f"- CSV limpio: {ruta_csv_limpio}",
        f"- Este reporte: {ruta_reporte}",
    ])

    with open(ruta_reporte, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/ventas_online_2025.csv"
    print(f"Leyendo: {ruta}")
    df_crudo = pd.read_csv(ruta)
    print(f"Filas originales: {len(df_crudo)}")

    df_limpio, reporte = limpiar_datos(df_crudo)

    print("\n--- Reporte de limpieza ---")
    for k, v in reporte.items():
        print(f"{k}: {v}")

    print(f"\nFilas finales: {len(df_limpio)}")
    print("\nTipos de dato finales:")
    print(df_limpio.dtypes)

    salida = ruta.replace(".csv", "_limpio.csv")
    df_limpio.to_csv(salida, index=False)
    print(f"\nGuardado: {salida}")

    ruta_reporte = "Reporte.txt"
    generar_reporte_txt(reporte, len(df_crudo), len(df_limpio), salida, ruta_reporte)
    print(f"Reporte guardado: {ruta_reporte}")


if __name__ == "__main__":
    main()