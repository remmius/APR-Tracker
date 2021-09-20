terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.77.0"
    }
  }
  #backend "gcs"{
  #  bucket      = "crypto_apr_tracker_state"
  #  prefix      = "dev"
  #  credentials = "apy-tracker-key.json"
  #}
}
provider "google" {
  credentials = file("apy-tracker-key.json")
  project     = var.project_name
  region      = var.region
  zone        = var.zone
}

module "project_services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "11.1.1"
  project_id    = var.project_name
  activate_apis =  [
   "cloudresourcemanager.googleapis.com",
   "iamcredentials.googleapis.com",
   "iam.googleapis.com",
   "cloudfunctions.googleapis.com",
   "cloudbuild.googleapis.com",
   "cloudscheduler.googleapis.com",
  ]

  disable_services_on_destroy = false
  disable_dependent_services  = false
}
#Bucket
resource "google_storage_bucket" "apr_tracker_state" {
  name     = "crypto_apr_tracker_state"
  location = var.region
}

#Bucket
resource "google_storage_bucket" "apr_tracker_data" {
  name     = "crypto_apr_tracker_data"
  location = var.region
}
#Bucket
resource "google_storage_bucket" "apr_tracker_bucket" {
  name     = "crypto_apr_tracker_src"
  location = var.region
}

resource "google_service_account" "service_account" {
  account_id   = "cloud-function-invoker"
  display_name = "Cloud Function Tutorial Invoker Service Account"
}

#Lambda
#Generate python package
data "archive_file" "get_apr_data_src" {
  type        = "zip"
  source_dir  = "../src/get_apr_data" # Directory where your Python source code is
  output_path = "../generated/get_apr_data/src.zip"
}

#Upload python package into bucket
resource "google_storage_bucket_object" "get_apr_data_func" {  
  name   = "${data.archive_file.get_apr_data_src.output_md5}.zip"
  bucket = google_storage_bucket.apr_tracker_bucket.name
  source = "${path.root}/../generated/get_apr_data/src.zip"
}

#Setup Lambda
resource "google_cloudfunctions_function" "get_apr_data_func" {
  name        = "get_apr_data"
  description = "Gets apr-values of different crypt-contracts"
  runtime     = "python37"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.apr_tracker_bucket.name
  source_archive_object = google_storage_bucket_object.get_apr_data_func.name
  trigger_http          = true
  entry_point           = "get_apr_data"
  timeout               = 120
  labels                = {}
  environment_variables = {
    ETHERSCAN-API-KEY   = var.etherscan_api_key,
    WEB3_HTTP_PROVIDER  = var.web3_http_provider,
    DATA_BUCKET         = google_storage_bucket.apr_tracker_data.name,
  }
}

resource "google_cloudfunctions_function_iam_member" "get_apr_data_invoker" {
  project        = google_cloudfunctions_function.get_apr_data_func.project
  region         = google_cloudfunctions_function.get_apr_data_func.region
  cloud_function = google_cloudfunctions_function.get_apr_data_func.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.service_account.email}"
}

#Sheduler
resource "google_cloud_scheduler_job" "job_get_apr_data" {
  name             = "trigger-get_apr_data"
  description      = "Trigger the ${google_cloudfunctions_function.get_apr_data_func.name} Cloud Function"
  schedule         = "10 01 * * *" # Every Tue and Fri
  time_zone        = "Europe/Dublin"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    headers= {}
    uri         = google_cloudfunctions_function.get_apr_data_func.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.service_account.email
      audience = google_cloudfunctions_function.get_apr_data_func.https_trigger_url
    }
  }
}

#Generate python package
data "archive_file" "send_apr_data_src" {
  type        = "zip"
  source_dir  = "../src/send_apr_data" # Directory where your Python source code is
  output_path = "../generated/send_apr_data/src.zip"
}

#Upload python package into bucket
resource "google_storage_bucket_object" "send_apr_data_func" {  
  name   = "${data.archive_file.send_apr_data_src.output_md5}.zip"
  bucket = google_storage_bucket.apr_tracker_bucket.name
  source = "${path.root}/../generated/send_apr_data/src.zip"
}

#Setup Lambda
resource "google_cloudfunctions_function" "send_apr_data_func" {
  name        = "send_apr_data"
  description = "Gets apr-values of different crypt-contracts"
  runtime     = "python37"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.apr_tracker_bucket.name
  source_archive_object = google_storage_bucket_object.send_apr_data_func.name
  trigger_http          = true
  entry_point           = "send_apr_data"
  timeout               = 120
  labels                = {}
  environment_variables = {
    DATA_BUCKET         = google_storage_bucket.apr_tracker_data.name,
    EMAIL_USER          = var.email_user,
    EMAIL_PWD           = var.email_pwd
  }
}

resource "google_cloudfunctions_function_iam_member" "send_apr_data_invoker" {
  project        = google_cloudfunctions_function.send_apr_data_func.project
  region         = google_cloudfunctions_function.send_apr_data_func.region
  cloud_function = google_cloudfunctions_function.send_apr_data_func.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.service_account.email}"
}

#Sheduler
resource "google_cloud_scheduler_job" "job_send_apr_data" {
  name             = "trigger-send_apr_data"
  description      = "Trigger the ${google_cloudfunctions_function.send_apr_data_func.name} Cloud Function"
  schedule         = "20 01 * * 2,5" # Every Tue and Fri
  time_zone        = "Europe/Dublin"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    headers= {}
    uri         = google_cloudfunctions_function.send_apr_data_func.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.service_account.email
      audience = google_cloudfunctions_function.send_apr_data_func.https_trigger_url
    }
  }
}

#Upload python package into bucket
resource "google_storage_bucket_object" "history_apy" {  
  name   = "history_apy.csv"
  bucket = google_storage_bucket.apr_tracker_data.name
  source = "${path.root}/../history_apy.csv"
}
