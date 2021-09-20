variable "project_name" {
   description = "The project ID where all resources will be launched."
  type = string
}

variable "etherscan_api_key" {
  type = string
}

variable "web3_http_provider" {
  type = string
}

variable "email_user" {
  type = string
}

variable "email_pwd" {
  type = string
}

variable "region" {
  description = "The location region to deploy"
  type        = string
}

variable "zone" {
  description = "The location zone to deploy "
  type        = string
}
