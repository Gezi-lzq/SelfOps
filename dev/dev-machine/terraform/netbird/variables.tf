variable "netbird_token" {
  description = "NetBird Management PAT. Prefer NB_PAT environment variable."
  type        = string
  sensitive   = true
  default     = null
}

variable "netbird_management_url" {
  description = "NetBird Management API URL. Defaults to NetBird Cloud."
  type        = string
  default     = "https://api.netbird.io"
}

variable "netbird_tenant_account" {
  description = "Optional NetBird tenant account ID."
  type        = string
  default     = null
}

variable "gezi_dev_peer_name" {
  description = "NetBird peer name for the development machine."
  type        = string
  default     = "gezi-dev"
}

variable "homepage_service_name" {
  description = "NetBird Reverse Proxy service name for Homepage."
  type        = string
  default     = "gezi-home"
}

variable "homepage_proxy_password" {
  description = "Password required by NetBird Reverse Proxy before reaching Homepage."
  type        = string
  sensitive   = true
}

