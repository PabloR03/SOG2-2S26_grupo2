"""
Conexión compartida a la base de datos (Neon Postgres).
Usado tanto por el ETL (load_to_db.py) como por el análisis (src/analysis/*).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


def get_engine():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "No se encontró DATABASE_URL. Crea un archivo .env "
            "(copia .env.example) con tu connection string de Neon."
        )
    return create_engine(db_url)