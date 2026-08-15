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

## Usuario IAM e policy de escopo minimo

O usuario `terraform-provisioner` e o grupo que o contem sao criados manualmente no Console OCI (Identity & Security > Domains > Users/Groups) — nao ha automacao para essa etapa, pois exige privilegio administrativo.

Policy sugerida, restrita ao compartment do Edge Node (substituir `<nome-do-compartment>` pelo valor real, descoberto na secao seguinte):

```text
Allow group TerraformProvisioners to inspect all-resources in compartment <nome-do-compartment>
Allow group TerraformProvisioners to manage virtual-network-family in compartment <nome-do-compartment>
Allow group TerraformProvisioners to manage instance-family in compartment <nome-do-compartment>
Allow group TerraformProvisioners to use volume-family in compartment <nome-do-compartment>
```

Motivo do escopo:

```text
inspect all-resources        -> necessario para "terraform plan"/"import" enxergarem qualquer recurso do compartment sem conceder escrita
manage virtual-network-family -> VCN, subnets, internet gateway, route table, security list (modulo network)
manage instance-family        -> a instancia itcenter-edge-01 (modulo compute)
use volume-family              -> volume de boot da instancia, sem permissao de apagar volumes por engano
```

Nao conceder `manage` sobre `all-resources`, nem qualquer permissao de IAM, Object Storage (fora do bucket de state, criado depois) ou outros compartments. A chave de API do usuario e gerada no Console apos a criacao e entregue fora do repositorio (variavel de ambiente local ou gerenciador de segredos).

## Descoberta dos parametros reais (rodar localmente, somente leitura)

Estes comandos usam a `oci` CLI configurada com a chave do `terraform-provisioner` (ou uma sessao com permissao de leitura equivalente) e nao alteram nada. Rode localmente e registre o resultado — nenhum deles esta disponivel no ambiente onde este repositorio e editado.

```bash
# Compartment (assumindo que o Edge Node esta no root compartment do tenancy; ajustar se houver compartment dedicado)
oci iam compartment list --compartment-id-in-subtree true --all

# Availability domains da regiao configurada
oci iam availability-domain list

# Instancia itcenter-edge-01: OCID, shape e availability-domain
oci compute instance list --compartment-id <compartment-ocid> --display-name itcenter-edge-01

# Detalhe do shape e da configuracao da instancia encontrada acima
oci compute instance get --instance-id <instance-ocid>

# VCNs do compartment
oci network vcn list --compartment-id <compartment-ocid>

# Subnets, internet gateway, route table e security list da VCN encontrada acima
oci network subnet list --compartment-id <compartment-ocid> --vcn-id <vcn-ocid>
oci network internet-gateway list --compartment-id <compartment-ocid> --vcn-id <vcn-ocid>
oci network route-table list --compartment-id <compartment-ocid> --vcn-id <vcn-ocid>
oci network security-list list --compartment-id <compartment-ocid> --vcn-id <vcn-ocid>

# IP publico: confirmar se e reservado (lifetime "RESERVED") ou efemero (lifetime "EPHEMERAL")
oci network public-ip list --compartment-id <compartment-ocid> --scope REGION
```

Registrar o resultado (compartment OCID, shape, availability domain, regiao, todos os OCIDs de rede, `lifetime` do IP publico) em `infra/terraform/environments/production/terraform.tfvars` (nunca versionado — ver `terraform.tfvars.example`). Se o IP publico aparecer com `lifetime: EPHEMERAL`, ele nao deve ser referenciado como recurso `oci_core_public_ip` importavel isolado — nesse caso, reservar o IP antes de prosseguir com qualquer import, para nao arriscar troca-lo em um `apply` futuro.

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

O bucket de state e criado manualmente uma unica vez fora do Terraform (problema do ovo e da galinha). Runbook completo de migracao:

