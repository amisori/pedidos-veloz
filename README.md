# Pedidos Veloz — Plataforma de Microsserviços

> **Trabalho Acadêmico — Cloud DevOps | UniFECAF 2026**  
> Entrega contínua de uma plataforma de pedidos em microsserviços: do Docker Compose ao Kubernetes com observabilidade e CI/CD

**Aluno:** Victor Pereira de Souza | **RA:** 73589  
**Repositório:** https://github.com/amisori/pedidos-veloz  
**Vídeo Pitch:** 🎥 https://youtu.be/m_ZfVAgK-tE

---

## Visão Geral da Arquitetura

```
[Cliente]
    │
    ▼
[API Gateway :8080]  ◄── único ponto de entrada externo
    │
    ├──► [Serviço de Pedidos :8000] ──► [PostgreSQL :5432]
    ├──► [Serviço de Pagamentos :8001] ──► [Gateway Externo (simulado)]
    └──► [Serviço de Estoque :8002]
              │              │
              └──────────────┘
                     │
                     ▼
              [RabbitMQ :5672]  ◄── mensageria assíncrona (evento PedidoCriado)
```

## Tecnologias

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Linguagem | Python + FastAPI | 3.11 / 0.111 |
| Conteinerização | Docker + Docker Compose | 24+ / v2+ |
| Orquestração | Kubernetes (kind dev · GKE prod) | 1.30 |
| CI/CD | GitHub Actions | — |
| IaC | Terraform (GKE) | 1.7+ |
| Banco de dados | PostgreSQL | 16-alpine |
| Mensageria | RabbitMQ | 3.13-management |

---

## Ambiente Local (Docker Compose)

### Pré-requisitos
- Docker Engine 24+
- Docker Compose v2+

### Subindo o ambiente

```bash
# 1. Clone o repositório
git clone https://github.com/amisori/pedidos-veloz.git
cd pedidos-veloz

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas senhas se necessário

# 3. Sobe todos os serviços com um único comando
docker compose up --build

# 4. Verifique o status (em outro terminal)
docker compose ps
```

Todos os 6 containers devem aparecer com status `healthy` em ~60 segundos.

### Endpoints disponíveis localmente

| Serviço | URL | Descrição |
|---------|-----|-----------|
| API Gateway | http://localhost:8080 | Ponto de entrada principal |
| Swagger UI | http://localhost:8080/docs | Documentação interativa da API |
| RabbitMQ Management | http://localhost:15672 | Interface de gerenciamento (dev) |

### Testando o fluxo completo

```bash
# Criar um pedido (fluxo: estoque → pedido → pagamento → baixa)
curl -X POST http://localhost:8080/api/v1/pedidos \
  -H "Content-Type: application/json" \
  -d '{
    "produto_id": "PROD-001",
    "quantidade": 2,
    "valor_total": 99.90,
    "metodo_pagamento": "cartao_credito"
  }'

# Resposta esperada:
# { "pedido_id": "...", "status": "CONFIRMADO", "codigo_autorizacao": "...", "valor_total": 99.9 }

# Consultar um pedido pelo ID retornado
curl http://localhost:8080/api/v1/pedidos/{pedido_id}
```

### Encerrando o ambiente

```bash
# Para e remove os containers (mantém volumes)
docker compose down

# Para, remove containers E volumes (limpa banco)
docker compose down -v
```

---

## Conteinerização e Versionamento de Imagens

Todos os serviços possuem **Dockerfiles multi-stage**, separando o ambiente de build do runtime. Boas práticas aplicadas:

- ✅ Usuário não-root (`appuser`) em todos os containers
- ✅ Imagem base enxuta (`python:3.11-slim`)
- ✅ Dependências mínimas via `pip --no-cache-dir`
- ✅ `HEALTHCHECK` declarado em cada Dockerfile

### Versionamento das imagens

As imagens são publicadas no Docker Hub com **tag baseada no SHA do commit Git**:

```
amisori/pedidos-veloz-api-gateway:sha-a1b2c3d
amisori/pedidos-veloz-pedidos:sha-a1b2c3d
amisori/pedidos-veloz-pagamentos:sha-a1b2c3d
amisori/pedidos-veloz-estoque:sha-a1b2c3d
```

Isso garante rastreabilidade completa entre código-fonte e artefato deployado. A tag `latest` é atualizada apenas em pushes na branch `main` via pipeline CI/CD.

---

## Kubernetes (kind — local)

### Pré-requisitos

```bash
# Windows (PowerShell como administrador)
winget install Kubernetes.kind
winget install Kubernetes.kubectl

# Confirmar instalação
kind version
kubectl version --client
```

> ⚠️ O Docker Desktop precisa estar rodando antes de criar o cluster.

### Subindo o cluster

```bash
# 1. Cria o cluster local
kind create cluster --name pedidos-veloz

# 2. Confirma que o nó está Ready
kubectl get nodes

# 3. Cria o namespace
kubectl create namespace pedidos-veloz

# 4. Aplica os manifests na ordem correta
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/hpa/

# 5. Verifica os pods (aguarda todos ficarem Running)
kubectl get pods -n pedidos-veloz

# 6. Acessa o gateway via port-forward
kubectl port-forward svc/api-gateway-svc 8080:80 -n pedidos-veloz
```

> ⚠️ Substitua `amisori` nos arquivos de deployment pelo seu usuário do Docker Hub antes de aplicar, ou faça o build local com `kind load docker-image`.

