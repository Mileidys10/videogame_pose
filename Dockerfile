# ==============================================================================
# Dockerfile — VideoGame Pose Combat (MediaPipe + YOLOv8 + Pygame-CE)
# VideoGame Pose Combat - Docker Containerization
# ==============================================================================

FROM python:3.11-slim

LABEL maintainer="Mileidys10 <agamezmileidys@gmail.com>"
LABEL project="VideoGame Pose Combat"
LABEL version="1.0.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SDL_VIDEODRIVER=dummy \
    SDL_AUDIODRIVER=dummy

WORKDIR /app

# Instalar librerías nativas de sistema para OpenCV, MediaPipe y Pygame
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libasound2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y modelos de visión
COPY src/ ./src/
COPY models/ ./models/
COPY yolov8n-pose.pt .
COPY main.py .

# Puerto UDP estándar para juego en red multijugador LAN
EXPOSE 9999/udp

# Por defecto inicia el servidor de combate LAN en modo headless
CMD ["python", "main.py", "--mode", "host", "--port", "9999", "--backend", "mock", "--headless"]
