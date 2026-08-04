variable "compartment_id" {
  description = "OCID do compartment onde a rede do Edge Node ja existe (descoberto via oci CLI, ver infra/terraform/README.md)."
  type        = string
}

variable "vcn_display_name" {
  description = "Nome de exibicao da VCN existente, para import por nome/tag."
  type        = string
  default     = "itcenter-vcn"
}

variable "vcn_cidr_block" {
  description = "CIDR da VCN existente."
  type        = string
  default     = "10.0.0.0/16"
}

variable "vcn_dns_label" {
  description = "DNS label da VCN existente."
  type        = string
  default     = "itcentervcn"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet publica existente (Nginx/Edge Node)."
  type        = string
}

variable "public_subnet_dns_label" {
  description = "DNS label da subnet publica existente."
  type        = string
  default     = "itcenterpub"
}

variable "private_subnet_cidr" {
  description = "CIDR da subnet privada existente."
  type        = string
}

variable "private_subnet_dns_label" {
  description = "DNS label da subnet privada existente."
  type        = string
  default     = "itcenterpriv"
}

variable "ingress_security_rules" {
  description = "Regras de entrada da security list existente, uma a uma, para reproduzir exatamente o que ja esta em producao antes do import (ex.: 22, 80, 443). Preencher com os valores reais descobertos via oci CLI."
  type = list(object({
    protocol    = string
    source      = string
    description = optional(string)
    tcp_port    = number
  }))
  default = []
}

variable "private_route_table_id" {
  description = "OCID da route table ja existente usada pela subnet privada (NAT Gateway + Service Gateway, criados pelo VCN Wizard da Oracle). Fora do escopo do Terraform (ADR-024) - apenas referenciada, nunca gerenciada."
  type        = string
}

variable "private_security_list_ids" {
  description = "OCIDs das security lists ja existentes usadas pela subnet privada. Fora do escopo do Terraform (ADR-024) - apenas referenciadas, nunca gerenciadas."
  type        = list(string)
}

variable "freeform_tags" {
  description = "Tags de identificacao dos recursos de rede."
  type        = map(string)
  default     = {}
}
