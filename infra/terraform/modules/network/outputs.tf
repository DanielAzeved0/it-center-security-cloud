output "vcn_id" {
  description = "OCID da VCN."
  value       = oci_core_vcn.this.id
}

output "public_subnet_id" {
  description = "OCID da subnet publica (onde a instancia do Edge Node roda)."
  value       = oci_core_subnet.public.id
}

output "private_subnet_id" {
  description = "OCID da subnet privada."
  value       = oci_core_subnet.private.id
}

output "internet_gateway_id" {
  description = "OCID do Internet Gateway."
  value       = oci_core_internet_gateway.this.id
}
