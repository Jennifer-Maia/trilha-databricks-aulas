"""Gera os dados da loja fictícia da trilha (clientes, produtos, pedidos e eventos de status).

Os arquivos gerados são publicados como dataset público no Hugging Face. A API do Hugging Face
(datasets-server) transforma esse dataset numa API REST paginada, acessível de dentro da Databricks Free Edition.

Uso (local, sem dependências):
    python3 gerar_dados_loja.py ../../hf_dataset

Semente fixa: todo mundo gera exatamente os mesmos dados, então os números das aulas batem.

Defeitos colocados de propósito (material das aulas 3 e 4):
- eventos duplicados (mesmo event_id);
- status escrito de jeitos diferentes (Entregue, ENTREGUE, delivered, Cancelado, CANCELED);
- eventos sem data;
- eventos de pedidos que não existem (órfãos);
- clientes com UF em minúsculas ou sem UF.
Todos os nomes, e-mails e telefones são inventados.
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta

SEMENTE = 42
N_CLIENTES, N_PRODUTOS, N_PEDIDOS = 500, 60, 1500
INICIO, FIM = datetime(2026, 8, 1), datetime(2026, 10, 31, 23, 59, 59)

# Peso aproximado de clientes por UF (concentração no Sudeste, como no e-commerce brasileiro)
UFS = {"SP": 30, "RJ": 10, "MG": 10, "PR": 6, "RS": 6, "SC": 5, "BA": 6, "PE": 4, "CE": 4, "GO": 3,
       "DF": 3, "ES": 2, "PA": 2, "AM": 2, "MA": 1, "PB": 1, "RN": 1, "AL": 1, "PI": 1, "SE": 1,
       "MT": 1, "MS": 1, "TO": 1, "RO": 1, "AC": 1, "AP": 1, "RR": 1}
CIDADES = {"SP": ["São Paulo", "Campinas", "Santos", "Ribeirão Preto"], "RJ": ["Rio de Janeiro", "Niterói"],
           "MG": ["Belo Horizonte", "Uberlândia"], "PR": ["Curitiba", "Londrina"], "RS": ["Porto Alegre", "Caxias do Sul"],
           "SC": ["Florianópolis", "Joinville"], "BA": ["Salvador", "Feira de Santana"], "PE": ["Recife"],
           "CE": ["Fortaleza"], "GO": ["Goiânia"], "DF": ["Brasília"], "ES": ["Vitória"], "PA": ["Belém"],
           "AM": ["Manaus"]}
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela", "João",
         "Larissa", "Marcos", "Natália", "Otávio", "Paula", "Rafael", "Sofia", "Thiago", "Vanessa", "Yuri"]
SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues", "Almeida",
              "Nascimento", "Carvalho", "Ribeiro", "Gomes", "Martins", "Araújo"]
CATEGORIAS = {"Eletrônicos": (150, 3500), "Casa": (30, 900), "Moda": (40, 400), "Esporte": (50, 1200),
              "Livros": (25, 150), "Beleza": (20, 300)}
STATUS_FLUXO = ["criado", "pago", "enviado", "entregue"]
VARIACOES = {"entregue": ["Entregue", "ENTREGUE", "delivered"], "cancelado": ["Cancelado", "CANCELED"]}


def _ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def gerar(semente=SEMENTE):
    rnd = random.Random(semente)

    clientes = []
    for i in range(1, N_CLIENTES + 1):
        nome, sobrenome = rnd.choice(NOMES), rnd.choice(SOBRENOMES)
        uf = rnd.choices(list(UFS), weights=list(UFS.values()))[0]
        cidade = rnd.choice(CIDADES.get(uf, ["Capital"]))
        clientes.append({
            "customer_id": i,
            "nome": f"{nome} {sobrenome}",
            "email": f"{nome}.{sobrenome}.{i}@exemplo.com.br".lower().replace("á", "a").replace("ã", "a").replace("é", "e").replace("í", "i").replace("ú", "u").replace("ô", "o").replace("ó", "o"),
            "telefone": f"({rnd.randint(11, 99)}) 9{rnd.randint(1000, 9999)}-{rnd.randint(1000, 9999)}",
            "cidade": cidade,
            "uf": uf,
            "cadastrado_em": _ts(INICIO - timedelta(days=rnd.randint(1, 900))),
        })
    for c in rnd.sample(clientes, 8):      # UF em minúsculas
        c["uf"] = c["uf"].lower()
    for c in rnd.sample(clientes, 3):      # sem UF
        c["uf"] = None

    produtos = []
    for i in range(1, N_PRODUTOS + 1):
        cat = rnd.choice(list(CATEGORIAS))
        lo, hi = CATEGORIAS[cat]
        produtos.append({"product_id": i, "nome": f"{cat} item {i:03d}", "categoria": cat,
                         "preco": round(rnd.uniform(lo, hi), 2)})

    pedidos, eventos, seq = [], [], 0
    for order_id in range(1, N_PEDIDOS + 1):
        criado = INICIO + timedelta(seconds=rnd.randint(0, int((FIM - INICIO).total_seconds()) - 10 * 86400))
        itens = []
        for p in rnd.sample(produtos, rnd.randint(1, 4)):
            qtd = rnd.randint(1, 3)
            desc = rnd.choice([0, 0, 0, 5, 10, 15])
            bruto = round(p["preco"] * qtd, 2)
            itens.append({"product_id": p["product_id"], "quantidade": qtd, "preco_unitario": p["preco"],
                          "desconto_pct": desc, "valor_bruto": bruto, "valor_liquido": round(bruto * (1 - desc / 100), 2)})
        pedidos.append({
            "order_id": order_id,
            "customer_id": rnd.randint(1, N_CLIENTES),
            "criado_em": _ts(criado),
            "itens": itens,
            "valor_bruto": round(sum(i["valor_bruto"] for i in itens), 2),
            "valor_liquido": round(sum(i["valor_liquido"] for i in itens), 2),
        })

        sorteio = rnd.random()
        if sorteio < 0.70:
            passos = STATUS_FLUXO
        elif sorteio < 0.82:
            passos = STATUS_FLUXO[: rnd.randint(1, 3)] + ["cancelado"]
        else:
            passos = STATUS_FLUXO[: rnd.randint(1, 3)]
        ts = criado
        for status in passos:
            if status in VARIACOES and rnd.random() < 0.15:
                status = rnd.choice(VARIACOES[status])
            seq += 1
            eventos.append({"event_id": f"ev-{seq:06d}", "order_id": order_id, "status": status,
                            "event_ts": _ts(ts), "canal": rnd.choice(["site", "app", "marketplace"])})
            ts += timedelta(hours=rnd.randint(2, 72))

    for ev in rnd.sample(eventos, k=len(eventos) // 30):       # ~3% duplicados
        eventos.append(dict(ev))
    for ev in rnd.sample(eventos, k=12):                        # sem data
        ev["event_ts"] = None
    for i in range(5):                                          # órfãos
        seq += 1
        eventos.append({"event_id": f"ev-{seq:06d}", "order_id": 90000 + i, "status": "entregue",
                        "event_ts": _ts(FIM - timedelta(days=i)), "canal": "site"})
    rnd.shuffle(eventos)                                        # a API não garante ordem
    return {"clientes": clientes, "produtos": produtos, "pedidos": pedidos, "eventos_pedido": eventos}


def gravar(tabelas, destino):
    os.makedirs(destino, exist_ok=True)
    for nome, linhas in tabelas.items():
        with open(os.path.join(destino, f"{nome}.jsonl"), "w", encoding="utf-8") as f:
            for linha in linhas:
                f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        print(f"{nome}: {len(linhas)} linhas")


if __name__ == "__main__":
    gravar(gerar(), sys.argv[1] if len(sys.argv) > 1 else "./hf_dataset")
