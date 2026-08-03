---
description: Roda o pipeline arquitetura -> implementação -> (review + segurança) -> docs para uma feature do IT Center Security Cloud
argument-hint: <descrição da feature>
---

Esta instrução autoriza explicitamente o uso da ferramenta Workflow (esse é o gatilho de opt-in exigido por ela) para orquestrar a feature abaixo em 4 fases: Architecture, Implementation, Review & Security (em paralelo) e Docs.

Chame a ferramenta Workflow com `args: { task: "$ARGUMENTS" }` e o seguinte script:

```js
export const meta = {
  name: 'feature-pipeline',
  description: 'Pipeline architecture -> implementation -> (review + security em paralelo) -> docs',
  phases: [
    { title: 'Architecture' },
    { title: 'Implementation' },
    { title: 'Review & Security' },
    { title: 'Docs' },
  ],
}

phase('Architecture')
const architecture = await agent(
  `Avalie o impacto arquitetural desta feature no IT Center Security Cloud, seguindo docs/architecture/ARCHITECTURE.md e docs/development/DECISIONS.md. Diga se exige ADR novo, mudança em docs/backend/DATABASE.md ou docs/backend/API.md. Feature: ${args.task}`,
  { label: 'architecture' }
)

phase('Implementation')
const implementation = await agent(
  `Com base nesta avaliação de arquitetura:\n${architecture}\n\nImplemente a feature no backend e/ou frontend do IT Center Security Cloud, seguindo docs/development/CONTRIBUTING.md (sem inventar endpoint/tabela, sem tecnologia fora da stack oficial). Feature: ${args.task}`,
  { label: 'implementation' }
)

const [review, security] = await parallel([
  () => agent(
    `Revise o código abaixo focando em reuso, simplificação e eficiência (sem caça a bugs, isso é feito separadamente). Alterações:\n${implementation}`,
    { label: 'review', phase: 'Review & Security' }
  ),
  () => agent(
    `Faça uma revisão de segurança (OWASP Top 10, docs/security/SECURITY.md, docs/security/AUTH.md) das alterações abaixo. Liste achados como risco -> cenário concreto -> correção sugerida. Alterações:\n${implementation}`,
    { label: 'security', phase: 'Review & Security' }
  ),
])

phase('Docs')
const docs = await agent(
  `Atualize a documentação correspondente em docs/ para refletir esta feature, seguindo o documento responsável de cada assunto (docs/development/CONTRIBUTING.md, seção "Fonte da Verdade"). Alterações:\n${implementation}\nAchados de segurança:\n${security}`,
  { label: 'docs' }
)

return { architecture, implementation, review, security, docs }
```

Depois que a Workflow retornar, resuma para o usuário: decisão de arquitetura, arquivos alterados, achados de review, achados de segurança e documentação atualizada.
