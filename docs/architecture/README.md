# Arquitetura

Esta pasta descreve a arquitetura do IT Center Security Cloud.

## Documentos principais

| Documento | Conteudo |
| --- | --- |
| `ARCHITECTURE.md` | Arquitetura oficial do sistema. |
| `DATA_FLOW.md` | Fluxos de comunicacao entre agente, API, banco e dashboard. |
| `FUTURE_ARCHITECTURE.md` | Diretrizes de evolucao arquitetural futura. |

## Referencias complementares

| Documento | Conteudo |
| --- | --- |
| `INFRASTRUCTURE.md` | Camada de infraestrutura e Edge Node. |
| `NETWORK.md` | Rede, DNS, portas e isolamento. |
| `CONTAINERS.md` | Containers e responsabilidades. |
| `SECURITY.md` | Seguranca da arquitetura de producao. |

## Visao resumida

```text
Internet
    |
    v
Nginx
    |-- Next.js Dashboard
    `-- FastAPI Backend
            |
            v
        PostgreSQL
```

Somente o Nginx recebe trafego externo. Backend, frontend e banco ficam isolados na rede Docker `itcenter-network`.
