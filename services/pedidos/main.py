from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import os
import uuid
import logging

# Logs como stream (12-Factor App - fator XI)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Serviço de Pedidos", version="1.0.0")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/pedidos_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PedidoDB(Base):
    __tablename__ = "pedidos"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    produto_id = Column(String, nullable=False)
    quantidade = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)
    status = Column(String, default="CRIADO")
    criado_em = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


class PedidoCreate(BaseModel):
    produto_id: str
    quantidade: float
    valor_total: float


class PedidoResponse(BaseModel):
    id: str
    produto_id: str
    quantidade: float
    valor_total: float
    status: str
    criado_em: datetime

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "pedidos"}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/pedidos", response_model=PedidoResponse, status_code=201)
def criar_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    logger.info(f"Criando pedido para produto {pedido.produto_id}")
    db_pedido = PedidoDB(**pedido.model_dump())
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    logger.info(f"Pedido {db_pedido.id} criado com sucesso")
    return db_pedido


@app.get("/pedidos/{pedido_id}", response_model=PedidoResponse)
def consultar_pedido(pedido_id: str, db: Session = Depends(get_db)):
    pedido = db.query(PedidoDB).filter(PedidoDB.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


@app.get("/pedidos", response_model=list[PedidoResponse])
def listar_pedidos(db: Session = Depends(get_db)):
    return db.query(PedidoDB).all()
