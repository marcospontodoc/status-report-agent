# Sistema demonstrativo fictício — documentação para desenvolvimento

> **Aviso:** este documento e a planilha `inputs/excel/modelo_qa_teste.xlsx` contêm exclusivamente dados fictícios, criados para desenvolvimento e demonstração. Não representam produto, projeto, pessoas, execução ou resultado real.

## Objetivo e escopo

### Evidências derivadas da planilha

A fixture contém cenários sobre autenticação, perfil de conta, busca e filtros de itens, carrinho e pedidos. Isso permite descrever, apenas para fins demonstrativos, uma aplicação de software com esses fluxos sob teste. A planilha não confirma arquitetura, público, operação ou objetivo comercial do sistema.

O escopo observado na fixture é limitado aos seguintes comportamentos testados:

- Entrada com credenciais válidas e rejeição de senha inválida.
- Bloqueio após uma quantidade configurada de tentativas inválidas.
- Visualização do perfil, persistência do nome de exibição e solicitação de alteração de e-mail com confirmação.
- Busca por nome, combinação de filtro de categoria e faixa de preço e estado vazio sem correspondências.
- Inclusão de item disponível no carrinho, conclusão de pedido e cancelamento antes do processamento.

### Hipótese fictícia complementar

Para completar o exemplo, considera-se uma aplicação demonstrativa que oferece acesso a uma conta e consulta de itens, com um fluxo de carrinho e pedidos. Essa descrição é uma hipótese derivada dos nomes dos cenários, não uma especificação confirmada do produto.

## Requisitos funcionais identificados na fixture

Os itens abaixo são **intenções de validação registradas nos cenários**. Eles não substituem requisitos aprovados ou documentação de produto.

| Referência | Comportamento a validar | Evidência |
|---|---|---|
| US-FIC-001 | Autenticar com credenciais válidas, rejeitar senha inválida e bloquear tentativas consecutivas após o limite configurado. | TC-FIC-001 a TC-FIC-003 |
| US-FIC-002 | Exibir o perfil, persistir o nome de exibição e permitir solicitar alteração de e-mail com etapa de confirmação. | TC-FIC-004 a TC-FIC-006 |
| US-FIC-003 | Buscar item por nome, combinar categoria e faixa de preço e informar ausência de resultados. | TC-FIC-007 a TC-FIC-009 |
| US-FIC-004 | Adicionar item disponível ao carrinho, concluir pedido com dados de pagamento de teste e cancelar pedido em estado cancelável. | TC-FIC-010 a TC-FIC-012 |

Os identificadores `US-FIC-*` e `TC-FIC-*` são os IDs sintéticos existentes na planilha; não devem ser tratados como IDs de um projeto real.

## Regras de negócio indicadas pelos cenários

As frases abaixo descrevem condições esperadas nos testes, não regras aprovadas fora da fixture:

- Uma senha incorreta não deve iniciar uma sessão.
- Depois de atingir um limite configurado de tentativas inválidas, o acesso deve ficar temporariamente bloqueado.
- Um nome de exibição salvo deve continuar visível após recarregar o perfil.
- A alteração de e-mail não deve ocorrer antes da conclusão da confirmação.
- Cada resultado da busca com filtros combinados deve satisfazer a categoria e a faixa de preço selecionadas.
- Um pedido em estado cancelável pode ser cancelado antes do processamento.

O valor do limite de tentativas, a duração do bloqueio, os estados de pedido e demais políticas não são informados pela planilha.

## Critérios de aceitação derivados dos resultados esperados

Os critérios a seguir são paráfrases dos resultados esperados registrados, associadas aos cenários. São critérios **derivados da fixture fictícia**, não critérios formalmente aprovados:

- `TC-FIC-001` e `TC-FIC-002`: credenciais válidas abrem a área inicial; senha inválida exibe mensagem e não inicia sessão.
- `TC-FIC-003`: após o número configurado de tentativas incorretas, o sistema bloqueia temporariamente o acesso e explica o bloqueio.
- `TC-FIC-004` e `TC-FIC-005`: o perfil mostra seus dados; o nome alterado permanece após recarga.
- `TC-FIC-006`: a etapa de confirmação é apresentada e o e-mail não muda antes da conclusão.
- `TC-FIC-007` a `TC-FIC-009`: a busca retorna correspondência, respeita simultaneamente categoria e faixa de preço e informa quando não encontra itens.
- `TC-FIC-010` a `TC-FIC-012`: o carrinho mostra item e quantidade; o pedido confirmado recebe identificador; o cancelamento muda o estado e apresenta confirmação.

Na planilha, `TC-FIC-009`, `TC-FIC-011` e `TC-FIC-012` estão como `Não Executado`. Seus resultados esperados não são evidência de aprovação ou execução.

## Bugs registrados na fixture

Os quatro registros abaixo são fictícios e relacionados a seus cenários na planilha:

| Bug | Cenário relacionado | Descrição resumida | Severidade | Status |
|---|---|---|---|---|
| BUG-FIC-001 | TC-FIC-003 | Novas tentativas são aceitas após o limite, sem bloqueio. | Crítica | Aberto |
| BUG-FIC-002 | TC-FIC-005 | O perfil volta a mostrar o nome anterior depois de salvar e recarregar. | Alta | Em Correção |
| BUG-FIC-003 | TC-FIC-008 | O filtro combinado pode incluir item acima do limite de preço. | Média | Pronto para Reteste |
| BUG-FIC-004 | TC-FIC-006 | A solicitação de alteração de e-mail não apresenta a confirmação. | Baixa | Em Análise |

Estes são os relatos e estados registrados na fixture; este documento não confirma correção ou reteste.

## Restrições e informações ausentes para QA

A planilha não especifica arquitetura, versões suportadas, navegadores, dispositivos, integrações, dados reais, serviço de pagamento, comportamento de segurança detalhado nem requisitos não funcionais. Também não define os valores do limite de tentativas, as regras de preço/categoria além do filtro combinado, os estados válidos de pedido ou o mecanismo de confirmação do e-mail. Esses pontos devem ser obtidos de fontes aprovadas antes de serem usados como critérios de cobertura.

O campo `Resultado` da planilha registra o resultado do cenário; não executa nem comprova sozinho os critérios acima. Cenários como `Não Executado` permanecem sem resultado de execução.
