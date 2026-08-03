> **ARQUIVO LEGADO — não é sobre o agente Windows.** Este arquivo era um prompt genérico de instruções para agentes de IA (anterior ao `CLAUDE.md` da raiz do projeto e aos subagents nativos em `.claude/agents/`, que hoje são a fonte de verdade sobre como agentes de IA devem trabalhar neste repositório — ver ADR-026 e `docs/development/AI_WORKFLOW.md`). Mantido apenas por histórico; não usar como referência.

Você é um agente de desenvolvimento do projeto
IT Center Security Cloud.

Antes de implementar qualquer funcionalidade:

1. Leia docs/development/ROADMAP.md
2. Leia docs/development/TASKS.md
3. Leia docs/architecture/ARCHITECTURE.md
4. Leia docs/backend/DATABASE.md
5. Leia docs/backend/API.md
6. Leia docs/development/DECISIONS.md

Regras:

- Não alterar arquitetura sem atualizar docs/development/DECISIONS.md
- Não criar tabelas fora de docs/backend/DATABASE.md
- Não criar endpoints fora de docs/backend/API.md
- Não adicionar tecnologias fora da stack oficial
- Priorizar simplicidade
- Priorizar custo zero
- Seguir docs/development/TASKS.md
