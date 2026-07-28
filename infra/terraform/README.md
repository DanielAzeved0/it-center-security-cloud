# Terraform

Provisionamento versionado da infraestrutura Oracle Cloud do IT Center Security Cloud (VCN, subnets, security list e a instancia do Edge Node). Ver `docs/architecture/IAC.md` para a visao de arquitetura e `docs/development/DECISIONS.md` (ADR-024) para o contexto da decisao.

Este diretorio **nao** gerencia Docker Compose, Nginx, backend, frontend, PostgreSQL ou os scripts de `infra/scripts/` — esses continuam exatamente como estao hoje.

## Layout

```text
infra/terraform/
├── modules/
│   ├── network/   VCN, subnets, internet gateway, route table, security list
│   └── compute/   instancia do Edge Node
└── environments/
    └── production/   referencia os modulos com os valores reais do ambiente
```

## Pre-requisitos

```text
terraform >= 1.6
oci CLI configurado (~/.oci/config)
Usuario IAM dedicado "terraform-provisioner" com escopo minimo no compartment do Edge Node
```

A chave de API do usuario IAM fica fora da arvore do repositorio (nunca dentro de `infra/terraform/`, mesmo estando no `.gitignore`).

## Introducao segura (import, nunca destroy/recreate)

A instancia `itcenter-edge-01` ja roda em producao com dados reais. A sequencia abaixo e obrigatoria:

1. Descobrir via `oci` CLI (somente leitura) todos os OCIDs existentes: compartment, VCN, subnets, internet gateway, route table, security list, instancia e IP publico.
2. Escrever os recursos em `modules/network` e `modules/compute` espelhando o que ja existe.
3. `terraform init` (backend local nesta fase).
4. Para cada recurso, na ordem VCN -> Internet Gateway -> Route Table -> Security List -> Subnet publica -> Subnet privada -> Instancia -> IP publico:
   ```bash
   terraform import <endereco_do_recurso> <ocid>
   terraform plan
   ```
   Corrigir o `.tf` ate o `plan` mostrar zero diferenca para aquele recurso antes de importar o proximo.
5. So depois de todos os recursos importados, `terraform plan` completo precisa retornar `No changes.`.
6. Nenhum `terraform apply` de criacao e executado durante esta introducao.

## State

```text
Fase inicial: local (terraform.tfstate, gitignored)
Fase alvo:    backend remoto S3-compativel apontando para um bucket OCI Object Storage
```

O bucket de state e criado manualmente uma unica vez fora do Terraform (problema do ovo e da galinha). Migracao com:

```bash
terraform init -migrate-state
```

## Comandos usuais

```bash
cd infra/terraform/environments/production
terraform init
terraform plan
terraform apply
terraform output
```

## O que nunca comitar

```text
.terraform/
*.tfstate*
terraform.tfvars (valores reais)
```

`terraform.tfvars.example` com placeholders e comitado normalmente. `.terraform.lock.hcl` tambem deve ser comitado (fixa a versao do provider).
