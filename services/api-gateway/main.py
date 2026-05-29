from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway - Pedidos Veloz", version="1.0.0")

# URLs dos serviços internos — injetadas via variável de ambiente (12-Factor: config por ambiente)
PEDIDOS_URL   = os.getenv("PEDIDOS_SERVICE_URL",   "http://pedidos:8000")
PAGAMENTOS_URL = os.getenv("PAGAMENTOS_SERVICE_URL", "http://pagamentos:8001")
ESTOQUE_URL   = os.getenv("ESTOQUE_SERVICE_URL",   "http://estoque:8002")

TIMEOUT = 10.0  # segundos


class NovoPedidoRequest(BaseModel):
    produto_id: str
    quantidade: int
    valor_total: float
    metodo_pagamento: str = "cartao_credito"


@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway", "timestamp": datetime.utcnow().isoformat()}


@app.get("/ready")
async def ready():
    """Verifica se todos os serviços downstream estão acessíveis."""
    resultados = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for nome, url in [("pedidos", PEDIDOS_URL), ("pagamentos", PAGAMENTOS_URL), ("estoque", ESTOQUE_URL)]:
            try:
                r = await client.get(f"{url}/health")
                resultados[nome] = "ok" if r.status_code == 200 else "degraded"
            except Exception:
                resultados[nome] = "unreachable"

    todos_ok = all(v == "ok" for v in resultados.values())
    status_code = 200 if todos_ok else 503
    return {"status": "ready" if todos_ok else "degraded", "servicos": resultados}


@app.post("/api/v1/pedidos", status_code=201)
async def criar_pedido_completo(payload: NovoPedidoRequest):
    """
    Orquestra o fluxo completo de criação de pedido:
    1. Verifica estoque
    2. Cria pedido
    3. Processa pagamento
    4. Baixa estoque
    """
    logger.info(f"[GATEWAY] Iniciando fluxo para produto={payload.produto_id}, qtd={payload.quantidade}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        # 1. Verifica estoque disponível
        try:
            r = await client.post(f"{ESTOQUE_URL}/estoque/reserva", json={
                "produto_id": payload.produto_id,
                "quantidade": payload.quantidade,
            })
            if r.status_code != 200:
                raise HTTPException(status_code=409, detail=r.json().get("detail", "Estoque indisponível"))
        except httpx.RequestError as e:
            logger.error(f"[GATEWAY] Serviço de estoque inacessível: {e}")
            raise HTTPException(status_code=503, detail="Serviço de estoque indisponível")

        # 2. Cria o pedido
        try:
            r = await client.post(f"{PEDIDOS_URL}/pedidos", json={
                "produto_id": payload.produto_id,
                "quantidade": payload.quantidade,
                "valor_total": payload.valor_total,
            })
            r.raise_for_status()
            pedido = r.json()
            pedido_id = pedido["id"]
        except httpx.RequestError as e:
            logger.error(f"[GATEWAY] Serviço de pedidos inacessível: {e}")
            raise HTTPException(status_code=503, detail="Serviço de pedidos indisponível")

        # 3. Processa pagamento
        try:
            r = await client.post(f"{PAGAMENTOS_URL}/pagamentos", json={
                "pedido_id": pedido_id,
                "valor": payload.valor_total,
                "metodo": payload.metodo_pagamento,
            })
            if r.status_code == 402:
                raise HTTPException(status_code=402, detail="Pagamento recusado")
            r.raise_for_status()
            pagamento = r.json()
        except httpx.RequestError as e:
            logger.error(f"[GATEWAY] Serviço de pagamentos inacessível: {e}")
            raise HTTPException(status_code=503, detail="Serviço de pagamentos indisponível")

        # 4. Confirma baixa no estoque
        try:
            await client.post(f"{ESTOQUE_URL}/estoque/baixa", json={
                "produto_id": payload.produto_id,
                "quantidade": payload.quantidade,
            })
        except Exception as e:
            # Não bloqueia — pagamento já foi aprovado. Em produção: fila de compensação.
            logger.error(f"[GATEWAY] Falha ao baixar estoque após pagamento aprovado: {e}")

    logger.info(f"[GATEWAY] Pedido {pedido_id} concluído com sucesso")
    return {
        "pedido_id": pedido_id,
        "status": "CONFIRMADO",
        "codigo_autorizacao": pagamento.get("codigo_autorizacao"),
        "valor_total": payload.valor_total,
    }


@app.get("/api/v1/pedidos/{pedido_id}")
async def consultar_pedido(pedido_id: str):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.get(f"{PEDIDOS_URL}/pedidos/{pedido_id}")
            if r.status_code == 404:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail="Serviço de pedidos indisponível")
