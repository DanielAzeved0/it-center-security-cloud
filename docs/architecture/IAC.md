# Infrastructure as Code (Terraform)

Este documento descreve como a camada de infraestrutura Oracle Cloud do IT Center Security Cloud passa a ser provisionada e versionada via Terraform, a partir do ADR-024.

## Visao geral

```mermaid
flowchart TD
    tf[Terraform] --> provider[Provider oci]
    provider --> vcn[VCN 10.0.0.0/16]
    provider --> subnets[Subnets publica e privada]
    provider --> seclist[Security List]
    provider --> instance[Instancia itcenter-edge-01]
    instance --> docker[Docker Engine]
    docker --> network[itcenter-network]
    network --> nginx[Nginx]
    network --> frontend[Next.js]
    network --> backend[FastAPI]
    network --> postgres[PostgreSQL]
```

O Terraform provisiona somente o que existe **abaixo do sistema operacional e da rede**. Docker Compose, Nginx, backend, frontend, PostgreSQL e os scripts de `infra/scripts/` continuam exatamente como estao hoje e nao sao geridos pelo Terraform.

## Escopo

Provisionado por Terraform:

```text
VCN
Subnet publica
Subnet privada
Internet Gateway
Route Table
Security List
Instancia de computacao (itcenter-edge-01)
```

Fora do escopo do Terraform:

```text
Docker Compose (infra/docker-compose.production.yml)
Scripts de deploy, backup, restore, rollback (infra/scripts/)
Certificados TLS (Certbot)
Migrations e dados do PostgreSQL
NAT Gateway e Service Gateway (existem, ver secao "Descoberta real" abaixo)
```

## Mapeamento com as camadas da arquitetura

A divisao de camadas completa esta em `docs/architecture/INFRASTRUCTURE.md` — nao duplicada aqui. O Terraform e responsavel apenas pela Infrastructure Layer (VCN, subnets, security list, instancia, volume de boot); as demais camadas continuam sob Docker Compose, como ja documentado la.

## Modulos

```text
infra/terraform/
├── modules/
│   ├── network/   VCN, subnets, internet gateway, route table, security list
│   └── compute/   instancia do Edge Node
└── environments/
    └── production/   referencia os modulos com os valores reais
```

Dois modulos pequenos, nao um por recurso individual: o ciclo de vida de rede e o ciclo de vida da instancia sao diferentes (trocar shape ou imagem da VM nunca deve arriscar tocar a VCN).

## Descoberta real (import executado em 2026-08-04)

A topologia completa descoberta via `oci` CLI (VCN criada pelo "VCN Wizard" da Oracle, NAT Gateway, Service Gateway, route tables e security lists dedicadas por subnet, IP publico efemero) esta descrita em `docs/architecture/NETWORK.md` — nao duplicada aqui. Implicacao para o Terraform:

```text
NAT Gateway e Service Gateway       -> fora do escopo (block_traffic = false desde a criacao, nada os toca)
Route table/security list privada   -> referenciadas por OCID via variavel (private_route_table_id, private_security_list_ids), nao geridas como recurso Terraform proprio
Route table/security list publica   -> geridas pelo Terraform (oci_core_route_table.public, oci_core_security_list.public), pois governam o trafego de entrada real do Edge Node
IP publico efemero                  -> mantido efemero por enquanto; risco detalhado na secao "Riscos" abaixo
```

## Introducao via import, nunca destroy/recreate

A VM `itcenter-edge-01` ja roda em producao com dados reais. A introducao do Terraform segue estritamente por `terraform import`, na ordem:

```text
1. VCN
2. Internet Gateway
3. Route Table
4. Security List
5. Subnet publica
6. Subnet privada
7. Instancia de computacao
8. IP publico (se reservado)
```

Regra: apos importar cada recurso, `terraform plan` precisa mostrar zero diferenca para aquele recurso antes de importar o proximo. So depois de todos os recursos importados o `terraform plan` completo precisa retornar `No changes.`. Nenhum `apply` de criacao e executado nesta introducao.

`lifecycle { prevent_destroy = true }` e aplicado na VCN e na instancia como trava adicional.

## Bootstrap e cloud-init

