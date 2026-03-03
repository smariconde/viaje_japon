FROM python:3.12-slim

WORKDIR /app

# Instalar uv
RUN pip install --no-cache-dir uv

# Copiar definición de dependencias primero (mejor cache de capas)
COPY pyproject.toml .
COPY src/ ./src/

# Instalar dependencias del proyecto
RUN uv sync --no-dev

# Directorio de datos persistente
# En Railway: montar un Volume en /app/data para que el historial no se pierda
RUN mkdir -p /app/data

# Por defecto corre un chequeo único (Railway lo invoca por cron)
# Para modo monitor continuo: CMD ["uv", "run", "japon", "flights", "monitor"]
CMD ["uv", "run", "japon", "flights", "check"]
