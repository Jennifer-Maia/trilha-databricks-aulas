"""Volta o SEU perfil na tabela de acesso para financeiro (o mesmo trocar_perfil('financeiro') da aula 5).

Uso: python3 voltar_financeiro.py                      (usa meu-portfolio/parametros.json)
     python3 voltar_financeiro.py --perfil-cli <perfil> --catalogo <catálogo>
Muda só a SUA linha em governanca.acesso_usuarios.
"""
import argparse

from comum import PARAMETROS, cli, ler_parametros, perfil_atual, trocar_perfil

ap = argparse.ArgumentParser()
ap.add_argument("--perfil-cli")
ap.add_argument("--catalogo", default="jornada_comercial")
a = ap.parse_args()

if a.perfil_cli:
    lista = cli(["warehouses", "list"], a.perfil_cli)
    p = {"perfil_cli": a.perfil_cli, "catalogo": a.catalogo, "warehouse_id": lista[0]["id"]}
else:
    p = ler_parametros()
trocar_perfil(p, "financeiro")
print(f"✅ Perfil agora: {perfil_atual(p)}")
