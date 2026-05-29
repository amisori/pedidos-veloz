FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt --target=/app/deps

FROM python:3.11-slim
WORKDIR /app
RUN useradd --no-create-home --shell /bin/false appuser
COPY --from=builder /app/deps /app/deps
ENV PYTHONPATH=/app/deps
COPY main.py .
USER appuser
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')"
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
