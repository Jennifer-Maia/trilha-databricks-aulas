# Trilha Databricks · Jornada de Dados

Material das aulas dos novos módulos de Databricks da **Jornada de Dados**: laboratórios, slides, diagramas e documentos de apoio.
Tudo roda na **Databricks Free Edition** (custo R$ 0) e usa uma loja online fictícia como cenário.

![Roadmap da trilha Databricks: novembro e dezembro de 2026 e as trilhas por certificação de 2027](docs/roadmap.svg)

## Roadmap

| Quando | O quê | Promessa | Certificação que apoia | Status |
|---|---|---|---|---|
| **Novembro/2026** | Módulo 01 · **Analytics Engineering com Databricks** | Do pedido do negócio a uma tabela confiável: regra escrita, testes e acesso controlado por perfil | Data Analyst Associate | 🟡 em gravação |
| **Dezembro/2026** | Módulo 02 · **Por que minha tabela ficou lenta e cara?** | Delta Lake por dentro, performance e custo, com números de antes e depois | Data Engineer Associate | ⚪ em preparação |
| **2027 · 1º trimestre (até abril)** | Trilha **Engenharia de Dados** | Os temas da prova, com projeto de portfólio. Começa onde dezembro termina | Data Engineer Associate | ⚪ planejada |
| **2027 · na sequência** | Trilha **Machine Learning** | Do treino ao modelo em produção no Databricks | Machine Learning Associate | ⚪ planejada |
| **2027 · na sequência** | Trilha **IA Generativa** | Agentes e aplicações de IA no Databricks | Generative AI Engineer Associate | ⚪ planejada |

Em 2027 a trilha segue a organização da própria Databricks: **uma trilha por certificação**. O formato (cursos novos ou módulos dentro da trilha atual), a ordem e as datas serão anunciados ao longo do ano.

### Em todas as trilhas

- **Quiz em cada aula**, com questões no estilo da prova e a explicação de cada alternativa.
- **Simulado cronometrado**, no formato da prova, com nota por tema no final.
- **Projeto de portfólio** que evolui de módulo em módulo. Cada módulo também funciona sozinho.

As questões são autorais, baseadas no guia oficial de cada prova.

## Módulos

| Módulo | Pasta | O que tem |
|---|---|---|
| 01 · Analytics Engineering com Databricks | [`modulo-01-analytics-engineering/`](modulo-01-analytics-engineering/) | Lab da ingestão via API (aula 2), slides das aulas 1 e 2, contrato de dados, diagramas |
| 02 · Por que minha tabela ficou lenta e cara? | [`modulo-02-delta-performance-custo/`](modulo-02-delta-performance-custo/) | Ementa prevista e diagrama de visão geral |

## Estrutura de cada módulo

```
modulo-NN-slug/
├── README.md     # o que você vai aprender, aulas e como rodar
├── slides/       # slides de cada aula (abra o .html no navegador)
├── diagramas/    # desenhos de cada aula (.excalidraw, abra em https://excalidraw.com)
├── docs/         # documentos de apoio (ex.: contrato de dados)
└── lab/
    ├── setup/    # prepara o ambiente e o plano B sem internet
    ├── src/      # versão do aluno, com TODOs para completar
    ├── solucao/  # versão completa, para conferir
    ├── tests/    # prova que o resultado está certo
    └── docs/     # explicação peça por peça do código
```

## Como começar

1. Crie uma conta na [Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition).
2. Traga este repositório para o Databricks: **Workspace → Create → Git folder** e cole a URL do repositório. Se a opção não aparecer no seu workspace, baixe os `.py` de `lab/` e importe pela opção **Import**.
3. Abra o `README.md` do módulo e siga a tabela **Como rodar do zero**.

## Dados

Os laboratórios usam o dataset fictício [`loja-ficticia-jornada`](https://huggingface.co/datasets/trilhajornadadatabricks/loja-ficticia-jornada) (500 clientes, 60 produtos, 1.500 pedidos e 5.416 eventos de status), consumido pela API pública do Hugging Face. Os dados foram gerados com semente fixa: todo mundo chega nos mesmos números. Não há dado real de pessoas nem de empresas.

## Pré-requisitos

Estes módulos aprofundam o que a Jornada de Dados já ensina. Vale ter feito antes:

- Módulo 1 · Fundamentos do Databricks (principalmente Unity Catalog)
- Módulo 2 · Arquitetura Medalhão
- Módulo 4 · Requisitos
- Módulo 6 · PySpark básico

---

Material da **Jornada de Dados**, conduzido por Jennifer Maia.
