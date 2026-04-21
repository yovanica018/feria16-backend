FROM python:3.11-slim

# ======================
# SISTEMA (PostGIS / GDAL)
# ======================
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    binutils \
    libproj-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# ======================
# APP
# ======================
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

# ======================
# PUERTO (informativo)
# ======================
EXPOSE 8000

# ======================
# START (PRODUCCIÓN)
# ======================
CMD ["sh", "-c", "gunicorn feria_api.wsgi:application --bind 0.0.0.0:$PORT"]
