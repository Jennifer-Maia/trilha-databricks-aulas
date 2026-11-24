"""Comando 04 · Gera a ficha do projeto (meu-portfolio/ficha.md) com números tirados das tabelas.

Uso: python3 gerar_ficha.py
Para se o seu perfil não for financeiro: com filtro de linha, o número depende de quem consulta
(no perfil vendas Sudeste a ficha sairia com 528 pedidos, sem nenhum erro).
"""
import json
import shutil
import sys

from comum import AULA, PORTFOLIO, REFERENCIA, ler_parametros, perfil_atual, reais, sql, um

p = ler_parametros()
perfil = perfil_atual(p)
if perfil != "financeiro":
    sys.exit(f"❌ Seu perfil é '{perfil}': a ficha sairia com números filtrados.\n"
             "   Para voltar: python3 voltar_financeiro.py e rode de novo.")

contagem = sql("""SELECT (SELECT COUNT(*) FROM bronze.clientes) AS clientes,
                         (SELECT COUNT(*) FROM bronze.produtos) AS produtos,
                         (SELECT COUNT(*) FROM bronze.pedidos) AS pedidos,
                         (SELECT COUNT(*) FROM bronze.eventos_pedido) AS eventos""", p)[0]
concluidos = int(um("SELECT COUNT(*) FROM gold.pedidos_concluidos", p))
# as três contas da aula 1 (mesmo SQL do Passo 8 da aula 3): o "antes" do projeto
pessoa_a = int(um("SELECT COUNT(*) FROM bronze.eventos_pedido WHERE status = 'entregue'", p))
pessoa_b = int(um("SELECT COUNT(*) FROM bronze.eventos_pedido WHERE lower(status) = 'entregue'", p))
valor = float(um("SELECT ROUND(SUM(valor_venda), 2) FROM gold.pedidos_concluidos", p))
regioes = sql("""SELECT regiao, SUM(quantidade_pedidos) AS pedidos, ROUND(SUM(valor_vendas), 2) AS valor
                 FROM gold.vendas_por_regiao GROUP BY regiao ORDER BY valor DESC""", p)
testes_ok = um("""SELECT COUNT_IF(resultado = 'OK') FROM qualidade.resultados_testes
                  WHERE execucao_id = (SELECT execucao_id FROM qualidade.resultados_testes WHERE teste < 'T10'
                                       GROUP BY execucao_id ORDER BY MAX(executado_em) DESC LIMIT 1)""", p)

if concluidos != REFERENCIA["pedidos"] or abs(valor - REFERENCIA["valor"]) > 0.01:
    sys.exit(f"❌ A gold não bate com o contrato ({concluidos} pedidos, {reais(valor)}). Rode as aulas 2 a 5 de novo.")

campea = regioes[0]
fatia = float(campea["valor"]) / valor
ficha = {
    "fonte": "API do Hugging Face (datasets-server), paginada, com retry e manifesto",
    "clientes": int(contagem["clientes"]), "produtos": int(contagem["produtos"]),
    "pedidos": int(contagem["pedidos"]), "eventos": int(contagem["eventos"]),
    "pedidos_concluidos": concluidos, "valor_vendas": valor,
    "regiao_campea": campea["regiao"], "fatia_campea": round(fatia, 4),
    "pessoa_a": pessoa_a, "pessoa_b": pessoa_b, "regras": 9, "testes_ok": f"{testes_ok} de 9",
}

md = ["# Ficha do projeto", "",
      "> Gerada por `scripts/gerar_ficha.py` a partir das tabelas, no perfil financeiro. Não digite estes números à mão.", "",
      "| | |", "|---|---|",
      f"| Fonte | {ficha['fonte']} |",
      f"| Clientes · produtos · pedidos · eventos | {ficha['clientes']} · {ficha['produtos']} · {ficha['pedidos']} · {ficha['eventos']} |",
      f"| O mesmo chamado, três contas | {pessoa_a} (status exato) · {pessoa_b} (sem tratar duplicados) · **{concluidos}** (contrato) |",
      f"| Pedidos concluídos (ago–out/2026) | {concluidos} |",
      f"| Valor de vendas | {reais(valor)} |",
      f"| Região que mais vendeu | {campea['regiao']} ({fatia:.0%} do valor) |",
      f"| Regras de negócio | 9 (RN-01 a RN-09), cada uma com teste |",
      f"| Testes de qualidade na última rodada | {ficha['testes_ok']} OK |",
      "| Governança | filtro por região (RN-08) e máscara de e-mail e telefone (RN-09) |",
      "| Consumo | painel publicado sem credencial embutida + agente (Genie) com as regras do contrato |",
      "", "## Vendas por região", "", "| Região | Pedidos | Valor |", "|---|---:|---:|"]
md += [f"| {r['regiao']} | {r['pedidos']} | {reais(r['valor'])} |" for r in regioes]

PORTFOLIO.mkdir(exist_ok=True)
(PORTFOLIO / "prints").mkdir(exist_ok=True)
(PORTFOLIO / "img").mkdir(exist_ok=True)
shutil.copy(AULA / "img" / "aula-06-projeto-ponta-a-ponta.svg", PORTFOLIO / "img")
(PORTFOLIO / "ficha.md").write_text("\n".join(md) + "\n")
(PORTFOLIO / "ficha.json").write_text(json.dumps(ficha, indent=2, ensure_ascii=False) + "\n")
print("\n".join(md))
print("\n✅ Ficha gravada em meu-portfolio/ficha.md (e ficha.json)")
