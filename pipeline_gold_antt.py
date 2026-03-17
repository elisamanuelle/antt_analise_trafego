import pandas as pd
import os

print("Iniciando camada GOLD...")

# =========================
# LEITURA
# =========================

df = pd.read_parquet("silver/antt_trafego_silver.parquet")

# remove lixo técnico se existir
df = df.drop(columns=["_index_level_0_"], errors="ignore")

print("Linhas recebidas:", len(df))


# =========================
# MÉTRICAS BASE
# =========================

df["dias_mes"] = df["mes_ano"].dt.days_in_month
df["vmd"] = df["volume_total"] / df["dias_mes"]

# evita problema de NaN na chave
df["categoria_eixo"] = df["categoria_eixo"].fillna(0)

df["fator_desgaste"] = df["categoria_eixo"].replace(0, 1) ** 4


# =========================
# DIMENSÕES
# =========================

# TEMPO
dim_tempo = df[["mes_ano"]].drop_duplicates().copy()
dim_tempo["id_tempo"] = dim_tempo["mes_ano"].dt.strftime("%Y-%m-%d")

dim_tempo["ano"] = dim_tempo["mes_ano"].dt.year
dim_tempo["mes"] = dim_tempo["mes_ano"].dt.month
dim_tempo["mes_nome"] = dim_tempo["mes_ano"].dt.strftime("%b")
dim_tempo["trimestre"] = dim_tempo["mes_ano"].dt.quarter


# PRAÇA
dim_praca = df[["praca"]].drop_duplicates().copy()
dim_praca["id_praca"] = dim_praca["praca"]


# CONCESSIONÁRIA
dim_concessionaria = df[["concessionaria"]].drop_duplicates().copy()
dim_concessionaria["id_concessionaria"] = dim_concessionaria["concessionaria"]


# VEÍCULO
dim_veiculo = df[["tipo_de_veiculo", "categoria_eixo"]].drop_duplicates().copy()

dim_veiculo["id_veiculo"] = (
    dim_veiculo["tipo_de_veiculo"] + "_" +
    dim_veiculo["categoria_eixo"].astype(int).astype(str)
)

# classificação vetorizada
dim_veiculo["tipo_peso"] = dim_veiculo["tipo_de_veiculo"].eq("COMERCIAL").map({
    True: "PESADO",
    False: "LEVE"
})


# COBRANÇA
dim_cobranca = df[["tipo_cobranca"]].drop_duplicates().copy()
dim_cobranca["id_cobranca"] = dim_cobranca["tipo_cobranca"]


# SENTIDO
dim_sentido = df[["sentido"]].drop_duplicates().copy()
dim_sentido["id_sentido"] = dim_sentido["sentido"]


# =========================
# FATO
# =========================

fato = df.copy()

fato["id_tempo"] = fato["mes_ano"].dt.strftime("%Y-%m-%d")
fato["id_praca"] = fato["praca"]
fato["id_concessionaria"] = fato["concessionaria"]
fato["id_cobranca"] = fato["tipo_cobranca"]
fato["id_sentido"] = fato["sentido"]

fato["id_veiculo"] = (
    fato["tipo_de_veiculo"] + "_" +
    fato["categoria_eixo"].astype(int).astype(str)
)

# participação mensal por praça
fato["participacao_praca"] = (
    fato["volume_total"] /
    fato.groupby("mes_ano")["volume_total"].transform("sum")
)

# seleção final (1FN garantida)
fato = fato[[
    "id_tempo",
    "id_praca",
    "id_concessionaria",
    "id_veiculo",
    "id_cobranca",
    "id_sentido",
    "volume_total",
    "vmd",
    "fator_desgaste",
    "participacao_praca"
]]


# =========================
# OUTPUT
# =========================

os.makedirs("gold", exist_ok=True)

fato.to_parquet("gold/fato_trafego.parquet", index=False)

dim_tempo.to_parquet("gold/dim_tempo.parquet", index=False)
dim_praca.to_parquet("gold/dim_praca.parquet", index=False)
dim_concessionaria.to_parquet("gold/dim_concessionaria.parquet", index=False)
dim_veiculo.to_parquet("gold/dim_veiculo.parquet", index=False)
dim_cobranca.to_parquet("gold/dim_cobranca.parquet", index=False)
dim_sentido.to_parquet("gold/dim_sentido.parquet", index=False)

print("GOLD concluída")