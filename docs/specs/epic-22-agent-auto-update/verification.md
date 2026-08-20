# Verification: EPIC 22 - Auto-atualização do Agente Windows (Updater Dedicado)

## Acceptance criteria

```
[x] Scenario: Manifest retorna a versão publicada — passou (test_agent_manifest.py::test_manifest_returns_version_and_sha256)
[x] Scenario: Download serve exatamente o arquivo do manifest — passou (test_download_returns_bytes_matching_manifest_sha256)
[x] Scenario: Updater aplica atualização válida — passou (run-agent-updater-tests.ps1, cenário "valid update")
[x] Scenario: Updater rejeita atualização com assinatura inválida — passou (cenário "invalid signature")
[x] Scenario: Updater rejeita atualização com hash divergente — passou (cenário "hash mismatch")
[x] Scenario: Auto-rollback após falhas consecutivas pós-atualização — passou (cenário "rollback")
[x] Scenario: Atualização confirmada após sucessos consecutivos — passou (cenário "confirm")
[x] Scenario: target_agent_version segura uma máquina fora do rollout — passou (cenário "hold-back" + test_manifest_returns_target_agent_version_for_known_hostname)
[x] Scenario: Máquina nunca atualizada automaticamente não muda de comportamento — passou (cenário "no state" + run-agent-tests.ps1 "no-op" case)
[x] Scenario: agent_version aparece no dashboard — passou (npm run build limpo com o novo DetailItem; não verificado visualmente em navegador real, mesma ressalva das EPICs 24/25/26)
```

## Tests

Backend (`python -m pytest -q`, Postgres local via `infra/docker-compose.yml`, `DATABASE_URL` apontando para `127.0.0.1`, não `localhost` — ver nota abaixo): **123 passed** (114 anteriores + 9 novos de `test_agent_manifest.py`, incluindo 2 ajustes em `test_machines.py`).

Agente Windows (`agent-windows/tests/`, executados via PowerShell real neste ambiente Windows):

```
run-agent-tests.ps1              -> "Agent tests passed."
run-install-agent-tests.ps1      -> "install-agent.ps1 execution policy tests passed." /
                                     "install-agent.ps1 updater scheduled task tests passed."
run-agent-updater-tests.ps1      -> "Agent updater tests passed." (novo arquivo, 8 cenários)
```

Frontend (`npm run build` em `frontend/dashboard/`): compilado limpo (Turbopack, TypeScript OK), as 8 rotas existentes sem erro novo.

Infra: `docker compose -f infra/docker-compose.yml config --quiet` validou a sintaxe do compose após a mudança de build context; `docker compose -f infra/docker-compose.yml build backend` completou com sucesso a partir da nova raiz de contexto (repositório inteiro), incluindo o novo passo `COPY agent-windows/itcenter-agent.ps1 ./agent-release/itcenter-agent.ps1`. Confirmado por inspeção direta da imagem (`docker run --rm infra-backend:latest cat /app/agent-release/itcenter-agent.ps1`) que o arquivo chega no caminho exato esperado por `AGENT_RELEASE_PATH` (padrão `/app/agent-release/itcenter-agent.ps1`), com o conteúdo correto (`$script:AgentVersion = "1.0.0"`).

**Não validado nesta sessão:** subir o container `backend` de ponta a ponta contra o Postgres local e bater nos endpoints via HTTP real através do container (não apenas via `TestClient` em processo) — o Postgres local deste ambiente tem um problema pré-existente e não relacionado (EPIC 33: `apply_migrations.py` reaplica todas as migrations a cada start sem tabela de controle, e a migration `011` não é idempotente contra um schema já migrado, entrando em crash-loop). Contornado sem tocar o banco (evitando qualquer ação destrutiva): a validação do `COPY` foi feita inspecionando a imagem diretamente, e o contrato HTTP dos endpoints novos foi validado via `TestClient` real (mesmo mecanismo ASGI, sem mock de FastAPI/Starlette) nos testes de `test_agent_manifest.py`. Recomendado, antes de produção: resolver a EPIC 33 (idempotência de `apply_migrations.py`) ou aplicar a migration `013` isoladamente, depois validar o container subindo de fato.

## Regression check

