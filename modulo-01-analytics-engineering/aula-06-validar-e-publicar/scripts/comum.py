"""Peças usadas por todos os scripts da aula 6.

Tudo passa pela Databricks CLI (`databricks ...`), com o perfil que você escolheu no comando 01.
Nenhum script apaga tabela: eles só leem a gold, criam o painel e o agente, e escrevem em `meu-portfolio/`.
"""
import json
import pathlib
import subprocess
import sys

AULA = pathlib.Path(__file__).resolve().parent.parent
PORTFOLIO = AULA / "meu-portfolio"
PARAMETROS = PORTFOLIO / "parametros.json"
REFERENCIA = {"pedidos": 1052, "valor": 2302177.12}   # contrato de dados, semente 42


def cli(args, perfil, entrada=None):
    """Roda `databricks <args> --profile <perfil> -o json` e devolve o JSON da resposta."""
    cmd = ["databricks", *args, "--profile", perfil, "-o", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True, input=entrada)
    if r.returncode != 0:
        ultima = (r.stderr.strip().splitlines() or ["(sem mensagem)"])[-1]
        sys.exit(f"❌ Falhou: databricks {' '.join(args[:2])}\n   {ultima}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def sql(consulta, p):
    """Roda uma consulta no SQL warehouse e devolve uma lista de dicionários."""
    corpo = {"statement": consulta, "warehouse_id": p["warehouse_id"], "catalog": p["catalogo"],
             "wait_timeout": "50s", "on_wait_timeout": "CANCEL"}
    r = cli(["api", "post", "/api/2.0/sql/statements", "--json", json.dumps(corpo)], p["perfil_cli"])
    estado = r.get("status", {}).get("state")
    if estado != "SUCCEEDED":
        erro = r.get("status", {}).get("error", {}).get("message", estado)
        sys.exit(f"❌ A consulta falhou: {erro[:300]}")
    colunas = [c["name"] for c in r["manifest"]["schema"]["columns"]]
    return [dict(zip(colunas, linha)) for linha in r.get("result", {}).get("data_array", [])]


def um(consulta, p):
    linhas = sql(consulta, p)
    return next(iter(linhas[0].values())) if linhas else None


def ler_parametros():
    if not PARAMETROS.exists():
        sys.exit("❌ Não achei meu-portfolio/parametros.json. Rode o comando /aula06-01-contexto primeiro.")
    return json.loads(PARAMETROS.read_text())


def salvar_parametros(p):
    PORTFOLIO.mkdir(exist_ok=True)
    PARAMETROS.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n")


def perfil_atual(p):
    return um("SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()", p)


def trocar_perfil(p, perfil, regiao=None):
    """O mesmo da aula 5: muda o SEU perfil na tabela de acesso."""
    valor_regiao = f"'{regiao}'" if regiao else "CAST(NULL AS STRING)"
    sql(f"""MERGE INTO governanca.acesso_usuarios a
            USING (SELECT current_user() AS usuario, '{perfil}' AS perfil, {valor_regiao} AS regiao) n
            ON a.usuario = n.usuario
            WHEN MATCHED THEN UPDATE SET perfil = n.perfil, regiao = n.regiao
            WHEN NOT MATCHED THEN INSERT *""", p)


def reais(valor):
    """2302177.12 → 'R$ 2.302.177,12'"""
    return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def host(perfil):
    r = subprocess.run(["databricks", "auth", "describe", "--profile", perfil, "-o", "json"],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)["details"]["host"].rstrip("/")
    except Exception:
        return None
