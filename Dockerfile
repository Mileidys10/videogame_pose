# ==============================================================================
# Dockerfile — VideoGame Pose Combat (MediaPipe + YOLOv8 + Pygame-CE)
# ==============================================================================

FROM python:3.11-slim

LABEL maintainer="Mileidys10 <agamezmileidys@gmail.com>"
LABEL project="VideoGame Pose Combat"
LABEL version="1.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SDL_VIDEODRIVER=dummy \
    SDL_AUDIODRIVER=dummy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libasound2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY models/ ./models/
COPY yolov8n-pose.pt .
COPY main.py .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 9999/udp

CMD ["python", "main.py", "--mode", "host", "--port", "9999", "--backend", "mock", "--headless"]
