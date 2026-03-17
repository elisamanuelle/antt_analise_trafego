import requests
import pandas as pd
import os
import time

DATASET = "volume-trafego-praca-pedagio"
API = f"https://dados.antt.gov.br/api/3/action/package_show?id={DATASET}"

headers = {"User-Agent": "Mozilla/5.0"}

pasta = "dados_antt"
os.makedirs(pasta, exist_ok=True)

response = requests.get(API, headers=headers, timeout=60)
resources = response.json()["result"]["resources"]

# =========================
# LOG DE RECURSOS
# =========================

log_recursos = []

for recurso in resources:
    log_recursos.append({
        "nome": recurso["name"],
        "formato": recurso["format"],
        "tamanho_bytes": recurso.get("size"),
        "url": recurso["url"],
        "data_coleta": pd.Timestamp.now()
    })

log_df = pd.DataFrame(log_recursos)

os.makedirs("log", exist_ok=True)
log_df.to_csv("log/log_recursos_antt.csv", index=False)

print("Log de recursos atualizado")

# =========================
# DOWNLOAD DOS ARQUIVOS
# =========================

arquivos = []

for recurso in resources:

    if recurso["format"].lower() == "csv":

        url = recurso["url"]
        nome = recurso["name"].replace(" ", "_") + ".csv"
        caminho = os.path.join(pasta, nome)

        if not os.path.exists(caminho):

            print("Baixando:", nome)

            for tentativa in range(3):
                try:
                    resp = requests.get(url, headers=headers, timeout=180)
                    with open(caminho, "wb") as f:
                        f.write(resp.content)
                    break
                except Exception:
                    print("Erro de download. Tentando novamente...")
                    time.sleep(5)

        arquivos.append((caminho, nome))  # ← guarda nome junto

# =========================
# LEITURA DOS CSVs
# =========================

dfs = []

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

for caminho, nome_arquivo in arquivos:

    try:

        df_temp = pd.read_csv(
            caminho,
            encoding="latin1",
            sep=";",
            header=None,
            dtype=str,           # 🔥 chave aqui
            low_memory=False
        )

        df_temp = df_temp.iloc[:, :8]
        df_temp.columns = colunas

        # remover cabeçalhos repetidos
        df_temp = df_temp[
            ~df_temp["concessionaria"]
            .str.lower()
            .str.contains("concessionaria", na=False)
        ]

        # 🔥 metadado de origem (MUITO importante)
        df_temp["arquivo_origem"] = nome_arquivo

        dfs.append(df_temp)

    except Exception as e:
        print("Erro ao ler:", caminho)
        print(e)

# =========================
# CONSOLIDAÇÃO
# =========================

df = pd.concat(dfs, ignore_index=True)

print("Linhas totais:", len(df))

# =========================
# DIAGNÓSTICO
# =========================

os.makedirs("evidencias", exist_ok=True)

def diagnostico_dados(df):

    print("\n=== DIAGNÓSTICO DE DADOS ===")

    nulls = df.isna().sum().reset_index()
    nulls.columns = ["coluna", "qtd_nulos"]
    nulls["percentual"] = (nulls["qtd_nulos"] / len(df)) * 100

    nulls.to_csv("evidencias/nulos.csv", index=False)

    duplicados = df[df.duplicated()]
    duplicados.head(1000).to_csv("evidencias/duplicados_amostra.csv", index=False)

    print("Duplicados:", len(duplicados))

    amostras = []

    for col in ["categoria_eixo", "volume_total", "tipo_de_veiculo"]:
        valores = df[col].dropna().unique()[:20]
        for v in valores:
            amostras.append({"coluna": col, "valor": v})

    pd.DataFrame(amostras).to_csv("evidencias/amostra_valores.csv", index=False)

    print("Evidências geradas")

diagnostico_dados(df)

# =========================
# OUTPUT BRONZE
# =========================

os.makedirs("bronze", exist_ok=True)

df.to_parquet("bronze/antt_trafego_raw.parquet")

print("Pipeline BRONZE concluído")