# Pedidos Veloz — Plataforma de Microsserviços

> Trabalho acadêmico — Cloud DevOps | UniFECAF  
> Entrega contínua de uma plataforma de pedidos em microsserviços: do Docker Compose ao Kubernetes com observabilidade e CI/CD

---

## Visão Geral da Arquitetura

```
[Cliente] → [API Gateway :8080]
                ├── [Serviço de Pedidos :8000] → [PostgreSQL]
                ├── [Serviço de Pagamentos :8001]
                └── [Serviço de Estoque :8002]
                         ↕
                    [RabbitMQ]
```

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.11 + FastAPI |
| Conteinerização | Docker + Docker Compose |
| Orquestração | Kubernetes (kind para dev, GKE para prod) |
| CI/CD | GitHub Actions |
| IaC | Terraform (GKE) |
| Banco de dados | PostgreSQL 16 |
| Mensageria | RabbitMQ 3.13 |

---

## Ambiente Local (Docker Compose)

### Pré-requisitos
- Docker Engine 24+
- Docker Compose v2+

### Subindo o ambiente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USER/pedidos-veloz.git
cd pedidos-veloz

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. Sobe todos os serviços com um único comando
docker compose up --build

# 4. Verifique o status
docker compose ps
```

### Endpoints disponíveis localmente

| Serviço | URL |
|---------|-----|
| API Gateway (ponto de entrada) | http://localhost:8080 |
| Docs interativos (Swagger) | http://localhost:8080/docs |
| RabbitMQ Management | http://localhost:15672 |

### Testando o fluxo completo

```bash
# Criar um pedido (fluxo completo: estoque → pedido → pagamento → baixa)
curl -X POST http://localhost:8080/api/v1/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "produto_id": "PROD-001",
    "quantidade": 2,
    "valor_total": 99.90,
    "metodo_pagamento": "cartao_credito"
  }'

# Consultar um pedido
curl http://localhost:8080/api/v1/pedidos/{pedido_id}
```

---

## Kubernetes (kind — local)

### Pré-requisitos
- kind instalado: `go install sigs.k8s.io/kind@latest`
- kubectl instalado

```bash
# 1. Cria o cluster local
kind create cluster --name pedidos-veloz

# 2. Cria o namespace
kubectl create namespace pedidos-veloz

# 3. Aplica os manifests na ordem correta
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/hpa/

# 4. Verifica os pods
kubectl get pods -n pedidos-veloz

# 5. Acessa o gateway via port-forward
kubectl port-forward svc/api-gateway-svc 8080:80 -n pedidos-veloz
```

> **Nota:** Substitua `SEU_DOCKERHUB_USER` nos arquivos de deployment pelo seu usuário real do Docker Hub antes de aplicar.

---

## CI/CD (GitHub Actions)

O pipeline executa automaticamente em:
- **Pull Request para main:** lint + testes
- **Push na main:** lint + testes + build + push de imagens + deploy

### Secrets necessários no repositório GitHub

| Secret | Descrição |
|--------|-----------|
| `DOCKERHUB_USERNAME` | Usuário do Docker Hub |
| `DOCKERHUB_TOKEN` | Token de acesso (não a senha) |
| `KUBECONFIG` | kubeconfig em base64 para o cluster de produção |

Configure em: **Settings → Secrets and variables → Actions**

---

## Infraestrutura como Código (Terraform)

```bash
cd terraform

# Inicializa os providers
terraform init

# Visualiza o plano sem aplicar
terraform plan -var="project_id=SEU_PROJECT_ID"

# Aplica a infraestrutura
terraform apply -var="project_id=SEU_PROJECT_ID"
```

---

## Observabilidade

| Pilar | Abordagem |
|-------|-----------|
| **Métricas** | Prometheus + Grafana (FastAPI expõe `/metrics` via `prometheus-fastapi-instrumentator`) |
| **Logs** | Logs estruturados em stdout (padrão 12-Factor), coletados pelo Fluentd/Loki |
| **Tracing** | OpenTelemetry com Jaeger — trace IDs propagados entre serviços via headers HTTP |

---

## Decisões Arquiteturais

**Rolling Update vs Blue/Green/Canary:** escolhemos Rolling Update por ser a estratégia nativa do Kubernetes, suficiente para o MVP e com zero downtime garantido via `maxUnavailable: 0`.

**Banco compartilhado:** para o MVP acadêmico, um único PostgreSQL com schemas por serviço foi adotado. Em produção, o padrão correto é *Database per Service*.

**Mensageria (RabbitMQ):** incluída para desacoplar Pedidos de Estoque/Pagamentos, eliminando dependências síncronas que cascateiam falhas.

---

## Vídeo Pitch

🎥 [Link do YouTube — adicionar após gravação]

---

## Estrutura do Repositório

```
pedidos-veloz/
├── services/
│   ├── api-gateway/
│   ├── pedidos/
│   ├── pagamentos/
│   └── estoque/
├── k8s/
│   ├── deployments/
│   ├── services/
│   ├── configmaps/
│   ├── secrets/
│   └── hpa/
├── terraform/
│   └── modules/k8s-cluster/
├── tests/
├── .github/workflows/ci-cd.yml
├── docker-compose.yml
└── README.md
```
