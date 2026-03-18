import pandas as pd
import os

print("Iniciando camada GOLD...")

# LEITURA

df = pd.read_parquet("silver/antt_trafego_silver.parquet")
df = df.drop(columns=["_index_level_0_"], errors="ignore")

print("Linhas recebidas:", len(df))

# TRATAMENTO BASE

df["categoria_eixo"] = pd.to_numeric(df["categoria_eixo"], errors="coerce").fillna(0)

cols_fill = [
    "concessionaria",
    "tipo_de_veiculo",
    "praca",
    "tipo_cobranca",
    "sentido"
]

for col in cols_fill:
    df[col] = df[col].fillna("NAO_INF")

# FATO 1 — TRÁFEGO

chave_trafego = [
    "mes_ano",
    "praca",
    "concessionaria",
    "tipo_de_veiculo",
    "categoria_eixo"
]

fato_trafego = (
    df.groupby(chave_trafego, as_index=False)
    .agg(volume_total=("volume_total", "sum"))
)

# métricas
fato_trafego["dias_mes"] = fato_trafego["mes_ano"].dt.days_in_month

fato_trafego["vmd"] = (
    fato_trafego["volume_total"] /
    fato_trafego["dias_mes"].replace(0, 1)
)

fato_trafego["fator_desgaste"] = (
    fato_trafego["categoria_eixo"].replace(0, 1) ** 4
)

# FATO 2 — OPERACIONAL

chave_operacional = [
    "mes_ano",
    "praca",
    "tipo_cobranca",
    "sentido"
]

fato_operacional = (
    df.groupby(chave_operacional, as_index=False)
    .agg(volume_total=("volume_total", "sum"))
)

# DIMENSÕES

# TEMPO
dim_tempo = df[["mes_ano"]].drop_duplicates().copy()

dim_tempo["id_tempo"] = dim_tempo["mes_ano"].dt.strftime("%Y-%m-%d")
dim_tempo["ano"] = dim_tempo["mes_ano"].dt.year
dim_tempo["mes"] = dim_tempo["mes_ano"].dt.month

dim_tempo["mes_nome"] = dim_tempo["mes_ano"].dt.month.map({
    1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
    7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"
})

dim_tempo["trimestre"] = dim_tempo["mes_ano"].dt.quarter

dim_tempo["mes_ano_ordem"] = dim_tempo["ano"] * 100 + dim_tempo["mes"]

# PRAÇA
dim_praca = df[["praca"]].drop_duplicates().copy()
dim_praca["id_praca"] = dim_praca["praca"]

# CONCESSIONÁRIA
dim_concessionaria = df[["concessionaria"]].drop_duplicates().copy()
dim_concessionaria["id_concessionaria"] = dim_concessionaria["concessionaria"]

# VEÍCULO
dim_veiculo = df[["tipo_de_veiculo", "categoria_eixo"]].drop_duplicates().copy()

dim_veiculo["id_veiculo"] = (
    dim_veiculo["tipo_de_veiculo"].str.strip() + "_" +
    dim_veiculo["categoria_eixo"].astype(int).astype(str)
)

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

# KEYS — FATO TRÁFEGO

fato_trafego["id_tempo"] = fato_trafego["mes_ano"].dt.strftime("%Y-%m-%d")
fato_trafego["id_praca"] = fato_trafego["praca"]
fato_trafego["id_concessionaria"] = fato_trafego["concessionaria"]

fato_trafego["id_veiculo"] = (
    fato_trafego["tipo_de_veiculo"] + "_" +
    fato_trafego["categoria_eixo"].astype(int).astype(str)
)

# participação dentro da praça no mês
fato_trafego["participacao_praca"] = (
    fato_trafego["volume_total"] /
    fato_trafego.groupby(["mes_ano", "praca"])["volume_total"].transform("sum")
)

fato_trafego = fato_trafego[[
    "id_tempo",
    "id_praca",
    "id_concessionaria",
    "id_veiculo",
    "volume_total",
    "dias_mes",
    "vmd",
    "categoria_eixo", 
    "fator_desgaste",
    "participacao_praca"
]]

# KEYS — FATO OPERACIONAL

fato_operacional["id_tempo"] = fato_operacional["mes_ano"].dt.strftime("%Y-%m-%d")
fato_operacional["id_praca"] = fato_operacional["praca"]
fato_operacional["id_cobranca"] = fato_operacional["tipo_cobranca"]
fato_operacional["id_sentido"] = fato_operacional["sentido"]

fato_operacional = fato_operacional[[
    "id_tempo",
    "id_praca",
    "id_cobranca",
    "id_sentido",
    "volume_total"
]]

# OUTPUT

os.makedirs("gold", exist_ok=True)

fato_trafego.to_parquet("gold/fato_trafego.parquet", index=False)
fato_operacional.to_parquet("gold/fato_operacional.parquet", index=False)

dim_tempo.to_parquet("gold/dim_tempo.parquet", index=False)
dim_praca.to_parquet("gold/dim_praca.parquet", index=False)
dim_concessionaria.to_parquet("gold/dim_concessionaria.parquet", index=False)
dim_veiculo.to_parquet("gold/dim_veiculo.parquet", index=False)
dim_cobranca.to_parquet("gold/dim_cobranca.parquet", index=False)
dim_sentido.to_parquet("gold/dim_sentido.parquet", index=False)

print("Concluído")
