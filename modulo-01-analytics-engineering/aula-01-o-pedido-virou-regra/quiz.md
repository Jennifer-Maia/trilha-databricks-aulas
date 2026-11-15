# Aula 1 · Quiz

> 8 perguntas, uma resposta certa em cada. Responda antes de abrir a resposta: a explicação de cada alternativa é onde mora o aprendizado.
> Base: o [chamado](README.md#o-chamado) e o [contrato de dados](../docs/contrato_de_dados.md).

---

### 1. O chamado chegou: "vendas por região, só pedidos concluídos, sem duplicidade". Qual é o primeiro passo?

- A) Escrever a consulta SQL e mostrar o resultado para a gerente validar.
- B) Listar as palavras ambíguas do pedido e transformar cada uma numa pergunta.
- C) Pedir acesso direto ao banco de dados da loja.
- D) Copiar a lógica do relatório antigo, que já estava em produção.

<details>
<summary>Ver resposta</summary>

**B.** Cada palavra em negrito do chamado ("vendas", "região", "concluídos", "duplicidade") esconde uma decisão. Perguntar antes evita refazer depois.

- A) Mostrar um número antes de combinar a regra é o caminho para o "não bate com o financeiro". A gerente vai validar um número sem saber o que ele conta.
- C) Acesso não resolve ambiguidade. Com acesso total você ainda não sabe o que é "concluído".
- D) O relatório antigo é justamente o que não bateu. Copiar a lógica dele copia o problema.
</details>

---

### 2. Três pessoas calcularam "pedidos concluídos" e chegaram a 946, 1.060 e 1.052. O que explica a diferença?

- A) Duas delas erraram a sintaxe do SQL.
- B) Os dados mudaram entre um cálculo e outro.
- C) Cada uma interpretou "concluído" de um jeito diferente.
- D) A API devolveu os dados em ordens diferentes.

<details>
<summary>Ver resposta</summary>

**C.** Ninguém errou o código. A pessoa A contou o texto exato `entregue` (946). A pessoa B ignorou maiúsculas, mas contou eventos duplicados (1.060). A pessoa C normalizou o status, tirou duplicados e olhou só o status **atual** de cada pedido (1.052).

- A) Os três códigos rodam e devolvem números. O problema é o que cada um decidiu contar.
- B) O dataset é fixo (semente 42). Os números se repetem toda vez.
- D) A ordem das linhas não muda uma contagem. Ela importa para achar o status *mais recente*, mas isso é uma regra, não a causa das três respostas.
</details>

---

### 3. O que é uma **premissa**, no contrato de dados?

- A) Um chute provisório, que a gente apaga quando o código estiver pronto.
- B) Uma decisão escrita, com dono, que o negócio pode confirmar ou corrigir.
- C) Uma regra que vem do sistema de origem e não pode mudar.
- D) Um comentário no código explicando uma linha difícil.

<details>
<summary>Ver resposta</summary>

**B.** Enquanto a resposta do negócio não chega, você decide e **escreve**. Assim todo mundo sabe o que foi assumido e quem pode corrigir.

- A) Premissa não é chute e não some: ela fica no contrato até ser confirmada ou trocada por uma resposta.
- C) Regra do sistema de origem é um fato da fonte. Premissa é uma decisão sua sobre como interpretar o pedido.
- D) Comentário no código ninguém do negócio lê. A premissa precisa estar num lugar que a gerente veja.
</details>

---

### 4. Por que a tabela `pedidos` sozinha não responde quais pedidos foram concluídos?

- A) Porque ela não tem a coluna de status: o status fica na tabela `eventos_pedido`.
- B) Porque ela tem só 100 linhas.
- C) Porque o valor dela está sem desconto.
- D) Porque ela não tem o `order_id`.

<details>
<summary>Ver resposta</summary>

**A.** O pedido não diz se foi entregue nem quando. Cada mudança de status é um evento em `eventos_pedido`, ligado ao pedido pelo `order_id`.

- B) A tabela tem 1.500 pedidos. "100" é o limite de linhas por chamada da API (aula 2), não o tamanho da tabela.
- C) Ela tem `valor_bruto` e `valor_liquido`. O valor não diz nada sobre o status.
- D) Ela tem `order_id`. É ele que liga as duas tabelas.
</details>

---

### 5. Um pedido teve o evento `entregue` e, dois dias depois, `cancelado`. Pelo contrato, ele entra nas vendas?

- A) Sim, porque em algum momento ele foi entregue.
- B) Sim, mas com o valor bruto.
- C) Não, porque vale o status mais recente, e ele é `cancelado`.
- D) Depende do canal de venda.

<details>
<summary>Ver resposta</summary>

**C.** RN-03: status atual = evento mais recente do pedido. RN-04: só conta se o status atual for `entregue`. Esse pedido terminou cancelado.

- A) "Foi entregue alguma vez" é outra regra, que infla o número. É parecido com o erro da pessoa B.
- B) O tipo de valor (RN-05) não muda se o pedido entra ou não.
- D) O canal não aparece em nenhuma regra do contrato.
</details>

---

### 6. O mesmo evento (mesmo `event_id`) apareceu duas vezes nos dados. O que o contrato manda fazer?

- A) Contar duas vezes, porque são duas linhas.
- B) Contar uma vez só.
- C) Apagar o pedido inteiro.
- D) Mandar as duas linhas para a quarentena.

<details>
<summary>Ver resposta</summary>

**B.** RN-02: mesmo `event_id` = mesmo evento, conta uma vez. Foi isso que separou a pessoa B (1.060) da pessoa C (1.052).

- A) Contar duas vezes é exatamente a "duplicidade" que a gerente pediu para tirar.
- C) O pedido existe e é válido. Só o evento veio repetido.
- D) A quarentena (RN-07) é para evento sem data ou de pedido que não existe. Evento duplicado tem dado bom: basta ficar com uma cópia.
</details>

---

### 7. Um cliente não tem UF no cadastro e fez um pedido entregue. O que acontece com essa venda?

- A) Some do relatório, porque não tem região.
- B) Entra na região `Não informada` e é reportada.
- C) Entra na região Sudeste, que é a maior.
- D) O relatório inteiro para até alguém corrigir o cadastro.

<details>
<summary>Ver resposta</summary>

**B.** RN-06: sem UF → região `Não informada`. A venda continua no total e o problema fica visível para alguém corrigir.

- A) Sumir com a venda faz o total não bater com o financeiro, que é o problema que originou o chamado.
- C) Escolher uma região "no chute" esconde o problema e distorce o número do Sudeste.
- D) Parar tudo por 4 pedidos (o número real no nosso dataset) é desproporcional. Melhor entregar e reportar.
</details>

---

### 8. Para que servem os números das regras (RN-01 a RN-09)?

- A) Para ordenar as regras por importância.
- B) Para dar para cada regra um endereço que aparece no código (aula 3) e no teste (aula 4).
- C) Para o Databricks validar o contrato automaticamente.
- D) São só enfeite do documento.

<details>
<summary>Ver resposta</summary>

**B.** Quando alguém perguntar "de onde vem esse filtro?", a resposta é "RN-04", e dá para achar a regra no contrato, a linha no código e o teste que prova. Isso é **rastreabilidade**.

- A) A numeração segue a ordem em que as regras aparecem, não a importância.
- C) O Databricks não lê o contrato. Quem liga a regra ao código e ao teste somos nós.
- D) Sem número, cada pessoa chama a regra de um jeito e a conversa volta a ser ambígua.
</details>
