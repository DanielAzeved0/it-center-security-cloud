# ASSET_POLICY.md

# Política de Ativos

## Objetivo

Definir quais ativos, softwares e comportamentos são considerados autorizados dentro do ambiente monitorado pelo IT Center Security Cloud.

As regras SOC devem consultar este documento antes de gerar alertas.

---

# Ambientes

## Produção

Máquinas utilizadas pelos colaboradores.

## TI

Máquinas utilizadas para suporte, administração e manutenção.

## Servidores

Servidores físicos ou virtuais.

---

# Ferramentas de Acesso Remoto

## Autorizadas

* RustDesk

Justificativa:

Ferramenta utilizada pela equipe de TI para suporte remoto.

---

## Não Autorizadas

* AnyDesk
* TeamViewer
* UltraViewer

Motivo:

Não fazem parte do padrão atual da operação.

---

# VPNs

## Em Avaliação

* Tailscale

---

## Não Autorizadas

* Hamachi
* ZeroTier
* Radmin VPN

Motivo:

Podem criar túneis não controlados para dentro da rede.

---

# Softwares Proibidos

## Torrent

* uTorrent
* BitTorrent
* qBittorrent

Motivo:

Risco jurídico e operacional.

---

# Acesso Remoto

## Máquinas Autorizadas

Categoria:

Equipe de TI

Exemplos:

* NOTE-DANIEL
* PC-TI-01
* PC-TI-02

Observação:

A lista real será mantida conforme o inventário crescer.

---

# RDP

## Permitido

* Servidores
* Máquinas da equipe de TI

## Não Permitido

* Estações comuns de usuários

---

# USB

## Permitido

* Teclados
* Mouses
* Headsets

## Monitorado

* Pendrives
* HDs externos
* SSDs externos
* Smartphones

---

# Antivírus

Obrigatório:

* Microsoft Defender

---

# Firewall

Obrigatório:

* Windows Firewall habilitado

---

# Softwares Obrigatórios

* Microsoft 365
* OneDrive
* Navegador Corporativo

Lista será expandida futuramente.

---

# Responsáveis

Equipe de TI

Responsável atual:

Daniel da Silva Azevedo

---

# Processo de Atualização

Sempre que uma nova ferramenta for aprovada ou removida da operação, este documento deverá ser atualizado antes da alteração das regras SOC.

ASSET_POLICY.md é a fonte oficial para validação de softwares e comportamentos autorizados.
