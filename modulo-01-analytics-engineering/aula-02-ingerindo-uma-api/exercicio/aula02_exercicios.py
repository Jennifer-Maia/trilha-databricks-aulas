# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 2 · Exercícios: construa a sua ingestão
# MAGIC
# MAGIC Na aula a gente viu a ingestão pronta. Aqui é você quem constrói, **um pedaço por vez**:
# MAGIC
# MAGIC | # | Exercício | O que você pratica |
# MAGIC |---|---|---|
# MAGIC | 1 | Ler a resposta | chamar a API e achar o total e as colunas no JSON |
# MAGIC | 2 | Quem errou? | decidir, pelo código HTTP, se segue, para ou tenta de novo |
# MAGIC | 3 | Quantas chamadas? | planejar a paginação antes de chamar |
# MAGIC | 4 | Tentar de novo | escrever o retry, testado numa API de mentira (sem esperar minutos) |
# MAGIC | 5 | A fonte mudou? | comparar as colunas recebidas com o contrato |
# MAGIC | 6 | A carga de verdade | juntar tudo e gravar uma tabela na landing, com manifesto |
# MAGIC
# MAGIC **Como funciona:** escreva o seu código onde estiver `✏️`, rode a célula e depois rode a célula **Conferir** logo abaixo.
# MAGIC Ela mostra ✅ ou ❌ para cada caso. Ficou ❌? Leia a dica e tente de novo. O gabarito está em `solucao/aula02_exercicios_gabarito`.
# MAGIC
# MAGIC Antes: rode `setup/01_criar_ambiente` com o mesmo catálogo. Conecte no **Serverless**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preparação (só rodar)

# COMMAND ----------

import json, os, time
from datetime import datetime, timezone
import requests

dbutils.widgets.text("catalogo", "jornada_comercial")
dbutils.widgets.text("dataset_hf", "trilhajornadadatabricks/loja-ficticia-jornada")
CAT = dbutils.widgets.get("catalogo")
DATASET = dbutils.widgets.get("dataset_hf")

API = "https://datasets-server.huggingface.co/rows"
LANDING = f"/Volumes/{CAT}/raw/landing"
CABECALHOS = {"User-Agent": "jornada-dados-lab/1.0"}
COLUNAS_ESPERADAS = {
    "clientes": ["customer_id", "nome", "email", "telefone", "cidade", "uf", "cadastrado_em"],
    "produtos": ["product_id", "nome", "categoria", "preco"],
    "pedidos": ["order_id", "customer_id", "criado_em", "itens", "valor_bruto", "valor_liquido"],
    "eventos_pedido": ["event_id", "order_id", "status", "event_ts", "canal"],
}

def conferir(exercicio, casos):
    """Roda cada caso (descrição, função que devolve True/False) e mostra ✅ ou ❌."""
    tudo_certo = True
    for descricao, caso in casos:
        try:
            passou, detalhe = bool(caso()), ""
        except NotImplementedError:
            print(f"⏳ {exercicio}: ainda falta escrever o código.")
            return
        except Exception as e:
            passou, detalhe = False, f"  →  {type(e).__name__}: {e}"
        print(("✅ " if passou else "❌ ") + descricao + detalhe)
        tudo_certo = tudo_certo and passou
    print(f"\n🎉 {exercicio}: tudo certo!" if tudo_certo else f"\n{exercicio}: ainda não. Releia a dica e tente de novo.")

def preenchido(valor):
    """Para a conferência com ⏳ enquanto a variável ainda estiver None."""
    if valor is None:
        raise NotImplementedError
    return True

