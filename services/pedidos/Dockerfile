# ============================================================
# Stage 1 — builder: instala dependências
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Copia apenas o requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt --target=/app/deps

# ============================================================
# Stage 2 — runtime: imagem final enxuta
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Cria usuário não-root (boa prática de segurança)
RUN useradd --no-create-home --shell /bin/false appuser

# Copia dependências instaladas do builder
COPY --from=builder /app/deps /app/deps
ENV PYTHONPATH=/app/deps

# Copia apenas o código da aplicação
COPY main.py .

# Muda para usuário não-root antes de expor/executar
USER appuser

EXPOSE 8000

# Healthcheck interno do container
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
