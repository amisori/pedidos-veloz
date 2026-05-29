# ============================================================
# Infraestrutura como Código — Pedidos Veloz
# Provider: Google Cloud Platform (GKE)
# Justificativa: GKE oferece Kubernetes gerenciado com
# autopilot, integração nativa com IAM e free tier generoso.
# ============================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Backend remoto para state compartilhado em equipe
  # Em produção: descomente e configure o bucket GCS
  # backend "gcs" {
  #   bucket = "pedidos-veloz-tfstate"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================================
# Módulo: Cluster GKE
# ============================================================
module "gke_cluster" {
  source = "./modules/k8s-cluster"

  project_id   = var.project_id
  region       = var.region
  cluster_name = var.cluster_name
  node_count   = var.node_count
  machine_type = var.machine_type
}

# ============================================================
# Outputs úteis após o apply
# ============================================================
output "cluster_name" {
  value       = module.gke_cluster.cluster_name
  description = "Nome do cluster GKE provisionado"
}

output "cluster_endpoint" {
  value       = module.gke_cluster.endpoint
  description = "Endpoint da API do Kubernetes"
  sensitive   = true
}

output "kubeconfig_command" {
  value       = "gcloud container clusters get-credentials ${var.cluster_name} --region ${var.region} --project ${var.project_id}"
  description = "Comando para configurar o kubeconfig local"
}
