# Aula 2 · Quiz

> 10 perguntas, uma resposta certa em cada. Responda antes de abrir a resposta: a explicação de cada alternativa é onde mora o aprendizado.
> As marcadas com 🎓 são sobre a plataforma Databricks: o tipo de conceito que também aparece nas certificações.

---

### 1. Você chamou a API pedindo `length=100` e recebeu `HTTP 200` com 100 pedidos. A resposta diz `num_rows_total: 1500`. O que aconteceu?

- A) A API falhou e mandou só uma parte.
- B) Funcionou como esperado: cada chamada traz no máximo 100 linhas, e faltam as outras 14 páginas.
- C) A API apagou 1.400 pedidos.
- D) O `requests` cortou a resposta por ser grande demais.

<details>
<summary>Ver resposta</summary>

**B.** A chamada deu certo. Ela só não traz tudo: é preciso **paginar**, aumentando o `offset` de 100 em 100 até chegar no total.

- A) Não houve falha: `200` quer dizer que a chamada funcionou. O "erro" é esperar que uma chamada traga tudo.
- C) O `num_rows_total` diz que os 1.500 estão lá.
- D) O `requests` não corta respostas. Quem limita é a API, e ela avisa o total.
</details>

---

### 2. Você pediu `length=1000` e recebeu `422 → Parameter 'length' must not be greater than 100`. Qual é a atitude certa?

- A) Tentar de novo depois de alguns segundos.
- B) Tentar de novo com espera dobrando (backoff).
- C) Corrigir o pedido: no máximo 100 por chamada, e paginar.
- D) Trocar de API.

<details>
<summary>Ver resposta</summary>

**C.** Código **4xx** (menos o 429) quer dizer "o problema está no seu pedido". O mesmo pedido vai dar o mesmo erro para sempre.

- A) e B) Tentar de novo só serve para falha passageira. Aqui a falha é do pedido, e a API até disse qual é o limite.
- D) A API está funcionando. Ela só tem uma regra, e a mensagem explica qual.
</details>

---

### 3. No meio da carga veio `HTTP 429`. O que ele quer dizer, e o que fazer?

- A) Seu pedido está errado. Corrija os parâmetros.
- B) Você fez chamadas demais em pouco tempo. Espere e tente de novo.
- C) O dataset não existe.
- D) A rede da Free Edition bloqueou o site.

<details>
<summary>Ver resposta</summary>

**B.** 429 é o **rate limit**: a API limita quantas chamadas cada um faz num intervalo. A carga toda são 76 chamadas, então é normal ver um 429. O retry espera e segue.

- A) O pedido está certo: as mesmas chamadas funcionavam um minuto antes.
- C) Dataset que não existe dá 404.
- D) Bloqueio de rede nem chega a ter código HTTP: aparece como `ConnectTimeout` ou `ConnectionError`.
</details>

---

### 4. O que é **backoff exponencial**?

- A) Diminuir o `length` pela metade a cada erro.
- B) Esperar cada vez mais entre as tentativas: 2 s, 4 s, 8 s…
- C) Fazer várias chamadas ao mesmo tempo para terminar mais rápido.
- D) Tentar de novo sem esperar, até dar certo.

<details>
<summary>Ver resposta</summary>

**B.** A espera dobra a cada tentativa. Isso dá tempo para o serviço se recuperar sem você ficar martelando ele.

- A) Mudar o tamanho da página não ajuda com servidor fora do ar ou limite de chamadas.
- C) Chamadas em paralelo fazem bater no limite (429) mais rápido ainda.
- D) Tentar sem esperar piora o problema e, com limite de chamadas, pode prolongar o bloqueio.
</details>

---

### 5. Por que a gente grava o `r.text` (a resposta crua) em vez de um JSON já "arrumado", só com as colunas que interessam?

- A) Porque é mais rápido de escrever.
- B) Porque é a prova do que a fonte mandou: se a transformação tiver bug, dá para refazer sem chamar a API de novo.
- C) Porque o Spark não consegue ler JSON arrumado.
- D) Porque o Volume só aceita texto cru.

<details>
<summary>Ver resposta</summary>

**B.** A landing guarda o dado **como veio**. Qualquer interpretação (o que é coluna útil, como tratar status) fica para a aula 3, onde pode ser corrigida e refeita a partir desses arquivos.

- A) A velocidade é parecida. O motivo é rastreabilidade.
- C) O Spark lê os dois formatos.
- D) O Volume aceita qualquer arquivo: JSON, CSV, imagem, PDF.
</details>

---

### 6. Uma pasta `carga_...` na landing tem as páginas, mas **não tem** `_manifesto.json`. O que isso quer dizer?

- A) A carga está completa: o manifesto é opcional.
- B) A carga parou no meio ou não bateu o total. Quem lê a landing deve ignorar essa pasta.
- C) A carga veio pelo plano B.
- D) Alguém apagou o manifesto e é preciso recriar na mão.

