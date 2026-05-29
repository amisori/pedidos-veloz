variable "project_id" {
  description = "ID do projeto no Google Cloud"
  type        = string
}

variable "region" {
  description = "Região GCP onde o cluster será provisionado"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Nome do cluster Kubernetes"
  type        = string
  default     = "pedidos-veloz-cluster"
}

variable "node_count" {
  description = "Número de nós no node pool"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Tipo de máquina dos nós do cluster"
  type        = string
  default     = "e2-standard-2"   # 2 vCPUs, 8GB RAM — adequado para MVP
}
