terraform {
  required_version = ">= 1.6.0"

  required_providers {
    netbird = {
      source  = "netbirdio/netbird"
      version = "0.0.9"
    }
  }
}

provider "netbird" {
  token          = var.netbird_token
  management_url = var.netbird_management_url
  tenant_account = var.netbird_tenant_account
}

data "netbird_peer" "gezi_dev" {
  name = var.gezi_dev_peer_name
}

data "netbird_reverse_proxy_domain" "free" {
  type = "free"
}

resource "netbird_reverse_proxy_service" "homepage" {
  count = var.enable_homepage_reverse_proxy ? 1 : 0

  name   = var.homepage_service_name
  domain = "${var.homepage_service_name}.${data.netbird_reverse_proxy_domain.free.domain}"

  enabled           = true
  pass_host_header  = true
  rewrite_redirects = true

  targets = [
    {
      target_id   = data.netbird_peer.gezi_dev.id
      target_type = "peer"
      protocol    = "http"
      port        = 80
      path        = "/"
      enabled     = true
    }
  ]

  auth = {
    password_auth = {
      enabled  = true
      password = var.homepage_proxy_password
    }
  }
}
