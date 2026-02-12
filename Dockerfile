# syntax=docker/dockerfile:1
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY modules/ ./modules/
COPY agent.py ./
COPY config.json ./

# Create cache directory
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Create non-root user
RUN useradd -m -u 1000 wikiscout && \
    chown -R wikiscout:wikiscout /app
USER wikiscout

# Set default command
ENTRYPOINT ["python", "agent.py"]
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python agent.py status || exit 1

# Labels
LABEL org.opencontainers.image.title="WikiScout"
LABEL org.opencontainers.image.description="Fast Wikipedia research agent"
LABEL org.opencontainers.image.source="https://github.com/steel-experiments/WikiScout"
LABEL org.opencontainers.image.version="1.1.0"

# Development stage
FROM base as dev

USER root
RUN pip install -e .[dev]
USER wikiscout

# Example usage:
# docker build -t wikiscout .
# docker run wikiscout search -q "Python programming"
# docker run wikiscout summarize -q "Machine Learning" --bullets 5
# docker run -v $(pwd)/cache:/app/cache wikiscout search -q "AI"