`docs/deployment/BOOTSTRAP.md` continua a fonte de verdade da preparacao do host. Os scripts `infra/bootstrap/{01-system,02-packages,03-directories,04-docker,05-firewall,bootstrap}.sh` estao implementados conforme essa especificacao. O `user_data` da instancia **ja viva** nao e alterado durante a introducao do Terraform, pois isso quebraria o `plan` zero-diff e cloud-init nao reexecuta em instancia ja iniciada.

O modulo `compute` expoe a variavel opcional `enable_bootstrap_user_data` (desligada por padrao, `bootstrap_user_data_base64` como conteudo) para ativar o bootstrap via `user_data`, reservada para uma futura VM nova ou cenario de recuperacao de desastre — nunca ativada em `environments/production` enquanto a instancia atual permanecer viva.

## State

```text
Fase inicial: local (reduz variaveis durante o import)
Fase alvo:    remoto, backend S3-compativel apontando para OCI Object Storage
```

O bucket de Object Storage e criado manualmente uma unica vez (Terraform nao pode gerenciar o bucket que guarda o proprio state). Versionamento do bucket habilitado como rede de seguranca adicional para o state. Configuracao do backend preparada como partial configuration (`backend "s3" {}` em `versions.tf` + `backend.hcl.example`, sem valores reais nem chaves versionados) — runbook completo de criacao do bucket, Customer Secret Key e `terraform init -migrate-state` em `infra/terraform/README.md`, secao "State".

**Migracao bloqueada desde 2026-08-15 (nao e apenas tarefa nao iniciada)**: ao retomar a EPIC 15 para criar o bucket e migrar o state, descobriu-se que (1) o unico usuario administrador da tenancy Oracle Cloud perdeu o MFA (celular antigo), sem fator de backup nem segundo administrador cadastrado — nenhuma acao de Console OCI ou `oci` CLI e possivel ate a conta ser recuperada; e (2) o `terraform.tfstate` e o `terraform.tfvars` reais do import de 2026-08-04 nao foram localizados (nem em `itcenter-edge-01` nem em copia conhecida), e a API key do usuario `terraform-provisioner` tambem foi dada como perdida. Ver `docs/deployment/KNOWN_ISSUES.md` ("Acesso ao Console Oracle Cloud bloqueado (MFA do administrador perdido)") e `docs/development/TASKS.md` (EPIC 15).

Ordem de desbloqueio necessaria antes de sequer poder migrar o state:

```text
1. Recuperar o acesso ao Console OCI (fator de backup, segundo administrador ja existente, ou Service Request ao suporte Oracle provando titularidade da tenancy)
2. Cadastrar um segundo administrador e um fator de MFA de backup, para nao repetir o bloqueio
3. Gerar uma API key nova para terraform-provisioner
4. Refazer a descoberta/import do Terraform do zero (infra/terraform/README.md), ja que o state de 2026-08-04 nao existe mais
5. So entao criar o bucket de Object Storage e rodar terraform init -migrate-state
```

## Secrets

```text
Usuario IAM dedicado: terraform-provisioner
Escopo: minimo, restrito ao compartment do Edge Node
Chave de API: fora da arvore do repositorio (nunca em infra/terraform/, mesmo gitignored)
```

## Riscos

```text
Recurso esquecido no import          -> Terraform tenta recriar/duplicar
State local corrompido por sync      -> pasta do projeto esta sob OneDrive
IP publico efemero (nao reservado)   -> confirmado EPHEMERAL em producao (2026-08-04); replace acidental da instancia trocaria o IP e quebraria o DNS - mitigado por nunca rodar apply de recriacao
Shape Always Free indisponivel       -> risco ao recriar a instancia numa recuperacao futura
Drift de versao do provider oci      -> comitar .terraform.lock.hcl
Acesso Console/oci CLI bloqueado (MFA do admin perdido, desde 2026-08-15) -> nenhuma acao administrativa na nuvem e possivel (bucket de state, rotacao de API key, disaster recovery da VM/rede); ver docs/deployment/KNOWN_ISSUES.md
terraform.tfstate/terraform.tfvars do import de 2026-08-04 nao localizados -> migracao de state bloqueada; sera necessario refazer a descoberta/import do zero com credenciais novas antes de migrar
```

Detalhes operacionais (comandos, runbook de import) ficam em `infra/terraform/README.md`. Decisao registrada em ADR-024 (`docs/development/DECISIONS.md`).
