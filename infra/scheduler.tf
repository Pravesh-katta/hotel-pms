# Cloud Scheduler for night audit
resource "google_cloud_scheduler_job" "night_audit" {
  name      = "hotel-pms-night-audit"
  region    = var.region
  schedule  = "30 0 * * *"  # 00:30 IST daily
  time_zone = "Asia/Kolkata"

  http_target {
    uri         = "${google_cloud_run_v2_service.web.uri}/api/tasks/night-audit/"
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}

# Service account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "hotel-pms-scheduler"
  display_name = "Hotel PMS Scheduler"
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_service.web.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}
