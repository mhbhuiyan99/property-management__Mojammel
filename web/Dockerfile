FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# GDAL/GEOS/PROJ are required by django.contrib.gis (GeoDjango).
# libpq-dev + gcc are required to build psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch FIRST, from PyTorch's dedicated CPU wheel index.
# Without this, sentence-transformers pulls the default torch wheel, which
# bundles full NVIDIA CUDA libraries (multiple GB) even with no GPU present.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

