# Modulo network: VCN, subnets, internet gateway, route table e security list
# do Edge Node itcenter-edge-01. Ciclo de vida separado do modulo compute
# porque trocar o shape/imagem da instancia nunca deve arriscar tocar a rede.
#
# Nenhum destes recursos e criado do zero aqui: todos ja existem em producao
# e entram via "terraform import" (ver infra/terraform/README.md). Os valores
# default abaixo devem ser conferidos contra o output real da oci CLI antes
# do import, ajustando ate "terraform plan" mostrar zero diferenca.

resource "oci_core_vcn" "this" {
  compartment_id = var.compartment_id
  display_name   = var.vcn_display_name
  cidr_blocks    = [var.vcn_cidr_block]
  dns_label      = var.vcn_dns_label
  freeform_tags  = var.freeform_tags

  lifecycle {
    prevent_destroy = true
  }
}

resource "oci_core_internet_gateway" "this" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "itcenter-igw"
  enabled        = true
  freeform_tags  = var.freeform_tags
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "itcenter-public-rt"
  freeform_tags  = var.freeform_tags

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.this.id
  }
}

resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.this.id
  display_name   = "itcenter-public-sl"
  freeform_tags  = var.freeform_tags

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  dynamic "ingress_security_rules" {
    for_each = var.ingress_security_rules
    content {
      protocol    = ingress_security_rules.value.protocol
      source      = ingress_security_rules.value.source
      description = ingress_security_rules.value.description

      tcp_options {
        min = ingress_security_rules.value.tcp_port
        max = ingress_security_rules.value.tcp_port
      }
    }
  }
}

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  display_name               = "itcenter-public-subnet"
  cidr_block                 = var.public_subnet_cidr
  dns_label                  = var.public_subnet_dns_label
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
  prohibit_public_ip_on_vnic = false
  freeform_tags              = var.freeform_tags
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.this.id
  display_name               = "itcenter-private-subnet"
  cidr_block                 = var.private_subnet_cidr
  dns_label                  = var.private_subnet_dns_label
  route_table_id             = oci_core_vcn.this.default_route_table_id
  security_list_ids          = [oci_core_vcn.this.default_security_list_id]
  prohibit_public_ip_on_vnic = true
  freeform_tags              = var.freeform_tags
}
