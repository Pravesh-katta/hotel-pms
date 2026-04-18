# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "main" {
  name             = "hotel-pms-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    disk_size         = 10
    disk_autoresize   = true
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled = false
      # Private IP via VPC (or use Cloud SQL Auth Proxy)
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "pms" {
  name     = "hotel_pms"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "pms" {
  name     = "hotel_pms"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}
