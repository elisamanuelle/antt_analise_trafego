import requests
import pandas as pd
import os
import time
import unicodedata
import re

print("Iniciando camada BRONZE...")

# CONFIG

DATASET = "volume-trafego-praca-pedagio"
API = f"https://dados.antt.gov.br/api/3/action/package_show?id={DATASET}"

headers = {"User-Agent": "Mozilla/5.0"}

PASTA_DADOS = "dados_antt"
os.makedirs(PASTA_DADOS, exist_ok=True)

os.makedirs("log", exist_ok=True)
os.makedirs("bronze", exist_ok=True)
os.makedirs("evidencias", exist_ok=True)

# FUNÇÃO UTIL

def normalizar_texto(texto):
    if pd.isna(texto):
        return texto
    return (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ascii", errors="ignore")
        .decode("utf-8")
        .lower()
    )

# COLETA METADADOS

response = requests.get(API, headers=headers, timeout=60)
resources = response.json()["result"]["resources"]

log_recursos = []

for r in resources:
    log_recursos.append({
        "nome_original": r["name"],
        "nome_normalizado": normalizar_texto(r["name"]),
        "formato": r["format"],
        "url": r["url"],
        "data_coleta": pd.Timestamp.now()
    })

pd.DataFrame(log_recursos).to_csv("log/log_recursos_antt.csv", index=False)

print("Log atualizado:", len(log_recursos), "recursos")

# MAPEAR ARQUIVOS POR ANO

mapa_anos = {}

for r in resources:

    if str(r["format"]).lower() != "csv":
        continue

    nome_norm = normalizar_texto(r["name"])

    match = re.search(r"(20\d{2})", nome_norm)
    if not match:
        continue

    ano = int(match.group(1))

    if ano not in mapa_anos:
        mapa_anos[ano] = []

    mapa_anos[ano].append({
        "resource": r,
        "nome_norm": nome_norm
    })

# ESCOLHER MELHOR ARQUIVO

arquivos_selecionados = []

for ano, lista in mapa_anos.items():

    if ano < 2016:
        continue

    consolidados = [x for x in lista if "consolidado" in x["nome_norm"]]
    normais = [
        x for x in lista
        if "consolidado" not in x["nome_norm"]
        and "diario" not in x["nome_norm"]
    ]

    if consolidados:
        escolhido = consolidados[0]
    elif normais:
        escolhido = normais[0]
    else:
        continue

    arquivos_selecionados.append((ano, escolhido))


print("Anos selecionados:", sorted([x[0] for x in arquivos_selecionados]))

# DOWNLOAD

arquivos = []

for ano, item in arquivos_selecionados:

    r = item["resource"]
    nome_original = r["name"]
    nome_norm = item["nome_norm"]

    nome_arquivo = nome_norm.replace(" ", "_") + ".csv"
    caminho = os.path.join(PASTA_DADOS, nome_arquivo)

    if not os.path.exists(caminho):

        print(f"Baixando: {nome_original} ({ano})")

        for tentativa in range(3):
            try:
                resp = requests.get(r["url"], headers=headers, timeout=180)
                with open(caminho, "wb") as f:
                    f.write(resp.content)
                break
            except Exception:
                print("Erro download, retry...")
                time.sleep(5)

    arquivos.append((caminho, nome_arquivo, nome_original))


print("Arquivos válidos:", len(arquivos))

# LEITURA

colunas = [
    "concessionaria",
    "mes_ano",
    "sentido",
    "praca",
    "tipo_cobranca",
    "categoria_eixo",
    "tipo_de_veiculo",
    "volume_total"
]

dfs = []

for caminho, nome_arquivo, nome_original in arquivos:

    try:

        df_temp = pd.read_csv(
            caminho,
            encoding="latin1",
            sep=";",
            header=None,
            dtype=str,
            low_memory=False
        )

        df_temp = df_temp.iloc[:, :8]
        df_temp.columns = colunas

        # remover headers duplicados
        df_temp = df_temp[
            ~df_temp["concessionaria"]
            .str.lower()
            .str.contains("concessionaria", na=False)
        ]

        df_temp["arquivo_origem"] = nome_arquivo
        df_temp["arquivo_original"] = nome_original

        dfs.append(df_temp)

    except Exception as e:
        print("Erro leitura:", nome_arquivo)
        print(e)

# CONSOLIDAÇÃO

df = pd.concat(dfs, ignore_index=True)

print("Linhas brutas:", len(df))

# DEDUPLICAÇÃO

df["linha_hash"] = (
    df[
        [
            "concessionaria",
            "mes_ano",
            "sentido",
            "praca",
            "tipo_cobranca",
            "categoria_eixo",
            "tipo_de_veiculo",
            "volume_total"
        ]
    ]
    .astype(str)
    .agg("|".join, axis=1)
)

antes = len(df)
df = df.drop_duplicates(subset=["linha_hash"])

print("Removidos duplicados:", antes - len(df))

# DIAGNÓSTICO

print("\n=== DIAGNÓSTICO ===")

nulls = df.isna().sum().reset_index()
nulls.columns = ["coluna", "qtd_nulos"]
nulls["percentual"] = (nulls["qtd_nulos"] / len(df)) * 100
nulls.to_csv("evidencias/nulos.csv", index=False)

duplicados = df[df.duplicated()]
duplicados.head(1000).to_csv("evidencias/duplicados_amostra.csv", index=False)

print("Duplicados restantes:", len(duplicados))

# OUTPUT

df.to_parquet("bronze/antt_trafego_raw.parquet", index=False)

print("Concluído")
