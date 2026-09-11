"""
ETL - Paso 1.d: Cargar los datos limpios a la base de datos SQL en la nube (Neon Postgres)

Ejecutar (fuera de Docker, con tu entorno virtual activo):
    python src/etl/load_to_db.py data/ventas_online_2025_limpio.csv

Ejecutar con Docker:
    docker compose run app python src/etl/load_to_db.py data/ventas_online_2025_limpio.csv

Requiere que exista un archivo .env (ver .env.example) con DATABASE_URL apuntando a Neon.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Integer, Float, String, Date, Boolean

TABLE_NAME = "ventas"


def get_engine():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "No se encontró DATABASE_URL. Crea un archivo .env "
            "(copia .env.example) con tu connection string de Neon."
        )
    return create_engine(db_url)


def cargar(csv_path: str, if_exists: str = "replace"):
    print(f"Leyendo datos limpios: {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=["FechaCompra"])

    # Nombres de columnas en snake_case, más cómodo para SQL
    df = df.rename(columns={
        "Id_cliente": "id_cliente",
        "Edad": "edad",
        "Genero": "genero",
        "Venta_total": "venta_total",
        "N_Compras": "n_compras",
        "FechaCompra": "fecha_compra",
        "MontoCompra": "monto_compra",
        "MetodoPago": "metodo_pago",
        "Tiempo": "tiempo",
        "Navegador": "navegador",
        "Boletín": "boletin",
        "Vale": "vale",
        "edad_atipica": "edad_atipica",
    })

    dtype_map = {
        "id_cliente": Integer(),
        "edad": Integer(),
        "genero": Integer(),
        "venta_total": Float(),
        "n_compras": Integer(),
        "fecha_compra": Date(),
        "monto_compra": Float(),
        "metodo_pago": Integer(),
        "tiempo": Float(),
        "navegador": Integer(),
        "boletin": Integer(),
        "vale": Integer(),
        "edad_atipica": Boolean(),
    }

    engine = get_engine()
    print(f"Conectando a la base de datos y cargando tabla '{TABLE_NAME}' (modo: {if_exists})...")
    with engine.begin() as conn:
        df.to_sql(TABLE_NAME, conn, if_exists=if_exists, index=False, dtype=dtype_map)
        # Llave primaria (si la tabla se acaba de crear con replace)
        if if_exists == "replace":
            conn.execute(text(f'ALTER TABLE {TABLE_NAME} ADD PRIMARY KEY (id_cliente);'))

    print(f"Listo. {len(df)} filas cargadas en la tabla '{TABLE_NAME}'.")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/ventas_online_2025_limpio.csv"
    modo = sys.argv[2] if len(sys.argv) > 2 else "replace"
    cargar(ruta, modo)
