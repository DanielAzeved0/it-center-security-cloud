output "instance_id" {
  description = "OCID da instancia itcenter-edge-01."
  value       = oci_core_instance.edge_node.id
}

output "public_ip" {
  description = "IP publico atual da instancia (conferir se e reservado ou efemero antes de depender dele em DNS)."
  value       = oci_core_instance.edge_node.public_ip
}

output "private_ip" {
  description = "IP privado da instancia."
  value       = oci_core_instance.edge_node.private_ip
}
