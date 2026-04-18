output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.web.uri
}

output "cloud_sql_connection" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "artifact_registry" {
  description = "Docker image registry"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/hotel-pms"
}
