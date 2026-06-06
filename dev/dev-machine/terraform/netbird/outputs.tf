output "homepage_reverse_proxy_domain" {
  description = "NetBird reverse proxy base domain for Homepage."
  value       = netbird_reverse_proxy_service.homepage.domain
}

output "homepage_reverse_proxy_hostname" {
  description = "Expected public hostname for Homepage."
  value       = "${var.homepage_service_name}.${netbird_reverse_proxy_service.homepage.domain}"
}

output "homepage_reverse_proxy_service_id" {
  description = "NetBird reverse proxy service ID for Homepage."
  value       = netbird_reverse_proxy_service.homepage.id
}

output "homepage_target_peer_id" {
  description = "Resolved NetBird peer ID for gezi-dev."
  value       = data.netbird_peer.gezi_dev.id
}
