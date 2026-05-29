from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Serviço de Estoque", version="1.0.0")

# Estoque em memória para MVP (em produção: banco de dados próprio por serviço)
_estoque: Dict[str, int] = {
    "PROD-001": 100,
    "PROD-002": 50,
    "PROD-003": 200,
}


class ReservaRequest(BaseModel):
    produto_id: str
    quantidade: int


class BaixaRequest(BaseModel):
    produto_id: str
    quantidade: int


class EstoqueResponse(BaseModel):
    produto_id: str
    quantidade_disponivel: int
    operacao: str
    sucesso: bool


@app.get("/health")
def health():
    return {"status": "ok", "service": "estoque"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/estoque/{produto_id}")
def consultar_estoque(produto_id: str):
    qtd = _estoque.get(produto_id)
    if qtd is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado no estoque")
    return {"produto_id": produto_id, "quantidade_disponivel": qtd}


@app.post("/estoque/reserva", response_model=EstoqueResponse)
def reservar(reserva: ReservaRequest):
    """Reserva quantidade sem baixar — usada no momento da criação do pedido."""
    logger.info(f"Reservando {reserva.quantidade} unidades de {reserva.produto_id}")
    disponivel = _estoque.get(reserva.produto_id, 0)

    if disponivel < reserva.quantidade:
        logger.warning(f"Estoque insuficiente para {reserva.produto_id}: disponível={disponivel}, solicitado={reserva.quantidade}")
        raise HTTPException(status_code=409, detail=f"Estoque insuficiente. Disponível: {disponivel}")

    return EstoqueResponse(
        produto_id=reserva.produto_id,
        quantidade_disponivel=disponivel,
        operacao="RESERVA",
        sucesso=True,
    )


@app.post("/estoque/baixa", response_model=EstoqueResponse)
def baixar(baixa: BaixaRequest):
    """Confirma a baixa do estoque após pagamento aprovado."""
    logger.info(f"Baixando {baixa.quantidade} unidades de {baixa.produto_id}")
    disponivel = _estoque.get(baixa.produto_id, 0)

    if disponivel < baixa.quantidade:
        raise HTTPException(status_code=409, detail="Estoque insuficiente para baixa")

    _estoque[baixa.produto_id] -= baixa.quantidade
    logger.info(f"Baixa realizada. Novo saldo de {baixa.produto_id}: {_estoque[baixa.produto_id]}")

    return EstoqueResponse(
        produto_id=baixa.produto_id,
        quantidade_disponivel=_estoque[baixa.produto_id],
        operacao="BAIXA",
        sucesso=True,
    )
