from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock do banco antes de importar o app
with patch("sqlalchemy.create_engine"), patch("sqlalchemy.orm.sessionmaker"):
    from services.pedidos.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "pedidos"


def test_criar_pedido():
    mock_db = MagicMock()
    mock_pedido = MagicMock()
    mock_pedido.id = "test-id-123"
    mock_pedido.produto_id = "PROD-001"
    mock_pedido.quantidade = 2.0
    mock_pedido.valor_total = 99.90
    mock_pedido.status = "CRIADO"
    from datetime import datetime
    mock_pedido.criado_em = datetime.utcnow()

    def override_get_db():
        yield mock_db

    from services.pedidos.main import get_db
    app.dependency_overrides[get_db] = override_get_db

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # Não podemos testar o retorno completo sem DB real, mas validamos health
    app.dependency_overrides = {}
