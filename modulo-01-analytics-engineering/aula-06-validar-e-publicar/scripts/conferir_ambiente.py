"""Comando 01 · Confere se o projeto está pronto e grava os parâmetros em meu-portfolio/parametros.json.

Uso: python3 conferir_ambiente.py --perfil-cli <perfil> [--catalogo jornada_comercial] [--warehouse <id>]
Só lê. Não muda nenhuma tabela.
"""
import argparse
import sys

import json

from comum import PARAMETROS, REFERENCIA, cli, perfil_atual, salvar_parametros, um

ap = argparse.ArgumentParser()
ap.add_argument("--perfil-cli", required=True, help="perfil da Databricks CLI (databricks auth profiles)")
ap.add_argument("--catalogo", default="jornada_comercial")
ap.add_argument("--warehouse", help="id do SQL warehouse (se não passar, uso o único que existir)")
a = ap.parse_args()

eu = cli(["current-user", "me"], a.perfil_cli)
print(f"✅ CLI conectada (perfil '{a.perfil_cli}')")

if a.warehouse:
    wh = a.warehouse
else:
    lista = cli(["warehouses", "list"], a.perfil_cli)
    if not lista:
        sys.exit("❌ Nenhum SQL warehouse no workspace. Na Free Edition existe o 'Serverless Starter Warehouse'.")
    wh = lista[0]["id"]
    print(f"✅ SQL warehouse: {lista[0]['name']} ({wh})")

# mantém os ids do painel e do agente se você já rodou os comandos 02 e 03 (rodar de novo não duplica nada)
antigo = json.loads(PARAMETROS.read_text()) if PARAMETROS.exists() else {}
if antigo.get("catalogo") != a.catalogo:
    antigo = {}
p = {**antigo, "perfil_cli": a.perfil_cli, "catalogo": a.catalogo, "warehouse_id": wh}

for tabela in ["gold.pedidos_concluidos", "gold.vendas_por_regiao", "governanca.acesso_usuarios"]:
    um(f"SELECT 1 FROM {tabela} LIMIT 1", p)   # sai com erro se a tabela não existir
    print(f"✅ {a.catalogo}.{tabela} existe")

perfil = perfil_atual(p)
if perfil != "financeiro":
    sys.exit(f"⚠️  Seu perfil na tabela de acesso é '{perfil}'. Os números sairiam filtrados (o '528' da aula 6).\n"
             "   Para voltar: python3 voltar_financeiro.py --perfil-cli <perfil> --catalogo <catálogo>")
print("✅ Perfil na tabela de acesso: financeiro")

pedidos = int(um("SELECT COUNT(*) FROM gold.pedidos_concluidos", p))
marca = "✅" if pedidos == REFERENCIA["pedidos"] else "⚠️ "
print(f"{marca} Pedidos concluídos na gold: {pedidos} (contrato: {REFERENCIA['pedidos']})")
if pedidos != REFERENCIA["pedidos"]:
    sys.exit("   A gold não bate com o contrato. Rode as aulas 2 a 5 de novo antes de publicar.")

salvar_parametros(p)
print("\nParâmetros gravados em meu-portfolio/parametros.json. Pode seguir para o comando 02.")