Suite completa do backend (123 testes, incluindo todos os já existentes de EPICs 1-33) passou sem nenhuma regressão. As 3 suites de teste do agente Windows (incluindo as pré-existentes de EPICs 4/8/16/27/28/31) passaram sem alteração de comportamento fora do que a EPIC 22 introduziu. `npm run build` do frontend sem novos erros/warnings além dos já pré-existentes (deprecation notice de `middleware` -> `proxy`, não relacionado a esta mudança).

## Spec drift encontrado

```
Requisito: FR-001 / FR-007 (spec original, antes desta correção)
Esperado: o updater respeitaria machines.target_agent_version para decidir hold-back.
Real: nenhum mecanismo dava ao updater uma forma de descobrir esse valor - ele só tem
X-Agent-Api-Key (autenticação de classe), sem identidade individual/RBAC para consultar sua
própria máquina.
Impacto: FR-007 seria impossível de implementar como escrito originalmente.
Ação: spec atualizada durante a implementação (mesma sessão, antes de escrever qualquer código
de produção) - GET /api/v1/agent/manifest passou a aceitar um parâmetro de query opcional
hostname (mesmo sinal de identidade já usado no check-in) e devolve target_agent_version na
resposta quando houver correspondência. Documentado em spec.md (FR-001) e no ADR-032 (nota de
implementação em DECISIONS.md). Backend, updater e testes já refletem a versão corrigida - não
há drift remanescente entre spec.md e o código final.
```

## Segurança

- `GET /agent/manifest`/`GET /agent/download`: mesma autenticação de classe do check-in
  (`X-Agent-Api-Key`, `hmac.compare_digest`), sem RBAC de usuário humano — consistente com a
  spec (Security Requirements). Nenhum dado sensível novo exposto (script público do agente +
  hash + hostname/target_agent_version, que já são visíveis a quem tem a `AGENT_API_KEY`
  compartilhada via outros meios).
- `target_agent_version` por hostname: um titular da `AGENT_API_KEY` pode agora perguntar "qual a
  target_agent_version de um hostname arbitrário" — não é um dado sensível (é uma string de
  versão, não um segredo), e o hostname já é informação que o parque compartilhado já expõe.
- Updater nunca aceita bypass de assinatura/hash em runtime (`Test-AgentUpdaterReleaseValid` sem
  nenhum parâmetro de bypass) — comportamento coberto pelos testes "invalid signature"/"hash
  mismatch".
- `update-state.json` recebe a mesma ACL restrita a `SYSTEM`/`Administrators` de `config.json`
  (via `Protect-AgentPath`, já generalizada na EPIC 28-B) — nenhum segredo armazenado ali, só
  versões/contadores.
- Build context do backend ampliado para a raiz do repositório: mitigado por `.dockerignore` na
  raiz excluindo `.git`, `node_modules`, `.venv`, `docs`, testes e outros diretórios não
  necessários à imagem — nenhum arquivo sensível (`.env*`, chaves) entra na imagem (já cobertos
  pelo `.dockerignore` novo, e o Dockerfile só copia `app/`, `migrations/`,
  `apply_migrations.py` e o único arquivo `agent-windows/itcenter-agent.ps1`).

## Escopo

Nenhuma mudança fora do combinado no plano. Um item foi corrigido durante a implementação (ver
"Spec drift encontrado" acima) — documentado, não escondido. `machines.target_agent_version`
continua sem endpoint de escrita (fora de escopo desta EPIC, conforme o backlog original).

## Sign-off

Status final: **VERIFIED**. Falta, antes de considerar isso pronto para produção: (1) validação
end-to-end do container `backend` real contra um Postgres com `apply_migrations.py` funcionando
de ponta a ponta (bloqueado pela EPIC 33, não por esta EPIC); (2) revisão visual manual do novo
campo "Versão do Agente" no dashboard em navegador real (mesma ressalva já registrada nas EPICs
24/25/26); (3) geração real do certificado de assinatura de produção e assinatura dos 4 scripts
(`Sign-AgentScripts.ps1`) antes do primeiro deploy que ative a Tarefa Agendada
`ITCenterAgentUpdater` de verdade - fora do escopo desta implementação, a cargo do mantenedor
(mesmo padrão já estabelecido pela EPIC 16/ADR-031).