<details>
<summary>Ver resposta</summary>

**B.** O manifesto só é escrito **no fim**, se o total bateu. Sem manifesto = sem garantia de que veio tudo. O notebook de teste mostra essas pastas como aviso e usa só as completas.

- A) É o manifesto que diz que a carga está completa. Sem ele, não dá para saber.
- C) O plano B também escreve manifesto, com `"fonte": "plano_b"`.
- D) Escrever o manifesto na mão seria declarar completa uma carga que ninguém conferiu. O certo é rodar uma carga nova.
</details>

---

### 7. 🎓 Qual destes é o caminho para gravar um arquivo, com o `open()` do Python, no Volume `landing` do schema `raw` do catálogo `jornada_comercial`?

- A) `/Volumes/jornada_comercial/raw/landing/pagina_0000.json`
- B) `jornada_comercial.raw.landing/pagina_0000.json`
- C) `/Workspace/jornada_comercial/raw/landing/pagina_0000.json`
- D) `dbfs:/FileStore/jornada_comercial/pagina_0000.json`

<details>
<summary>Ver resposta</summary>

**A.** Arquivos em Volumes ficam em `/Volumes/<catálogo>/<schema>/<volume>/` ([doc de Volumes](https://docs.databricks.com/aws/en/volumes/)).

- B) `jornada_comercial.raw.landing` é o **nome** do Volume no Unity Catalog (o mesmo padrão de três níveis das tabelas: catálogo.schema.objeto). Serve para dar permissão (`GRANT`), não como caminho de arquivo.
- C) `/Workspace` é onde ficam notebooks e arquivos do workspace, não os Volumes.
- D) `dbfs:/FileStore` é o jeito antigo de guardar arquivos, fora da governança do Unity Catalog.
</details>

---

### 8. 🎓 Por que a landing é um **Volume** e não uma tabela?

- A) Porque tabela não pode ter mais de 1.000 linhas.
- B) Porque o Volume guarda arquivos (aqui, JSON cru) com a governança do Unity Catalog. Tabela é para dado já organizado em linhas e colunas.
- C) Porque Volume é mais barato na Free Edition.
- D) Porque o Spark não lê tabelas.

<details>
<summary>Ver resposta</summary>

**B.** Volumes são para arquivos, inclusive os que ainda não viraram tabela. Eles têm permissões controladas pelo Unity Catalog, como as tabelas ([doc de Volumes](https://docs.databricks.com/aws/en/volumes/)). Na aula 3 esses arquivos viram tabelas Delta.

- A) Tabelas não têm esse limite.
- C) Escolhemos o Volume pelo tipo do dado (arquivo cru), não pelo preço.
- D) O Spark lê tabelas normalmente: é o uso mais comum dele.
</details>

---

### 9. 🎓 O notebook começa com `dbutils.widgets.text("catalogo", "jornada_comercial")`. Para que serve isso?

- A) Para criar o catálogo `jornada_comercial`.
- B) Para criar uma caixinha de parâmetro no topo do notebook. O mesmo código roda em outro catálogo sem editar nada.
- C) Para dar permissão de leitura no catálogo.
- D) Para conectar o notebook no Serverless.

<details>
<summary>Ver resposta</summary>

**B.** Widgets são parâmetros do notebook ([doc de widgets](https://docs.databricks.com/aws/en/notebooks/widgets)): `text` cria a caixa com um valor padrão e `get` lê o valor. É por isso que a regra do lab é "nada de nome fixo no código".

- A) Quem cria o catálogo é o `setup/01_criar_ambiente`, com `CREATE CATALOG`. O widget só guarda o nome.
- C) Permissão é com `GRANT` (aula 5).
- D) A conexão é escolhida no botão *Connect*, no topo do notebook.
</details>

---

### 10. A fonte mandou as colunas com `valor_liq` no lugar de `valor_liquido`. O que a validação de schema da aula faz, e por quê?

- A) Ignora: o Spark descobre sozinho.
- B) Só avisa e segue a carga.
- C) Para a carga com erro, porque falta uma coluna que o contrato espera e o cálculo das vendas depende dela.
- D) Renomeia a coluna automaticamente.

<details>
<summary>Ver resposta</summary>

**C.** Coluna **faltando** para tudo: melhor quebrar na entrada do que entregar um relatório errado semanas depois. Já uma coluna **nova** só gera aviso, porque não quebra nada.

- A) O Spark leria `valor_liq` sem reclamar, e a regra RN-05 (que usa `valor_liquido`) falharia ou daria nulo lá na frente.
- B) Seguir com uma coluna essencial faltando é o "erro que não dá erro".
- D) Adivinhar que `valor_liq` é a mesma coisa é uma premissa. Ela precisa ser decidida e escrita, não feita escondida no código.
</details>
