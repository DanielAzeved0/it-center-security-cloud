# Modulo compute: instancia do Edge Node (itcenter-edge-01).
#
# Assim como o modulo network, nada aqui e criado do zero: a instancia ja
# roda em producao com dados reais e entra via "terraform import"
# (ver infra/terraform/README.md). O user_data de bootstrap fica desligado
# por padrao porque cloud-init nao reexecuta em uma instancia ja iniciada e
# ativa-lo aqui nao teria efeito nela — a variavel existe para uma VM nova
# ou um cenario de recuperacao de desastre.

resource "oci_core_instance" "edge_node" {
  compartment_id      = var.compartment_id
  availability_domain = var.availability_domain
  display_name        = var.display_name
  shape               = var.shape
  freeform_tags       = var.freeform_tags

  dynamic "shape_config" {
    for_each = var.shape_config == null ? [] : [var.shape_config]
    content {
      ocpus         = shape_config.value.ocpus
      memory_in_gbs = shape_config.value.memory_in_gbs
    }
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = var.assign_public_ip
  }

  source_details {
    source_type = "image"
    source_id   = var.image_id
  }

  metadata = merge(
    {
      ssh_authorized_keys = var.ssh_authorized_keys
    },
    var.enable_bootstrap_user_data ? {
      user_data = var.bootstrap_user_data_base64
    } : {}
  )

  lifecycle {
    prevent_destroy = true

    ignore_changes = [
      source_details,
    ]
  }
}
