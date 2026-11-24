Três pessoas receberam o mesmo pedido, "quero as vendas por região", e chegaram a números diferentes.

No meu projeto de Analytics Engineering no Databricks, eu parei de discutir o número e fui decidir as regras:
- transformei o pedido em 9 regras numeradas: o que é "concluído", o que é duplicado, qual status vale;
- busquei os dados numa API, página por página, com retry, e conferi se veio tudo;
- cada regra virou um teste (9 de 9 OK na última rodada), e o acesso por região e a máscara de e-mail e telefone ficaram na própria tabela;
- entreguei um painel e um agente de IA (Genie) que respondem com as mesmas regras. Cada vendedor só vê a própria região.

Resultado: 1052 pedidos concluídos, R$ 2.302.177,12 em vendas, com o Sudeste respondendo por 52% do valor. E qualquer número tem caminho de volta até a regra que o gerou.

O que mais me ensinou: o mesmo SQL deu um número menor num perfil sem acesso a tudo, sem erro nenhum. Por isso o número oficial sai sempre do perfil financeiro.

Dados fictícios, projeto completo no GitHub: <link do seu repositório>

#Databricks #AnalyticsEngineering #Dados
