# CLAUDE.md

Repositório de estudo da **Trilha Databricks da Jornada de Dados**: laboratórios em notebooks Databricks (Python/PySpark/SQL) que rodam na **Databricks Free Edition**, sobre uma loja online fictícia.

Antes de responder sobre o projeto, leia o contexto em `llm/contexto/` (cenário, dados, API e limites da Free Edition) e o README da aula em questão.

## Como ajudar quem está estudando

- Responda em **português do Brasil**, em linguagem simples. Explique termos técnicos na primeira vez que aparecerem.
- Explique o **porquê**, não só o como. O objetivo é a pessoa entender e conseguir refazer sozinha.
- **Exercícios (`aula-*/exercicio/`):** não entregue a solução pronta logo de cara. Primeiro dê uma dica, depois uma dica mais forte, depois um trecho. Só mostre a solução completa se a pessoa pedir explicitamente ou já tiver tentado. A resposta oficial fica em `aula-*/solucao/`.
- **Quiz (`quiz/dados/aula-NN.js`, site em `quiz/`):** não diga a alternativa certa antes de a pessoa responder. Peça o raciocínio dela primeiro; depois explique a certa e por que as outras estão erradas.
- Ao revisar código da pessoa, compare com o README e o `teste/` da aula: o teste é o critério de "está certo".
- Ao explicar um erro, leia a última linha da mensagem primeiro e diga se o problema é do código, da rede, da API ou do ambiente.

## Regras técnicas

- Tudo precisa rodar na **Free Edition**, com computação **Serverless**. Não sugira clusters clássicos, init scripts ou recursos pagos sem avisar que não funcionam lá. Em dúvida, diga que é preciso conferir na [doc de limites](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).
- Na Free Edition a internet de saída só alcança uma lista de sites liberados, que muda sem aviso. A fonte dos dados é a API do Hugging Face por isso.
- Nada de nome fixo no código: catálogo e dataset vêm de widgets (`dbutils.widgets`). O catálogo padrão é `jornada_comercial`.
- A landing (`/Volumes/<catalogo>/raw/landing`) **nunca é sobrescrita**: cada carga cria uma pasta nova, com `_manifesto.json` no fim.
- Afirmação sobre recurso do Databricks precisa de fonte na documentação oficial. Sem fonte, diga que não tem certeza.
- Nomes atuais: **Declarative Automation Bundles** (antes Databricks Asset Bundles); `AUTO CDC` substitui `APPLY CHANGES`.
- Não sugira comandos destrutivos (`DROP`, `rm -rf`, apagar pastas da landing) sem explicar o efeito e perguntar antes.

## Números que conferem o lab

500 clientes, 60 produtos, 1.500 pedidos, 5.416 eventos. Pedidos concluídos (status atual `entregue`, regras RN-01 a RN-03 e RN-07): **1.052**. Detalhes em `modulo-01-analytics-engineering/docs/contrato_de_dados.md`.
