import pandas as pd
import os

print("Iniciando camada SILVER...")

# LEITURA

df = pd.read_parquet("bronze/antt_trafego_raw.parquet")

print("Linhas recebidas:", len(df))

# PADRONIZAÇÃO TEXTO

cols_texto = ["concessionaria", "sentido", "praca", "tipo_cobranca", "tipo_de_veiculo"]

for col in cols_texto:
    df[col] = df[col].str.strip().str.upper()

# NORMALIZAÇÃO VEÍCULO

df["tipo_de_veiculo"] = df["tipo_de_veiculo"].replace({
    "VEÍCULO PEQUENO": "PASSEIO"
})

# NUMÉRICOS

df["volume_total"] = (
    df["volume_total"]
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df["volume_total"] = pd.to_numeric(df["volume_total"], errors="coerce")

df["categoria_eixo"] = pd.to_numeric(
    df["categoria_eixo"].str.extract(r"(\d+)")[0],
    errors="coerce"
)

# FILTRO MENSAL

print(df["arquivo_origem"].drop_duplicates().to_list())

df = df[
    ~df["arquivo_origem"]
    .str.lower()
    .str.contains("diário|diario", na=False)
]

print(df["arquivo_origem"].str.contains("Diário", case=False).sum())

print("Após filtro mensal:", len(df))

# DATA

df["mes_ano"] = df["mes_ano"].astype(str).str.strip().str.lower()

# tentativa padrão
data_padrao = pd.to_datetime(df["mes_ano"], dayfirst=True, errors="coerce")

# detectar jan/2026
mask_texto = df["mes_ano"].str.match(r"^[a-z]{3}/\d{4}$", na=False)

if mask_texto.any():

    map_meses = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12"
    }

    split = df.loc[mask_texto, "mes_ano"].str.split("/", expand=True)

    mes = split[0].str[:3].map(map_meses)
    ano = split[1]

    data_texto = pd.to_datetime(ano + "-" + mes + "-01", errors="coerce")

    data_padrao.loc[mask_texto] = data_texto

df["mes_ano"] = data_padrao

# REMOVER INVÁLIDOS

antes = len(df)

df = df.dropna(subset=["mes_ano", "volume_total"])

print("Removidos inválidos:", antes - len(df))

# AGREGAÇÃO

chave = [
    "concessionaria",
    "mes_ano",
    "sentido",
    "praca",
    "tipo_cobranca",
    "categoria_eixo",
    "tipo_de_veiculo"
]

antes = len(df)

df = df.groupby(chave, as_index=False)["volume_total"].sum()

print("Após agregação:", len(df))
print("Consolidados:", antes - len(df))

# OUTPUT

os.makedirs("silver", exist_ok=True)

df.to_parquet("silver/antt_trafego_silver.parquet")

print("SILVER concluída")