# Lab · Módulo 01 — Do dado à confiança

> Status: aula 2 pronta e testada (10/11/2026) · aulas 3 a 6 a construir

## Pré-requisitos

- Conta na [Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition) (custo R$ 0).
- Nada para instalar no computador: tudo roda em notebooks no Databricks, com computação **Serverless**.

## Estrutura

```
lab/
├── README.md
├── setup/
│   ├── 00_validar_ambiente.py     # só para a instrutora: testa a Free Edition antes de gravar
│   ├── 01_criar_ambiente.py       # catálogo, schemas e Volume raw.landing
│   ├── 02_plano_b_sem_api.py      # carga sem a API (se ela estiver fora do ar ou bloqueada)
│   ├── plano_b/                   # os dados da API em arquivo (.jsonl) + formato das colunas
│   └── gerar_dados_loja.py        # como os dados foram gerados (semente 42); não precisa rodar
├── src/
│   └── aula02_ingestao_api.py     # versão do aluno, com TODOs
├── solucao/
│   └── aula02_ingestao_api.py     # versão completa
├── tests/
│   └── aula02_conferir_landing.py # prova que a landing veio completa
└── docs/
    └── aula02_como_funciona.md    # cada peça explicada, com as saídas esperadas
```

## Como rodar do zero

Em todos os notebooks, use o mesmo valor no widget `catalogo` (padrão `jornada_comercial`).

| Ordem | Notebook | Resultado esperado |
|---|---|---|
| 1 | `setup/01_criar_ambiente` | schemas `raw`, `bronze`, `silver`, `gold`, `governanca`, `qualidade` e o Volume `raw.landing` |
| 2 | `src/aula02_ingestao_api` (ou `solucao/…`) | 4 pastas `landing/<tabela>/carga_<data>/` com páginas e `_manifesto.json` |
| 3 | `tests/aula02_conferir_landing` | `Landing completa: todos os testes OK` |

## A fonte: API do Hugging Face

| Item | Valor |
|---|---|
| Endpoint | `GET https://datasets-server.huggingface.co/rows` |
| Parâmetros | `dataset=trilhajornadadatabricks/loja-ficticia-jornada`, `config=<tabela>`, `split=train`, `offset`, `length` |
| Autenticação | Nenhuma (dataset público) |
| Paginação | `offset`/`length`, máximo 100 linhas por chamada (`length` > 100 → HTTP 422) |
| Limite de chamadas | Por IP. Medido em 10/11: ~40 a 55 chamadas seguidas e vem HTTP 429, que libera em ~60 s. Não documentado: pode mudar |
| Volume da carga | 76 chamadas (500 clientes, 60 produtos, 1.500 pedidos, 5.416 eventos) |

**Plano B:** se a API estiver bloqueada (`ConnectTimeout`) ou fora do ar por muito tempo, rode `setup/02_plano_b_sem_api`. Ele grava os mesmos dados no mesmo formato, e o resto do curso funciona igual.

## Custos

R$ 0 na Free Edition. A Free Edition tem cota diária de computação ([limites](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)); este lab usa poucos minutos.
