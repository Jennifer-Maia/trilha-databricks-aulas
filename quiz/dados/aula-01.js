// Quiz da Aula 1 · O pedido virou regra
// "porque" da alternativa certa: explica a resposta. Das erradas: diz por que está errada SEM entregar a certa.
window.QUIZ = window.QUIZ || {};
window.QUIZ["01"] = {
  id: "01",
  titulo: "Aula 1 · O pedido virou regra",
  aula_url: "https://github.com/Jennifer-Maia/trilha-databricks-aulas/tree/main/modulo-01-analytics-engineering/aula-01-o-pedido-virou-regra",
  perguntas: [
    {
      pergunta: "O chamado chegou: \"vendas por região, só pedidos concluídos, sem duplicidade\". Qual é o primeiro passo?",
      alternativas: [
        { texto: "Escrever a consulta SQL e mostrar o resultado para a gerente validar.",
          porque: "Mostrar um número antes de combinar a regra faz a gerente validar algo sem saber o que ele conta. É o caminho mais curto para o \"não bate com o financeiro\"." },
        { texto: "Listar as palavras ambíguas do pedido e transformar cada uma numa pergunta.", certa: true,
          porque: "Cada palavra do chamado (\"vendas\", \"região\", \"concluídos\", \"duplicidade\") esconde uma decisão. Perguntar antes de codar evita refazer depois." },
        { texto: "Pedir acesso direto ao banco de dados da loja.",
          porque: "Com acesso total ao banco você ainda não sabe o que é \"concluído\". O problema aqui não é chegar no dado." },
        { texto: "Copiar a lógica do relatório antigo, que já estava em produção.",
          porque: "O relatório antigo é justamente o que não bateu. Copiar a lógica dele copia o problema." },
      ],
    },
    {
      pergunta: "Três pessoas calcularam \"pedidos concluídos\" e chegaram a 946, 1.060 e 1.052. O que explica a diferença?",
      alternativas: [
        { texto: "Duas delas erraram a sintaxe do SQL.",
          porque: "Os três códigos rodam e devolvem números. Nenhum quebrou." },
        { texto: "Os dados mudaram entre um cálculo e outro.",
          porque: "O dataset é fixo (semente 42): os números se repetem toda vez que alguém roda." },
        { texto: "Cada uma interpretou \"concluído\" de um jeito diferente.", certa: true,
          porque: "Ninguém errou o código. A pessoa A contou o texto exato `entregue` (946). A B ignorou maiúsculas, mas contou eventos duplicados (1.060). A C normalizou o status, tirou duplicados e olhou só o status **atual** de cada pedido (1.052)." },
        { texto: "A API devolveu os dados em ordens diferentes.",
          porque: "A ordem das linhas não muda o resultado de uma contagem." },
      ],
    },
    {
      pergunta: "O que é uma **premissa**, no contrato de dados?",
      alternativas: [
        { texto: "Um chute provisório, que a gente apaga quando o código estiver pronto.",
          porque: "Se a premissa sumisse quando o código fica pronto, como alguém do negócio saberia o que você assumiu?" },
        { texto: "Uma regra que vem do sistema de origem e não pode mudar.",
          porque: "Regra do sistema de origem é um fato da fonte. A premissa é sobre outra coisa: como interpretar o pedido." },
        { texto: "Um comentário no código explicando uma linha difícil.",
          porque: "Ninguém do negócio lê o código. Pense em quem precisa ver a premissa para poder corrigir." },
        { texto: "Uma decisão escrita, com dono, que o negócio pode confirmar ou corrigir.", certa: true,
          porque: "Enquanto a resposta do negócio não chega, você decide e **escreve**. Assim todo mundo sabe o que foi assumido e quem pode corrigir. Premissa não é chute." },
      ],
    },
    {
      pergunta: "Por que a tabela `pedidos` sozinha não responde quais pedidos foram concluídos?",
      alternativas: [
        { texto: "Porque ela tem só 100 linhas.",
          porque: "A tabela tem 1.500 pedidos. O \"100\" é o limite de linhas por chamada da API, assunto da aula 2." },
        { texto: "Porque o valor dela está sem desconto.",
          porque: "Ela tem `valor_bruto` e `valor_liquido`. E o valor não diz nada sobre se o pedido foi entregue." },
        { texto: "Porque ela não tem a coluna de status: o status fica na tabela `eventos_pedido`.", certa: true,
          porque: "O pedido não diz se foi entregue nem quando. Cada mudança de status é um evento em `eventos_pedido`, ligado ao pedido pelo `order_id`." },
        { texto: "Porque ela não tem o `order_id`.",
          porque: "Ela tem `order_id`. Inclusive, é ele que liga os pedidos a outra tabela." },
      ],
    },
    {
      pergunta: "Um pedido teve o evento `entregue` e, dois dias depois, `cancelado`. Pelo contrato, ele entra nas vendas?",
      alternativas: [
        { texto: "Sim, porque em algum momento ele foi entregue.",
          porque: "\"Foi entregue alguma vez\" infla o número. Releia no contrato: quando um pedido tem vários eventos, qual deles vale?" },
        { texto: "Sim, mas com o valor bruto.",
          porque: "O tipo de valor (RN-05) não decide se o pedido entra ou não." },
        { texto: "Depende do canal de venda.",
          porque: "O canal não aparece em nenhuma regra do contrato." },
        { texto: "Não, porque vale o status mais recente, e ele é `cancelado`.", certa: true,
          porque: "RN-03: o status atual é o evento mais recente do pedido. RN-04: só conta se o status atual for `entregue`. Este pedido terminou cancelado." },
      ],
    },
    {
      pergunta: "O mesmo evento (mesmo `event_id`) apareceu duas vezes nos dados. O que o contrato manda fazer?",
      alternativas: [
        { texto: "Contar duas vezes, porque são duas linhas.",
          porque: "Contar duas vezes é exatamente a \"duplicidade\" que a gerente pediu para tirar." },
        { texto: "Contar uma vez só.", certa: true,
          porque: "RN-02: mesmo `event_id` = mesmo evento, conta uma vez. Foi isso que separou a pessoa B (1.060) da pessoa C (1.052)." },
        { texto: "Apagar o pedido inteiro.",
          porque: "O pedido existe e é válido. Só o evento veio repetido." },
        { texto: "Mandar as duas linhas para a quarentena.",
          porque: "A quarentena (RN-07) é para evento sem data ou de pedido que não existe. Este evento tem dado bom." },
      ],
    },
    {
      pergunta: "Um cliente não tem UF no cadastro e fez um pedido entregue. O que acontece com essa venda?",
      alternativas: [
        { texto: "Some do relatório, porque não tem região.",
          porque: "Se a venda some, o total deixa de bater com o financeiro, que é justamente o problema que originou o chamado." },
        { texto: "Entra na região Sudeste, que é a maior.",
          porque: "Escolher uma região \"no chute\" esconde o problema e distorce o número de outra região." },
        { texto: "Entra na região `Não informada` e é reportada.", certa: true,
          porque: "RN-06: sem UF → região `Não informada`. A venda continua no total e o problema fica visível para alguém corrigir o cadastro." },
        { texto: "O relatório inteiro para até alguém corrigir o cadastro.",
          porque: "Parar tudo por 4 pedidos (o número real no nosso dataset) é desproporcional. Existe um jeito de entregar e ainda deixar o problema visível." },
      ],
    },
    {
      pergunta: "Para que servem os números das regras (RN-01 a RN-09)?",
      alternativas: [
        { texto: "Para ordenar as regras por importância.",
          porque: "A numeração segue a ordem em que as regras aparecem, não a importância." },
        { texto: "Para o Databricks validar o contrato automaticamente.",
          porque: "O Databricks não lê o contrato. Quem liga cada regra ao resto do projeto somos nós." },
        { texto: "São só enfeite do documento.",
          porque: "Sem número, cada pessoa chama a regra de um jeito. Pense em onde mais a regra vai aparecer nas aulas 3 e 4." },
        { texto: "Para dar a cada regra um endereço que aparece no código (aula 3) e no teste (aula 4).", certa: true,
          porque: "Quando alguém perguntar \"de onde vem esse filtro?\", a resposta é \"RN-04\", e dá para achar a regra no contrato, a linha no código e o teste que prova. Isso é **rastreabilidade**." },
      ],
    },
  ],
};
