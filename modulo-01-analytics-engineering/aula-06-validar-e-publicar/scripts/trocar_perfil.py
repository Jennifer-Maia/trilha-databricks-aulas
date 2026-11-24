"""Troca o SEU perfil na tabela de acesso (o mesmo trocar_perfil da aula 5). Usado no erro de propósito.

Uso: python3 trocar_perfil.py vendas Sudeste      → você passa a ver só o Sudeste
     python3 trocar_perfil.py financeiro          → volta a ver tudo (o mesmo que voltar_financeiro.py)
Muda só a SUA linha em governanca.acesso_usuarios.
"""
import sys

from comum import ler_parametros, perfil_atual, trocar_perfil

if len(sys.argv) < 2:
    sys.exit(__doc__)
p = ler_parametros()
trocar_perfil(p, sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
print(f"✅ Perfil agora: {perfil_atual(p)}")
