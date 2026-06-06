output "homepage_reverse_proxy_domain" {
  description = "NetBird reverse proxy domain for Homepage."
  value       = try(netbird_reverse_proxy_service.homepage[0].domain, null)
}

output "homepage_reverse_proxy_hostname" {
  description = "Expected public hostname for Homepage."
  value       = try(netbird_reverse_proxy_service.homepage[0].domain, null)
}

output "homepage_reverse_proxy_service_id" {
  description = "NetBird reverse proxy service ID for Homepage."
  value       = try(netbird_reverse_proxy_service.homepage[0].id, null)
}

output "homepage_target_peer_id" {
  description = "Resolved NetBird peer ID for gezi-dev."
  value       = data.netbird_peer.gezi_dev.id
}
