import pandas as pd
import os

print("Iniciando camada SILVER...")

# LEITURA

df = pd.read_parquet("bronze/antt_trafego_raw.parquet")
print("Linhas recebidas:", len(df))

# PADRONIZAÇÃO DE TEXTO

cols_texto = [
    "concessionaria",
    "sentido",
    "praca",
    "tipo_cobranca",
    "tipo_de_veiculo"
]

for col in cols_texto:
    df[col] = df[col].astype(str).str.strip().str.upper()

# NORMALIZAÇÃO DE DOMÍNIOS

df["tipo_de_veiculo"] = df["tipo_de_veiculo"].replace({
    "VEÍCULO PEQUENO": "PASSEIO",
    "VEICULO PEQUENO": "PASSEIO"
})

# TRATAMENTO NUMÉRICO

df["volume_total"] = (
    df["volume_total"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df["volume_total"] = pd.to_numeric(df["volume_total"], errors="coerce")

df["categoria_eixo"] = pd.to_numeric(
    df["categoria_eixo"].astype(str).str.extract(r"(\d+)")[0],
    errors="coerce"
)

# TRATAMENTO DE DATA

df["mes_ano_raw"] = df["mes_ano"].astype(str).str.strip()

# formato dd/mm/yyyy
df["mes_ano"] = pd.to_datetime(
    df["mes_ano_raw"],
    format="%d/%m/%Y",
    errors="coerce"
)

# formato mm/yyyy
mask = df["mes_ano"].isna()

if mask.any():
    df.loc[mask, "mes_ano"] = pd.to_datetime(
        "01/" + df.loc[mask, "mes_ano_raw"],
        format="%d/%m/%Y",
        errors="coerce"
    )

# padroniza início do mês
df["mes_ano"] = df["mes_ano"].dt.to_period("M").dt.to_timestamp()

# INVESTIGAÇÃO DE CONFLITOS

chave = [
    "concessionaria",
    "mes_ano",
    "praca",
    "tipo_de_veiculo",
    "categoria_eixo",
    "sentido",
    "tipo_cobranca"
]

df_conflict = (
    df.groupby(chave)["volume_total"]
    .nunique()
    .reset_index(name="qtd_valores")
)

df_conflict = df_conflict[df_conflict["qtd_valores"] > 1]

print("Grupos com conflito:", len(df_conflict))

# CONSOLIDAÇÃO (RESOLUÇÃO DE CONFLITO)

antes = len(df)

df = df.groupby(chave, as_index=False)["volume_total"].max()

print("Linhas após consolidação:", len(df))
print("Linhas reduzidas:", antes - len(df))

# REMOÇÃO DE REGISTROS INVÁLIDOS

antes = len(df)

df = df[
    df["volume_total"].notna() &
    df["mes_ano"].notna()
]

print("Removidos inválidos:", antes - len(df))

# GARANTIA DE UNICIDADE

antes = len(df)

df = df.drop_duplicates(subset=chave + ["volume_total"])

print("Removidos duplicados residuais:", antes - len(df))

dup = df.duplicated(subset=chave).sum()

print("Duplicidades finais:", dup)

# OUTPUT

os.makedirs("silver", exist_ok=True)

df.to_parquet("silver/antt_trafego_silver.parquet", index=False)

print("Concluído")
