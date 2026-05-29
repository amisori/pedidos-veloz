from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import random
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Serviço de Pagamentos", version="1.0.0")


class PagamentoRequest(BaseModel):
    pedido_id: str
    valor: float
    metodo: str = "cartao_credito"


class PagamentoResponse(BaseModel):
    id: str
    pedido_id: str
    valor: float
    status: str
    processado_em: datetime
    codigo_autorizacao: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "pagamentos"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.post("/pagamentos", response_model=PagamentoResponse, status_code=201)
def processar_pagamento(pagamento: PagamentoRequest):
    """
    Simula integração com gateway de pagamento externo.
    Em produção, aqui entraria a chamada real à API do gateway (ex: Stripe, PagSeguro).
    """
    logger.info(f"Processando pagamento para pedido {pagamento.pedido_id}, valor R${pagamento.valor:.2f}")

    # Simulação: 95% de aprovação (comportamento realista de gateway)
    aprovado = random.random() > 0.05

    if not aprovado:
        logger.warning(f"Pagamento recusado para pedido {pagamento.pedido_id}")
        raise HTTPException(status_code=402, detail="Pagamento recusado pelo gateway externo")

    codigo = str(uuid.uuid4()).replace("-", "")[:12].upper()
    logger.info(f"Pagamento aprovado. Código: {codigo}")

    return PagamentoResponse(
        id=str(uuid.uuid4()),
        pedido_id=pagamento.pedido_id,
        valor=pagamento.valor,
        status="APROVADO",
        processado_em=datetime.utcnow(),
        codigo_autorizacao=codigo,
    )
