variable "project_id"   { type = string }
variable "region"       { type = string }
variable "cluster_name" { type = string }
variable "node_count"   { type = number }
variable "machine_type" { type = string }

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region

  # Remove o node pool padrão para usar node pool gerenciado separado
  remove_default_node_pool = true
  initial_node_count       = 1

  # Habilita Workload Identity (boa prática de segurança)
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 50
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }

  # Permite atualização de nós sem destruir o pool
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

output "cluster_name" { value = google_container_cluster.primary.name }
output "endpoint"     { value = google_container_cluster.primary.endpoint }
