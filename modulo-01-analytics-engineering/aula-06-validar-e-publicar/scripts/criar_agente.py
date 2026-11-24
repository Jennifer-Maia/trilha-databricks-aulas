"""Comando 03 · Cria (ou atualiza) o agente da Marina (Genie) e faz perguntas para ele.

Uso: python3 criar_agente.py [--pergunta "..."] [--como-vendas Sudeste]
- As instruções do agente saem do contrato de dados (RN-04, RN-05, RN-06, período).
- --como-vendas troca o SEU perfil para vendas daquela região, pergunta e volta para financeiro:
  mostra que o agente respeita o filtro de linha da aula 5.
"""
import argparse
import json
import subprocess
import uuid

from comum import cli, host, ler_parametros, salvar_parametros, trocar_perfil

INSTRUCOES = """Você responde a Marina, gerente comercial da loja fictícia, sobre o chamado #482 (vendas por região).
Regras do contrato de dados, que valem para toda resposta:
- Pedido concluído = status atual 'entregue' (RN-04). As tabelas gold já têm só pedidos concluídos: não filtre status.
- Valor da venda = valor com desconto, coluna valor_venda ou valor_vendas (RN-05). Mostre em R$.
- Região = região do IBGE pela UF do cliente; cliente sem UF aparece como 'Não informada' (RN-06). Sempre mostre essa linha.
- Período do chamado: entregas de agosto a outubro de 2026 (coluna mes ou entregue_em).
- Ticket médio = soma do valor dividida pela quantidade de pedidos, nunca a média dos tickets mensais.
- Para totais por região ou mês, prefira gold.vendas_por_regiao. Use gold.pedidos_concluidos só para detalhe de pedido.
- Não mostre e-mail nem telefone de cliente. Se pedirem, diga que é dado protegido (RN-09).
- Se a pergunta sair do contrato (devolução, frete, imposto, produto), diga que não está no escopo do chamado.
Responda em português do Brasil, com o número e a regra usada."""

PERGUNTAS_EXEMPLO = [
    "Quanto vendemos por região de agosto a outubro de 2026?",
    "Qual região teve o maior ticket médio?",
    "Como as vendas evoluíram mês a mês?",
]


def novo_id():
    return uuid.uuid4().hex


def espaco(p):
    eu = p["catalogo"]
    s = {
        "version": 2,
        "config": {"sample_questions": sorted([{"id": novo_id(), "question": [q]} for q in PERGUNTAS_EXEMPLO],
                                              key=lambda x: x["id"])},
        "data_sources": {"tables": [{"identifier": f"{eu}.gold.pedidos_concluidos"},
                                    {"identifier": f"{eu}.gold.vendas_por_regiao"}]},
        "instructions": {"text_instructions": [{"id": novo_id(), "content": [INSTRUCOES]}]},
    }
    return json.dumps(s, ensure_ascii=False)


def perguntar(p, pergunta):
    r = subprocess.run(["databricks", "genie", "start-conversation", p["agente_id"], pergunta,
                        "--profile", p["perfil_cli"], "-o", "json", "--timeout", "5m"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return f"(o agente não respondeu: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'sem mensagem'})", ""
    d = json.loads(r.stdout)
    texto, consulta = "", ""
    for anexo in d.get("attachments") or []:
        if anexo.get("text"):
            texto += anexo["text"].get("content", "")
        if anexo.get("query"):
            consulta = anexo["query"].get("query", "")
    return texto.strip() or "(sem texto)", consulta.strip()


ap = argparse.ArgumentParser()
ap.add_argument("--pergunta", action="append", help="pergunta para o agente (pode repetir)")
ap.add_argument("--como-vendas", metavar="REGIAO", help="pergunta no perfil vendas desta região e volta")
a = ap.parse_args()

p = ler_parametros()
corpo = {"title": "Agente da Marina · Chamado #482", "warehouse_id": p["warehouse_id"],
         "description": "Responde sobre vendas por região com as regras do contrato de dados. Dados fictícios.",
         "serialized_space": espaco(p)}
if p.get("agente_id"):
    # sem o título: reenviar o mesmo nome faz o Databricks tentar criar outro arquivo com esse nome e falhar
    sem_titulo = {k: v for k, v in corpo.items() if k != "title"}
    cli(["genie", "update-space", p["agente_id"], "--json", json.dumps(sem_titulo)], p["perfil_cli"])
    print("✅ Agente atualizado com as instruções do contrato")
else:
    p["agente_id"] = cli(["genie", "create-space", "--json", json.dumps(corpo)], p["perfil_cli"])["space_id"]
    salvar_parametros(p)
    print("✅ Agente criado com as instruções do contrato")
print(f"Abra: {host(p['perfil_cli'])}/genie/rooms/{p['agente_id']}\n")

perguntas = a.pergunta or ["Quantos pedidos concluídos temos no total e qual o valor vendido?"]
if a.como_vendas:
    try:
        trocar_perfil(p, "vendas", a.como_vendas)
        print(f"(perfil trocado para vendas · {a.como_vendas})")
        for q in perguntas:
            texto, _ = perguntar(p, q)
            print(f"❓ {q}\n💬 {texto}\n")
    finally:
        trocar_perfil(p, "financeiro")
        print("(perfil de volta para financeiro)")
else:
    for q in perguntas:
        texto, consulta = perguntar(p, q)
        print(f"❓ {q}\n💬 {texto}\n🔎 SQL que o agente usou:\n{consulta}\n")