1. Criar o bucket manualmente (uma unica vez, fora do Terraform), com versionamento habilitado:
   ```bash
   oci os bucket create --compartment-id <compartment-ocid> --name itcenter-terraform-state --versioning Enabled
   ```
2. Descobrir o namespace do tenancy (usado no endpoint S3-compativel):
   ```bash
   oci os ns get
   ```
3. Gerar uma Customer Secret Key (par access key/secret key, formato S3) para o usuario `terraform-provisioner` no Console OCI: Identity & Security > Domains > Users > `terraform-provisioner` > Customer Secret Keys > Generate Secret Key. O secret so e mostrado uma vez — guardar fora do repositorio.
4. Copiar `backend.hcl.example` para `backend.hcl` (gitignored) dentro de `infra/terraform/environments/production/` e preencher `bucket`, `region` e o `endpoints.s3` com o namespace real descoberto no passo 2.
5. Exportar as credenciais da Customer Secret Key como variaveis de ambiente (nunca dentro de `backend.hcl`):
   ```bash
   export AWS_ACCESS_KEY_ID="<access key>"
   export AWS_SECRET_ACCESS_KEY="<secret key>"
   ```
6. Migrar o state local para o bucket:
   ```bash
   cd infra/terraform/environments/production
   terraform init -migrate-state -backend-config=backend.hcl
   ```
7. Confirmar que o state remoto reflete exatamente o state local anterior:
   ```bash
   terraform plan
   ```
   Deve retornar `No changes.` — qualquer diff aqui indica migracao incompleta, nao um problema de infraestrutura real.
8. So depois de confirmado o `plan` limpo, mover o `terraform.tfstate` local antigo para fora do diretorio do projeto (backup manual), nunca apagar sem essa confirmacao.

## Comandos usuais

```bash
cd infra/terraform/environments/production
terraform init
terraform plan
terraform apply
terraform output
```

## Execucao real (2026-08-04)

O import descrito acima foi executado com sucesso contra producao. Notas para quem for repetir um processo parecido (nova VM, disaster recovery, ou outro ambiente):

```text
Provider oracle/oci ~> 5.0 resolveu para 5.47.0. Os modulos (network/compute)
precisam de um versions.tf proprio declarando source = "oracle/oci" - sem
isso o Terraform resolve "oci" para o namespace legado hashicorp/oci dentro
dos modulos (ver "terraform providers" para diagnosticar isso).

No provider 5.x, oci_core_instance.source_details usa o argumento
source_id, nao image_id (o nome usado originalmente no modulo estava
desatualizado/errado e so foi descoberto no primeiro terraform plan real).

A VCN foi criada pelo "VCN Wizard" da Oracle: isso significa NAT Gateway,
Service Gateway, e route tables/security lists dedicadas por subnet, nao so
os recursos "basicos" descritos na secao Escopo. Ver docs/architecture/IAC.md
("Descoberta real") e docs/architecture/NETWORK.md para o que foi encontrado
e como o modulo network foi ajustado (variaveis private_route_table_id e
private_security_list_ids).

A regra "SSH" da security list default nao tinha description preenchida
(so HTTP/HTTPS tinham) - o tipo da variavel ingress_security_rules precisou
virar description = optional(string).

O IP publico de producao (147.15.78.220) e EPHEMERAL, nao RESERVED -
confirmado, decisao foi nao reservar agora (ver IAC.md).

Ao final do import, sobrou so um diff de freeform_tags (tag "VCN" que o
Wizard deixa em cada recurso de rede). Resolvido com um terraform apply
minimo (0 add, 6 change, 0 destroy) normalizando para freeform_tags = {} -
plan final confirmado como "No changes.".
```

## O que nunca comitar

```text
.terraform/
*.tfstate*
terraform.tfvars (valores reais)
```

`terraform.tfvars.example` com placeholders e comitado normalmente. `.terraform.lock.hcl` tambem deve ser comitado (fixa a versao do provider).
