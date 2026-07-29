# Ambiente production: referencia os modulos com os valores reais do
# Edge Node itcenter-edge-01. Ver infra/terraform/README.md para o runbook
# de descoberta e a ordem obrigatoria de import (nunca destroy/recreate).

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

module "network" {
  source = "../../modules/network"

  compartment_id           = var.compartment_id
  vcn_display_name         = var.vcn_display_name
  vcn_cidr_block           = var.vcn_cidr_block
  vcn_dns_label            = var.vcn_dns_label
  public_subnet_cidr       = var.public_subnet_cidr
  public_subnet_dns_label  = var.public_subnet_dns_label
  private_subnet_cidr      = var.private_subnet_cidr
  private_subnet_dns_label = var.private_subnet_dns_label
  ingress_security_rules   = var.ingress_security_rules
  freeform_tags            = var.freeform_tags
}

module "compute" {
  source = "../../modules/compute"

  compartment_id             = var.compartment_id
  availability_domain        = var.availability_domain
  display_name               = var.instance_display_name
  shape                      = var.instance_shape
  shape_config               = var.instance_shape_config
  subnet_id                  = module.network.public_subnet_id
  image_id                   = var.instance_image_id
  assign_public_ip           = var.instance_assign_public_ip
  ssh_authorized_keys        = var.instance_ssh_authorized_keys
  enable_bootstrap_user_data = false
  freeform_tags              = var.freeform_tags
}
