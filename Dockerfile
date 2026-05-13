FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =====================================================
# HuggingFace / Transformers cache (WAJIB)
# =====================================================
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1

# =====================================================
# System dependencies
# =====================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    postgresql-client \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =====================================================
# App setup
# =====================================================
WORKDIR /app

COPY requirements.txt .

# pip install (hemat layer & cache)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# HF cache directory (runtime)
RUN mkdir -p /app/.cache/huggingface && chmod -R 777 /app/.cache

COPY . .

# =====================================================
# ENTRYPOINT
# =====================================================
CMD ["python", "main.py"]