print(f"Catálogo: {CAT} | Landing: {LANDING}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 1 · Ler a resposta
# MAGIC
# MAGIC Peça **5 linhas** da tabela `produtos` à API e preencha as três variáveis:
# MAGIC
# MAGIC - `corpo`: a resposta já convertida de JSON para dicionário Python.
# MAGIC - `total_produtos`: quantos produtos existem na fonte (não quantos vieram!).
# MAGIC - `colunas_produtos`: a lista com o **nome** de cada coluna.
# MAGIC
# MAGIC **Dica:** os parâmetros são `dataset`, `config`, `split` (sempre `"train"`), `offset` e `length`.
# MAGIC Depois de chamar, olhe as chaves com `print(list(corpo))`. O total e as colunas estão em duas delas.

# COMMAND ----------

# ✏️ Exercício 1: chame a API e preencha as variáveis (troque os None)
r = None
corpo = None
total_produtos = None
colunas_produtos = None
print("Vieram", len(corpo["rows"]) if corpo else 0, "linhas nesta chamada")

# COMMAND ----------

conferir("Exercício 1", [
    ("corpo é um dicionário com a chave 'rows'", lambda: preenchido(corpo) and isinstance(corpo, dict) and "rows" in corpo),
    ("vieram 5 linhas, como você pediu", lambda: len(corpo["rows"]) == 5),
    ("total_produtos é o total da fonte (não o que veio nesta chamada)", lambda: total_produtos == 60),
    ("colunas_produtos tem os nomes das colunas", lambda: sorted(colunas_produtos) == sorted(COLUNAS_ESPERADAS["produtos"])),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 2 · Quem errou?
# MAGIC
# MAGIC Escreva `classificar(status)`, que recebe um código HTTP e devolve **uma** destas três palavras:
# MAGIC
# MAGIC | Devolver | Quando |
# MAGIC |---|---|
# MAGIC | `"seguir"` | deu certo |
# MAGIC | `"tentar_de_novo"` | a falha é passageira: limite de chamadas ou o servidor falhou |
# MAGIC | `"parar"` | o erro é nosso (pedido errado): tentar de novo não resolve |
# MAGIC
# MAGIC **Dica:** volte na tabela de códigos do README da aula. Quais códigos são "passageiros"? Guarde-os num conjunto (`{...}`).

# COMMAND ----------

def classificar(status):
    # ✏️ Exercício 2
    raise NotImplementedError

# COMMAND ----------

conferir("Exercício 2", [
    ("200 → seguir", lambda: classificar(200) == "seguir"),
    ("429 (chamadas demais) → tentar_de_novo", lambda: classificar(429) == "tentar_de_novo"),
    ("502 e 503 (servidor caiu) → tentar_de_novo", lambda: classificar(502) == classificar(503) == "tentar_de_novo"),
    ("404 (tabela não existe) → parar", lambda: classificar(404) == "parar"),
    ("422 (pediu mais de 100 linhas) → parar", lambda: classificar(422) == "parar"),
    ("400 (pedido mal feito) → parar", lambda: classificar(400) == "parar"),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 3 · Quantas chamadas?
# MAGIC
# MAGIC Antes de sair chamando, planeje. Escreva `planejar_offsets(total, tamanho=100)`, que devolve a lista de `offset`
# MAGIC de cada chamada. Exemplo: `planejar_offsets(250)` → `[0, 100, 200]`.
# MAGIC
# MAGIC **Dica:** o `range` do Python aceita um terceiro número, o "passo": `range(início, fim, passo)`.

# COMMAND ----------

def planejar_offsets(total, tamanho=100):
    # ✏️ Exercício 3
    raise NotImplementedError

# COMMAND ----------

conferir("Exercício 3", [
    ("250 linhas → [0, 100, 200]", lambda: planejar_offsets(250) == [0, 100, 200]),
    ("60 produtos → 1 chamada", lambda: planejar_offsets(60) == [0]),
    ("100 linhas certinhas → 1 chamada (não 2)", lambda: planejar_offsets(100) == [0]),
    ("1.500 pedidos → 15 chamadas, a última no offset 1400", lambda: len(planejar_offsets(1500)) == 15 and planejar_offsets(1500)[-1] == 1400),
    ("5.416 eventos → 55 chamadas", lambda: len(planejar_offsets(5416)) == 55),
    ("tabela vazia → nenhuma chamada", lambda: planejar_offsets(0) == []),
])

# COMMAND ----------

# MAGIC %md
# MAGIC Agora responda com o seu código: quantas chamadas a carga inteira faz? Compare com o limite de ~40 a 55 chamadas
# MAGIC seguidas que a API aguentou nos nossos testes. É por isso que o 429 aparece.

# COMMAND ----------

TOTAIS = {"clientes": 500, "produtos": 60, "pedidos": 1500, "eventos_pedido": 5416}
try:
    print("Chamadas na carga inteira:", sum(len(planejar_offsets(n)) for n in TOTAIS.values()))
except NotImplementedError:
    print("Faça o exercício 3 primeiro.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 4 · Tentar de novo (retry)
# MAGIC
# MAGIC Testar retry com a API de verdade é lento (o 429 manda esperar 60 s). Então aqui você testa numa **API de mentira**:
# MAGIC `api_falsa([502, 200])` cria uma função que, a cada chamada, responde o próximo status da lista.
# MAGIC E a espera não é de verdade: a conferência troca o `time.sleep` por uma função que só anota quanto você esperaria.
# MAGIC
# MAGIC Escreva `com_retry(chamar, tentativas=4, espera=2, espera_429=60, dormir=time.sleep)`:
# MAGIC
# MAGIC 1. Chame `r = chamar()` e use o seu `classificar(r.status_code)`.
# MAGIC 2. `"seguir"` → devolva `r`. `"parar"` → `raise RuntimeError(...)` na hora.
# MAGIC 3. `"tentar_de_novo"` → `dormir(...)` e repita. No 429 espere `espera_429`; nos outros, `espera`, que **dobra** a cada vez.
# MAGIC 4. Se `chamar()` levantar `requests.exceptions.Timeout` ou `ConnectionError`, também é passageiro: espere e repita.
# MAGIC 5. Acabaram as tentativas → `raise RuntimeError("Desisti ...")`. Não espere depois da última.
# MAGIC
# MAGIC **Dica:** um `for tentativa in range(1, tentativas + 1):` com um `try/except` dentro.

# COMMAND ----------

class RespostaFalsa:
    def __init__(self, status_code):
        self.status_code, self.text = status_code, f'{{"status": {status_code}}}'

def api_falsa(sequencia):
    """Cada chamada devolve o próximo item da lista: um status HTTP ou uma exceção (que é levantada)."""
    fila = list(sequencia)
    def chamar():
        chamar.chamadas += 1
        item = fila.pop(0)
        if isinstance(item, Exception):
            raise item
        return RespostaFalsa(item)
    chamar.chamadas = 0
    return chamar

# COMMAND ----------

def com_retry(chamar, tentativas=4, espera=2, espera_429=60, dormir=time.sleep):
    # ✏️ Exercício 4
    raise NotImplementedError

# COMMAND ----------

def rodar(sequencia):
    """Roda o seu com_retry na API de mentira. Devolve (resultado, quantas chamadas, lista de esperas)."""
    esperas, chamar = [], api_falsa(sequencia)
    try:
        resultado = com_retry(chamar, dormir=esperas.append).status_code
    except NotImplementedError:
        raise
    except RuntimeError as e:
        resultado = "RuntimeError: " + str(e)
    return resultado, chamar.chamadas, esperas

conferir("Exercício 4", [
    ("[200] → devolve na 1ª chamada, sem esperar", lambda: rodar([200]) == (200, 1, [])),
    ("[502, 503, 200] → espera 2 s, depois 4 s, e devolve", lambda: rodar([502, 503, 200]) == (200, 3, [2, 4])),
    ("[429, 200] → espera os 60 s do limite", lambda: rodar([429, 200]) == (200, 2, [60])),
    ("[Timeout, 200] → rede caiu também é passageiro", lambda: rodar([requests.exceptions.Timeout(), 200])[:2] == (200, 2)),
    ("[404] → para na 1ª chamada, com RuntimeError", lambda: rodar([404])[0].startswith("RuntimeError") and rodar([404])[1] == 1),
    ("[502, 502, 502, 502] → desiste depois de 4, sem esperar depois da última",
        lambda: (lambda res: res[0].startswith("RuntimeError") and res[1:] == (4, [2, 4, 8]))(rodar([502] * 4))),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 5 · A fonte mudou?
# MAGIC
# MAGIC Escreva `comparar_colunas(esperadas, recebidas)`, que devolve **duas listas**: `(faltando, novas)`.
# MAGIC
# MAGIC - `faltando`: estão no contrato, mas não vieram. Isso vai **parar** a carga.
# MAGIC - `novas`: vieram, mas não estão no contrato. Isso só gera um **aviso**.
# MAGIC
# MAGIC Mantenha a ordem em que as colunas aparecem em cada lista.

# COMMAND ----------

def comparar_colunas(esperadas, recebidas):
    # ✏️ Exercício 5
    raise NotImplementedError

# COMMAND ----------

conferir("Exercício 5", [
    ("tudo igual → nada faltando, nada novo", lambda: comparar_colunas(["a", "b"], ["a", "b"]) == ([], [])),
    ("ordem diferente não é problema", lambda: comparar_colunas(["a", "b"], ["b", "a"]) == ([], [])),
    ("renomearam valor_liquido → falta uma e aparece outra",
        lambda: comparar_colunas(["order_id", "valor_liquido"], ["order_id", "valor_liq"]) == (["valor_liquido"], ["valor_liq"])),
    ("coluna extra → só aparece em novas", lambda: comparar_colunas(["a"], ["a", "x", "y"]) == ([], ["x", "y"])),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 6 · A carga de verdade
# MAGIC
# MAGIC Hora de juntar tudo. As peças abaixo já estão prontas (só rodar): `chamar_api` usa o **seu** `com_retry` com a API de verdade,
# MAGIC e `validar` usa o **seu** `comparar_colunas`.

# COMMAND ----------

def chamar_api(tabela, offset):
    params = {"dataset": DATASET, "config": tabela, "split": "train", "offset": offset, "length": 100}
    return com_retry(lambda: requests.get(API, params=params, headers=CABECALHOS, timeout=30), tentativas=6)

def validar(tabela, features):
    faltando, novas = comparar_colunas(COLUNAS_ESPERADAS[tabela], [f["name"] for f in features])
    if faltando:
        raise ValueError(f"{tabela}: a fonte mudou! Faltando: {faltando}. Novas: {novas}")
    if novas:
        print(f"   Aviso {tabela}: colunas novas na fonte: {novas}")

def agora():
    return datetime.now(timezone.utc).isoformat()

# COMMAND ----------

# MAGIC %md
# MAGIC Agora escreva `baixar(tabela, carga_id)`. Ela grava em `LANDING/<tabela>/carga_<carga_id>/`:
# MAGIC
# MAGIC 1. Crie a pasta (`os.makedirs(pasta, exist_ok=True)`).
# MAGIC 2. Chame a **primeira página** (offset 0). Dela você tira o total (`num_rows_total`) e confere as colunas com `validar`.
# MAGIC 3. Com o total, use o seu `planejar_offsets` para saber as outras páginas.
# MAGIC 4. Grave cada resposta **crua** (`r.text`) em `pagina_0000.json`, `pagina_0001.json`… (`f"pagina_{n:04d}.json"`)
# MAGIC    e some as linhas de cada página. Faça `time.sleep(1)` entre as chamadas.
# MAGIC 5. Se a soma das linhas não bater com o total, `raise RuntimeError` **sem** escrever o manifesto.
# MAGIC 6. Bateu? Escreva o `_manifesto.json` com estas chaves e devolva o dicionário:
# MAGIC    `tabela`, `carga_id`, `fonte` (= `API`), `dataset`, `paginas`, `linhas`, `num_rows_total`, `inicio_utc`, `fim_utc` (use `agora()`) e `status` (= `"completa"`).
# MAGIC
# MAGIC **Dica:** a primeira resposta você já tem; não chame o offset 0 duas vezes.

# COMMAND ----------

def baixar(tabela, carga_id):
    # ✏️ Exercício 6
    raise NotImplementedError

# COMMAND ----------

# MAGIC %md
# MAGIC Teste com `clientes` (500 linhas, 5 páginas). Leva uns 10 segundos.

# COMMAND ----------

CARGA_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
pasta_clientes = f"{LANDING}/clientes/carga_{CARGA_ID}"
m, erro = None, None
try:
    m = baixar("clientes", CARGA_ID)
except NotImplementedError:
    pass
except Exception as e:
    erro = e

def devolveu_manifesto():
    if erro:
        raise erro
    if m is None:
        raise NotImplementedError
    return m["linhas"] == 500

def manifesto_gravado():
    with open(f"{pasta_clientes}/_manifesto.json") as f:
        return json.load(f)

conferir("Exercício 6", [
    ("baixar devolveu o manifesto com 500 linhas", devolveu_manifesto),
    ("5 arquivos de página na pasta", lambda: sorted(a for a in os.listdir(pasta_clientes) if a.startswith("pagina_")) == [f"pagina_{n:04d}.json" for n in range(5)]),
    ("a página foi gravada crua (tem features, rows e num_rows_total)", lambda: {"features", "rows", "num_rows_total"} <= set(json.load(open(f"{pasta_clientes}/pagina_0000.json")))),
    ("_manifesto.json gravado com 500 linhas e status completa", lambda: manifesto_gravado()["linhas"] == 500 and manifesto_gravado()["status"] == "completa"),
    ("manifesto tem todas as chaves", lambda: {"tabela", "carga_id", "fonte", "dataset", "paginas", "linhas", "num_rows_total", "inicio_utc", "fim_utc", "status"} <= set(manifesto_gravado())),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Fechando: as outras 3 tabelas
# MAGIC
# MAGIC Passou no exercício 6? Rode a célula abaixo para buscar as outras tabelas com o **seu** código, na mesma carga.
# MAGIC Leva de 2 a 6 minutos. Se aparecer `HTTP 429 ... nova tentativa em 60s`, é o seu retry funcionando.
# MAGIC
# MAGIC Depois rode `teste/aula02_conferir_landing`. Se terminar com `Landing completa: todos os testes OK`, a sua ingestão está pronta para a aula 3.

# COMMAND ----------

if m is None:
    print("Termine o exercício 6 antes de rodar esta célula.")
else:
    for tabela in ["produtos", "pedidos", "eventos_pedido"]:
        mt = baixar(tabela, CARGA_ID)
        print(f"{tabela}: {mt['linhas']} linhas em {mt['paginas']} páginas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Desafios extras (sem gabarito)
# MAGIC
# MAGIC 1. Acrescente `duracao_s` ao manifesto: quantos segundos a carga levou.
# MAGIC 2. Escreva `ultima_carga_completa(tabela)`, que devolve a pasta mais recente **com** manifesto. Compare com o que o notebook de teste faz.
# MAGIC 3. Em `COLUNAS_ESPERADAS`, troque `"valor_liquido"` por `"valor_liq"` e rode `baixar("pedidos", ...)`. Em que momento a carga para? Sobra alguma pasta sem manifesto?
