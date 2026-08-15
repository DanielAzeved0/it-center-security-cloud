terraform {
  required_version = ">= 1.6"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }

  # Backend remoto S3-compativel apontando para o bucket de state em OCI
  # Object Storage (ver docs/architecture/IAC.md e infra/terraform/README.md,
  # secao "State"). Configuracao parcial de proposito: nenhum valor real
  # (bucket, namespace, endpoint, chaves) fica hardcoded aqui. Preencher via
  # infra/terraform/environments/production/backend.hcl (gitignored, copiar
  # de backend.hcl.example) e rodar:
  #
  #   terraform init -migrate-state -backend-config=backend.hcl
  #
  # Antes de existir o backend.hcl preenchido, "terraform init" continua
  # usando o state local (terraform.tfstate) normalmente.
  backend "s3" {}
}