### Resultado esperado

```
NAME                                    READY   STATUS    RESTARTS   AGE
api-gateway-deployment-xxx              1/1     Running   0          2m
api-gateway-deployment-yyy              1/1     Running   0          2m
estoque-deployment-xxx                  1/1     Running   0          2m
estoque-deployment-yyy                  1/1     Running   0          2m
pagamentos-deployment-xxx               1/1     Running   0          2m
pagamentos-deployment-yyy               1/1     Running   0          2m
pedidos-deployment-xxx                  1/1     Running   0          2m
pedidos-deployment-yyy                  1/1     Running   0          2m
postgres-deployment-xxx                 1/1     Running   0          2m
```

---

## CI/CD (GitHub Actions)

O pipeline executa automaticamente em:
- **Pull Request para main:** lint + testes
- **Push na main:** lint + testes + build + push de imagens + deploy

### Jobs do pipeline

| Job | Ferramenta | Condição | O que valida |
|-----|-----------|----------|-------------|
| Lint | Ruff | Sempre | Qualidade e estilo do código |
| Testes | pytest + PostgreSQL | Após Lint | Testes com banco real |
| Build & Push | Docker Buildx | Só main | Publica 4 imagens no Docker Hub |
| Deploy | kubectl | Só main + aprovação | Rolling Update no cluster |

### Secrets necessários no repositório GitHub

| Secret | Descrição |
|--------|-----------|
| `DOCKERHUB_USERNAME` | Usuário do Docker Hub |
| `DOCKERHUB_TOKEN` | Token de acesso gerado em hub.docker.com → Security |
| `KUBECONFIG` | kubeconfig em base64 para o cluster de produção |

Configure em: **Settings → Secrets and variables → Actions → New repository secret**

---

## Infraestrutura como Código (Terraform)

Esqueleto para provisionar cluster GKE no Google Cloud Platform.

```bash
cd terraform

# Inicializa os providers
terraform init

# Visualiza o plano sem aplicar
terraform plan -var="project_id=SEU_PROJECT_ID"

# Aplica a infraestrutura
terraform apply -var="project_id=SEU_PROJECT_ID"

# Configura o kubeconfig após o apply
gcloud container clusters get-credentials pedidos-veloz-cluster \
  --region us-central1 --project SEU_PROJECT_ID
```

---

## Observabilidade

| Pilar | Ferramentas | Implementação |
|-------|-------------|---------------|
| **Métricas** | Prometheus + Grafana | FastAPI expõe `/metrics` via `prometheus-fastapi-instrumentator` |
| **Logs** | Fluentd + Loki | Logs estruturados em stdout — padrão 12-Factor fator XI |
| **Tracing** | OpenTelemetry + Jaeger | trace IDs propagados via headers HTTP entre todos os serviços |

---

## Estratégia de Deploy

**Rolling Update** com `maxUnavailable: 0` e `maxSurge: 1`:
- Novo Pod sobe e aguarda aprovação da readinessProbe
- Somente após aprovação o Pod antigo é removido
- **Zero downtime garantido** sem infraestrutura duplicada

## Escalabilidade Automática (HPA)

| Serviço | Mín réplicas | Máx réplicas | Trigger |
|---------|-------------|-------------|---------|
| api-gateway | 2 | 10 | CPU > 60% |
| pedidos | 2 | 8 | CPU > 70% |
| pagamentos | 2 | 6 | CPU > 70% |

---

## Decisões Arquiteturais

**Rolling Update vs Blue/Green/Canary:** Rolling Update é a estratégia nativa do Kubernetes, suficiente para o MVP com zero downtime via `maxUnavailable: 0`. Blue/Green adicionaria custo de infraestrutura duplicada desnecessário neste estágio.

**Banco compartilhado (trade-off documentado):** para o MVP acadêmico, um único PostgreSQL foi adotado para reduzir complexidade. O padrão correto em produção é *Database per Service* — próximo passo evolutivo da arquitetura.

**Mensageria (RabbitMQ):** desacopla Pedidos de Estoque e Pagamentos via eventos (`PedidoCriado`), eliminando dependências síncronas que propagariam falhas em cascata.

**GKE via Terraform:** plano de controle gerenciado com Workload Identity, eliminando chaves JSON de serviço. IaC garante reprodutibilidade e rastreabilidade via controle de versão.

---

## Estrutura do Repositório

```
pedidos-veloz/
├── services/
│   ├── api-gateway/        # Dockerfile + main.py + requirements.txt
│   ├── pedidos/            # Dockerfile + main.py + requirements.txt
│   ├── pagamentos/         # Dockerfile + main.py + requirements.txt
│   └── estoque/            # Dockerfile + main.py + requirements.txt
├── k8s/
│   ├── deployments/
│   │   ├── pedidos-deployment.yaml
│   │   ├── outros-deployments.yaml   # gateway, pagamentos, estoque
│   │   └── postgres-k8s.yaml         # PostgreSQL para o cluster
│   ├── services/
│   │   └── services.yaml
│   ├── configmaps/
│   │   └── app-config.yaml
│   ├── secrets/
│   │   └── app-secrets.yaml
│   └── hpa/
│       └── hpa.yaml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── modules/k8s-cluster/
│       └── main.tf
├── tests/
│   └── test_pedidos.py
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```
