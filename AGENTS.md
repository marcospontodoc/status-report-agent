# Instruções permanentes do projeto

## Objetivo

Este repositório desenvolve, por etapas, um agente genérico para produzir status reports executivos de QA em apresentações PowerPoint editáveis. Siga o escopo solicitado para cada etapa e não antecipe etapas futuras.

## Regras para dados e relatórios

- Não fixe nomes de projetos, módulos, URLs, credenciais ou dados de exemplo nas instruções gerais.
- Não invente métricas, resultados de teste, datas, bugs, responsáveis, prazos ou fatos ausentes das fontes.
- Diferencie claramente dados confirmados pelas fontes, informações ausentes e riscos potenciais inferidos. Identifique inferências como riscos potenciais, com a evidência disponível e as lacunas relevantes.
- Preserve o histórico de execuções de testes; não substitua resultados anteriores por resultados mais recentes.
- Mantenha separados o status de uma tarefa do Jira e o resultado de um caso de teste. Um não é evidência automática do outro.
- Trate Jira, planilhas, documentação e, futuramente, relatórios de automação como fontes distintas, mantendo a origem e o contexto de cada dado.
- O Excel é a fonte de gestão dos cenários de teste manuais e de seus resultados.
- Não assuma que fontes incompletas ou indisponíveis confirmam sucesso, falha ou ausência de risco.

## Segurança e dependências

- Nunca grave tokens, senhas, chaves ou credenciais em arquivos versionados, documentação, exemplos ou relatórios.
- Use variáveis de ambiente ou armazenamento local não versionado para credenciais quando uma integração for implementada; documente apenas os nomes/configurações necessários, sem valores secretos.
- Priorize ferramentas gratuitas e execução local. Avalie dependências futuras pelo custo, manutenção, compatibilidade e capacidade de gerar arquivos editáveis.
- Não envie dados do projeto a serviços externos sem necessidade e autorização compatíveis com o escopo.

## Arquitetura e evolução

- Preserve separação entre aquisição de fontes, normalização/validação, análise executiva e apresentação.
- Mantenha conectores desacoplados para que projetos e fontes possam variar sem instruções específicas de um projeto.
- Planeje suporte futuro a resultados de testes automatizados em formatos como JSON ou JUnit, sem misturá-los aos casos manuais do Excel.
- Gere futuramente PowerPoint com elementos editáveis e rastreáveis às fontes; evite depender de slides renderizados como imagens.
- Nesta fase inicial, apenas documentação e estrutura são permitidas. Não implemente APIs, processamento de arquivos ou geração de relatórios até que uma etapa posterior solicite isso.

## Colaboração via Codex

- O desenvolvimento é conduzido por solicitações em linguagem natural. Faça alterações necessárias nos arquivos dentro do escopo aprovado; não exija que a pessoa usuária escreva código manualmente.
- Para cada solicitação, examine o repositório e as instruções aplicáveis antes de editar.
- Faça mudanças pequenas e focadas na etapa em andamento. Não crie subagentes, skills complexas ou integrações sem solicitação explícita.
- Ao concluir uma etapa, descreva os arquivos alterados, a validação realizada e o próximo passo sugerido. Não avance para a etapa seguinte automaticamente.
