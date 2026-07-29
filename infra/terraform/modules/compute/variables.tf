variable "compartment_id" {
  description = "OCID do compartment onde a instancia itcenter-edge-01 ja existe."
  type        = string
}

variable "availability_domain" {
  description = "Availability domain real da instancia (descoberto via oci CLI, ver infra/terraform/README.md)."
  type        = string
}

variable "display_name" {
  description = "Nome de exibicao da instancia existente."
  type        = string
  default     = "itcenter-edge-01"
}

variable "shape" {
  description = "Shape real da instancia (ex.: VM.Standard.E2.1.Micro ou VM.Standard.A1.Flex), descoberto via oci CLI."
  type        = string
}

variable "shape_config" {
  description = "Configuracao de OCPU/memoria para shapes flexiveis (VM.Standard.A1.Flex). Deixar null para shapes fixos."
  type = object({
    ocpus         = number
    memory_in_gbs = number
  })
  default = null
}

variable "subnet_id" {
  description = "OCID da subnet publica (saida do modulo network) onde a instancia ja esta conectada."
  type        = string
}

variable "image_id" {
  description = "OCID da imagem de boot real da instancia existente."
  type        = string
}

variable "assign_public_ip" {
  description = "Se a instancia usa IP publico (reservado ou efemero, ver README sobre como confirmar o lifetime real antes do import)."
  type        = bool
  default     = true
}

variable "ssh_authorized_keys" {
  description = "Chave publica SSH ja associada a instancia (metadata authorized_keys), para bater com o valor real antes do import."
  type        = string
}

variable "enable_bootstrap_user_data" {
  description = "Ativa o user_data de bootstrap (infra/bootstrap/, ver docs/deployment/BOOTSTRAP.md). Desligado por padrao: a instancia ja esta viva e cloud-init nao reexecuta; so usar em uma VM nova ou recuperacao de desastre."
  type        = bool
  default     = false
}

variable "bootstrap_user_data_base64" {
  description = "Conteudo do bootstrap ja codificado em base64, usado somente quando enable_bootstrap_user_data = true."
  type        = string
  default     = null
}

variable "freeform_tags" {
  description = "Tags de identificacao da instancia."
  type        = map(string)
  default     = {}
}
