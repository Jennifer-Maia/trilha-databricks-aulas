"""Comando 02 · Cria (ou atualiza) e publica o painel da Marina a partir de painel_marina.json.

Uso: python3 criar_painel.py
O painel lê só gold.vendas_por_regiao. É publicado SEM credencial embutida: cada pessoa vê os dados
com o próprio acesso, então o filtro de linha da aula 5 (RN-08) continua valendo.
"""
import json
import pathlib

from comum import cli, host, ler_parametros, salvar_parametros

p = ler_parametros()
eu = cli(["current-user", "me"], p["perfil_cli"])["userName"]
pasta = f"/Workspace/Users/{eu}/jornada-portfolio"
cli(["workspace", "mkdirs", pasta], p["perfil_cli"])

painel = (pathlib.Path(__file__).parent / "painel_marina.json").read_text()
comum = ["--warehouse-id", p["warehouse_id"], "--dataset-catalog", p["catalogo"],
         "--dataset-schema", "gold", "--serialized-dashboard", painel]

if p.get("painel_id"):
    cli(["lakeview", "update", p["painel_id"], *comum], p["perfil_cli"])
    print("✅ Painel atualizado")
else:
    r = cli(["lakeview", "create", "--display-name", "Chamado #482 · Vendas por região", *comum,
             "--json", json.dumps({"parent_path": pasta})], p["perfil_cli"])
    p["painel_id"] = r["dashboard_id"]
    salvar_parametros(p)
    print("✅ Painel criado")

# embed-credentials=false: o painel roda com o acesso de QUEM ABRE, não de quem publicou
cli(["lakeview", "publish", p["painel_id"], "--warehouse-id", p["warehouse_id"],
     "--embed-credentials=false"], p["perfil_cli"])
print("✅ Painel publicado sem credencial embutida (cada pessoa vê com o próprio acesso)")
print(f"\nAbra: {host(p['perfil_cli'])}/sql/dashboardsv3/{p['painel_id']}/published")
