# Autenticacao do provider oci (usuario IAM terraform-provisioner, ver README.md)

variable "tenancy_ocid" {
  description = "OCID do tenancy OCI."
  type        = string
}

variable "user_ocid" {
  description = "OCID do usuario terraform-provisioner."
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint da chave de API do usuario terraform-provisioner."
  type        = string
}

variable "private_key_path" {
  description = "Caminho local da chave privada da API, fora da arvore do repositorio."
  type        = string
}

variable "region" {
  description = "Regiao OCI onde o Edge Node roda (descoberta via oci CLI, ver README.md)."
  type        = string
}

# Compartment e rede (modulo network)

variable "compartment_id" {
  description = "OCID do compartment do Edge Node (descoberto via oci CLI, ver README.md)."
  type        = string
}

variable "vcn_display_name" {
  type    = string
  default = "itcenter-vcn"
}

variable "vcn_cidr_block" {
  type    = string
  default = "10.0.0.0/16"
}

variable "vcn_dns_label" {
  type    = string
  default = "itcentervcn"
}

variable "public_subnet_cidr" {
  type = string
}

variable "public_subnet_dns_label" {
  type    = string
  default = "itcenterpub"
}

variable "private_subnet_cidr" {
  type = string
}

variable "private_subnet_dns_label" {
  type    = string
  default = "itcenterpriv"
}

variable "ingress_security_rules" {
  description = "Regras de entrada reais da security list existente (preencher a partir do output de 'oci network security-list list')."
  type = list(object({
    protocol    = string
    source      = string
    description = optional(string)
    tcp_port    = number
  }))
  default = []
}

variable "private_route_table_id" {
  description = "OCID da route table real usada pela subnet privada (NAT Gateway + Service Gateway), descoberta via 'oci network route-table list'."
  type        = string
}

variable "private_security_list_ids" {
  description = "OCIDs das security lists reais usadas pela subnet privada, descobertas via 'oci network subnet list'."
  type        = list(string)
}

# Instancia (modulo compute)

variable "availability_domain" {
  type = string
}

variable "instance_display_name" {
  type    = string
  default = "itcenter-edge-01"
}

variable "instance_shape" {
  type = string
}

variable "instance_shape_config" {
  type = object({
    ocpus         = number
    memory_in_gbs = number
  })
  default = null
}

variable "instance_image_id" {
  type = string
}

variable "instance_assign_public_ip" {
  type    = bool
  default = true
}

variable "instance_ssh_authorized_keys" {
  type = string
}

variable "freeform_tags" {
  type = map(string)
  default = {
    project     = "it-center-security-cloud"
    managed_by  = "terraform"
    environment = "production"
  }
}
