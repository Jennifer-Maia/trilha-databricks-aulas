# Contexto 03 · Databricks Free Edition

Documentação oficial: [Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition) · [Limitações](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations).

## O que o lab assume

- Computação **Serverless** (notebooks e jobs). É a opção da Free Edition: não há cluster clássico para configurar.
- **Unity Catalog**: catálogos, schemas, tabelas e Volumes funcionam. O lab cria o catálogo `jornada_comercial`.
- Há cota diária de computação. Os labs usam poucos minutos.
- Arquivos ficam em **Volumes** (`/Volumes/<catalogo>/<schema>/<volume>/`), não no DBFS root.

## Internet de saída

O workspace só alcança uma lista de sites liberados, que **não é publicada e muda sem aviso**. O que observamos ao preparar o lab:

| Data | Respondeu | Bloqueado |
|---|---|---|
| 09/11/2026 | Hugging Face, GitHub, PyPI | IBGE |
| 10/11/2026 | Hugging Face, GitHub, PyPI, DummyJSON | IBGE |

Por isso a fonte é o Hugging Face e existe o plano B. Erro `ConnectTimeout` ou `ConnectionError` = a rede não chegou no site (não é bug no código).

## Cuidados que o lab já segue

- Ler e escrever arquivo do Volume com Python comum (`open`, `os.makedirs`) e ler com Spark (`spark.read.json`).
- Não sobrescrever um arquivo e ler logo em seguida com o Spark: cada carga vai para uma pasta nova.
- Se a sessão do notebook reiniciar, as variáveis somem (`NameError`): rode de novo a célula de parâmetros.

Antes de afirmar que um recurso funciona na Free Edition, confira na documentação de limitações ou teste.
