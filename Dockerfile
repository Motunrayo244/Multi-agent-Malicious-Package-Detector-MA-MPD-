# Multi-Agent Python Package Detection - API Service
# Use x86_64 platform for TensorFlow compatibility with agents library
FROM --platform=linux/amd64 python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git ca-certificates libstdc++6 libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install uv (astral) for faster package management if you want to keep it
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install project dependencies via uv
RUN /root/.local/bin/uv sync --frozen

# Copy application code
COPY . .

RUN mkdir -p logs

ENV TF_CPP_MIN_LOG_LEVEL=3
ENV TF_ENABLE_ONEDNN_OPTS=0
ENV AGENTS_NO_TENSORFLOW=1

EXPOSE 8000

# Use uv to run uvicorn if you prefer; otherwise call uvicorn directly
CMD ["uv", "run", "uvicorn", "api.classify:app", "--host", "0.0.0.0", "--port", "8000"]
