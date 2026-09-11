# SOG2 - Práctica 1: Análisis de Ventas con Agente IA

Proyecto para el curso Sistemas Organizacionales y Gerenciales 2.

Análisis de ventas online 2025 con carga a base de datos en la nube (Neon Postgres)
y agente conversacional (Google ADK + MCP Server) para entregar resultados bajo demanda.

## Estructura del proyecto

```
sog2-practica1/
├── docker-compose.yml     # servicios (app, etc.)
├── requirements.txt       # dependencias Python
├── .env.example           # plantilla de variables de entorno
├── data/                  # csv de ventas (no se sube el csv real)
├── src/
│   ├── etl/                # limpieza y carga a la BD
│   ├── analysis/            # EDA, tendencias, segmentación, correlación
│   └── agent/                # agente IA + MCP server
├── notebooks/              # exploración
└── README.md
```

## Setup rápido

1. Clonar el repo.
2. Copiar `.env.example` a `.env` y llenar con tus credenciales reales (Neon, API key del modelo).
3. Crear entorno virtual e instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. (Próximos pasos) Levantar contenedor Docker / correr el ETL / correr el agente.

## Decisiones de limpieza de datos

- **Montos con formato mixto** (`$`, comas europeas, comillas): se normalizan a `float` estándar.
- **Montos negativos**: se asume error de captura y se usa valor absoluto (una venta no puede ser negativa). Se cuenta y documenta cuántos casos se corrigieron.
- **Fechas en múltiples formatos**: se detecta la posición del año (inicio/final) y el separador (`/` o `-`) para normalizar todo a `YYYY-MM-DD`.
- **Códigos categóricos fuera de catálogo** (ej. `Genero=10`, `MetodoPago=5`, `Navegador=99`): se convierten a `NaN` en lugar de eliminarse o inventarse un valor.
- **Filas con `NaN` en columnas categóricas**: **se conservan** (no se eliminan del dataset). Cada análisis específico excluye esos `NaN` únicamente en los cálculos donde esa columna participa, para no perder información del resto de la fila.
- **NULL en la base de datos (no valor por defecto)**: se decidió cargar los faltantes como `NULL` en Postgres en vez de un valor por defecto como `0`. Razón: en columnas como `MetodoPago`, `Navegador`, `Boletín`, `Vale` y `Genero`, el `0` ya tiene un significado real (Efectivo, Tienda Física, No, No, Masculino). Usar `0` como relleno inflaría artificialmente esas categorías y sesgaría las estadísticas. `NULL` es semánticamente correcto ("desconocido") y Postgres lo excluye automáticamente de `AVG()`, `COUNT()`, `SUM()`.
- **IDs de cliente duplicados**: `Id_cliente` es la llave primaria de la tabla `ventas`; cuando el mismo ID aparecía más de una vez con datos distintos, se conservó solo la primera aparición y se descartaron las repeticiones (se documenta cuántas).
- **Edades imposibles** (negativas o mayores a 100): se invalidan (`NULL`), a diferencia de edades simplemente atípicas (<18, pero plausibles), que se conservan con la bandera `edad_atipica`.
- **Boletín/Vale como texto** (`"No"`, `"Sí"`, `"Masculino"`): se mapean valores reconocibles (`No`→0, `Sí`→1) y cualquier valor sin sentido (`Masculino`) se marca como `NaN`.
- **Edad atípica** (< 18 años): no se elimina, se marca con la columna booleana `edad_atipica` para que el equipo decida si la excluye en la segmentación.
- **Duplicados**: se eliminan filas 100% idénticas.
