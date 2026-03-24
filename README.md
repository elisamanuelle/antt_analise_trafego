# Análise de Tráfego Rodoviário - ANTT (CRO)

## Sumário
* [1. Case de Negócio](#1-case-de-negócio)
    * [Contexto](#contexto)
    * [Problema](#problema)
    * [Hipótese](#hipótese)
    * [Abordagem Analítica](#abordagem-analítica)
    * [Construção dos Dados](#construção-dos-dados)
    * [Insights](#insights)
    * [Recomendações](#recomendações)
    * [Impacto Potencial](#impacto-potencial)
* [2. Desenvolvimento Técnico](#2-desenvolvimento-técnico)
    * [Camada Bronze](#camada-bronze)
    * [Camada Silver](#camada-silver)
    * [Camada Gold](#camada-gold)
    * [Indicadores](#indicadores)
    * [Visualizações](#visualizações)
    * [Limitações](#limitações)


## 1. Case de Negócio

### Contexto
O tráfego rodoviário tem como um dos seus principais parâmetros o ```volume absoluto de veículos```. No entanto, a engenharia de tráfego raramente utiliza apenas esse indicador. Ele é analisado em conjunto com outras métricas como ```composição do tráfego``` por exemplo. Além disso, é possível analisar que nem todos os veículos impactam a infraestrutura da via da mesma forma.

Este projeto utiliza dados abertos da **Agência Nacional de Transportes Terrestres (ANTT)** para analisar a concessionária Rota do Oeste (CRO), com o objetivo de transformar dados operacionais em indicadores de pressão sobre a rodovia.

*[Retornar ao sumário](#sumário)*

---
### Problema
Se concentrar em indicadores como ```volume absoluto de veículos```, sem combinar com outros que avaliam outros aspectos do tráfego e via, gera resposta apenas para a pergunta simples *"quantos veículos passam?"*, não respondendo questionamentos importantes como:
* Onde o sistema está mais pressionado?
* Quais pontos geram maior desgate estrutural?
* Onde priorizar investimento ou manutenção?

O que acaba levando a tomada de decisões reativas e potencialmente ineficientes.

*[Retornar ao sumário](#sumário)*

---
### Hipótese
É possível que praças com menor ``volume médio diário de veículos`` podem apresentar uma maior criticidade quando há uma maior concentração de veículos pesados transitando. Isto é, a rodovia é impactada pela composição do tráfego, além do próprio ``volume absoluto de veículos``. 

*[Retornar ao sumário](#sumário)*

---
### Abordagem analítica
A análise foi estruturada em três dimensões principais para avaliação da criticidade operacional:
* **Volume de tráfego**: volume absoluto de veículos
* **Desgate**: impacto dos veículos na estrutura, considerando a <span style="color:red"> "Lei da Quarta Potência" </span>
* **Concentração**: participação da praça no fluxo total

A combinação dessas dimensões resultou na criação de um KPI personalizado para gestão de praças de pedágio: *Índice de Gargalo Operacional*. 

O cálculo sugere que se uma praça de pedágio tem muito tráfego, com veículos que causam muito desgate, e essa praça concentra a maior parte do fluxo de uma rodovia, o índice será alto, indicando um **gargalo crítico** que necessita de intervenção operacional.

A fórmula criada foi uma maneira encontrada para quantificar o risco de congestionamento e a necessidade de manutenção em um ponto específico.

*[Retornar ao sumário](#sumário)*

---
### Construção dos dados

Os dados utilizados foram organizados em pipeline em camadas:

* Bronze: camada de ingestão automatizada de dados via API da ANTT
* Silver: camada de tratamento, padronização e resolução de inconsistências
* Gold: camada de modelagem dimensional adotando o modelo estrela (Star Schema)

Nesse processo foram tratados problemas estruturais relevantes como:
* Mistura de granularidade de dados diário com mensal
* Problemas com inconsistência de datas
* Variações categóricas
* Linhas com duplicidades

Resultado após tratamento:
* Granularidade consistente (mantendo apenas dados mensais)
* Dados sem duplicidade
* Base confiável para análise

*[Retornar ao sumário](#sumário)*

---
### Insights

Observando os resultados da concessionária Rota do Oeste (CRO) em 2025, o principal padrão identificado foi consistente em toda a análise:

> Os veículos comerciais representam 54,60% do volume absoluto de veículos transitados na via da concessionária CRO no período de 2025, sendo os responsáveis por 99,67% dos desgates da via.

![alt text](image-2.png)

[Acessar Dashboard no Power BI](https://app.powerbi.com/view?r=eyJrIjoiZTNlY2M2NjItZWRhNC00MzMzLWIzYmEtNDU4N2NmYmQ4MGNmIiwidCI6ImJhMjVhMjgxLTY5MTAtNDdhYS1hZTFiLTA2NWIzOGY3ZDVhMSJ9)

Além disso, foi identificado que:
* Praças como a P2 e a P4 concentram simultaneamente alto volume de tráfego + alto impacto dos veículos (desgate) + significativa participação da praça no fluxo total, resultando em probabilidade de existência de gargalos reais
* Outras praças, como a P6 e P3, apresentam menor volume em relação as praças anteriores, mas relevante criticidade, sugerindo existência de gargalos ocultos
* E as demais praças apresentam oportunidade de atuação preventiva

*[Retornar ao sumário](#sumário)*

---
### Recomendações

Os resultados obtidos demonstram a necessidade de tomada de algumas decisões como:
* Priorizar a manutenção da via com base no acompanhamento do índice de gargalo em conjunto com o volume absoluto de veículos
* Monitorar continuamente a proporção de veículos pesados
* Expandir o uso de cobrança automática em praças críticas, para melhorar agilidade
* Antecipar intervenções em praças com criticidade emergente (ações preventivas)

*[Retornar ao sumário](#sumário)*

---
### Impacto Potencial

A adoção dessa abordagem permite realizar uma gestão baseada em pressão operacional, conseguindo com essa análise:
* Melhorar a alocação de investimento
* Reduzir o desgate estrutural não previsto (com ações preventivas)
* Aumentar a eficiência operacional

*[Retornar ao sumário](#sumário)*

## 2. Desenvolvimento Técnico

### Camada Bronze
A camada Bronze é a responsável pela ingestão automatizada e padronização estrutural dos dados brutos da ANTT, preservando a fidelidade da fonte e garantindo reprodutibilidade do pipeline.

O dataset **“Volume de Tráfego por Praça de Pedágio”** é disponibilizado em múltiplos arquivos CSV, variando por ano e granularidade (diária e mensal). Para garantir consistência analítica, a ingestão foi estruturada com critérios explícitos de seleção.

---

#### Critérios de ingestão

Foram considerados apenas arquivos:

- Com granularidade **mensal**
- Com período a partir de **2016** (para manter um histórico dos últimos 10 anos)
- Priorizando versões **mensal consolidado** quando disponíveis

Essa decisão evita mistura de granularidades e elimina duplicidade lógica ainda na origem.

---

#### Pipeline de ingestão

A ingestão foi implementada em Python utilizando `requests` e `pandas`, seguindo o fluxo:

1. Consulta à API da ANTT para listagem dos recursos disponíveis  
2. Normalização dos nomes dos arquivos (remoção de acentos e padronização textual)  
3. Aplicação dos critérios de seleção  
4. Registro dos metadados em log de ingestão (rastreabilidade)  
5. Download automatizado dos arquivos com controle de falhas  
6. Armazenamento dos dados brutos  
7. Consolidação dos arquivos em dataset único em formato parquet (garante leitura rápida, compressão alta e análise de dados em escala)

---

#### Transformações aplicadas

Nesta camada, são realizadas apenas transformações estruturais mínimas:

- Padronização do número de colunas  
- Remoção de cabeçalhos duplicados  
- Inclusão da coluna `arquivo_origem` para rastreabilidade  
- Remoção de duplicidades exatas entre arquivos  

Nenhuma regra de negócio ou agregação é aplicada nesta etapa.

---

#### Saída da camada Bronze

A camada Bronze entrega um dataset:

- Consolidado em nível bruto  
- Com granularidade consistente (dados mensal)  
- Com rastreabilidade completa da origem  
- Pronto para tratamento na camada Silver  

---

#### Consideração

O principal papel da Bronze não foi de limpar dados, mas garantir que:

> todos os dados relevantes foram corretamente capturados, preservados e organizados de forma reprodutível.

*[Retornar ao sumário](#sumário)*

---

Aqui você já está muito perto de um nível sênior — o ajuste agora é **organização mental + precisão de linguagem**.

Eu vou te devolver no mesmo padrão da Bronze: mais enxuto, mais estruturado e com **cara de decisão consciente (não só execução)**.

---

### Camada Silver

A camada Silver é responsável por transformar os dados da Bronze em uma base consistente, padronizada e analiticamente confiável.

Nesta etapa, o foco deixa de ser ingestão e passa a ser qualidade e integridade dos dados, garantindo que cada registro represente uma observação única do sistema.

Objetivos da camada:

- Eliminar inconsistências estruturais e semânticas  
- Padronizar formatos (texto, números e datas)  
- Resolver conflitos de duplicidade lógica  
- Garantir unicidade no nível de análise  

---

#### Padronização de dados

**Texto (categorias):**

As colunas categóricas foram normalizadas para evitar duplicidade lógica:

- Remoção de espaços em branco  
- Conversão para letras maiúsculas  
- Unificação de valores equivalentes  

Exemplo:

```text
VEÍCULO PEQUENO → PASSEIO
VEICULO PEQUENO → PASSEIO
```

---

**Numérico:**

* `volume_total` convertido de texto (formato brasileiro) para numérico
* `categoria_eixo` transformada para tipo numérico com extração de valores

Isso garante consistência em agregações e métricas derivadas.

---

**Temporal:**

A coluna `mes_ano` apresentava múltiplos formatos.

Tratamento aplicado:

* conversão para `datetime`
* padronização para o primeiro dia do mês (`YYYY-MM-01`)

Essa abordagem assegura consistência em análises temporais e integração com dimensões de tempo.

---

#### Resolução de conflitos de dados

Foram identificados casos em que múltiplos registros representavam a mesma observação, mas com valores diferentes de volume.

**Chave analítica considerada:**

* concessionária
* mes_ano
* praça
* tipo de veículo
* categoria de eixo
* sentido
* tipo de cobrança

**Estratégia adotada:**

* Identificação de conflitos por chave
* Consolidação utilizando o valor máximo de `volume_total`

Essa decisão evita subestimação do tráfego e mantém consistência sem inflar os dados.

---

#### Consolidação e validação

Após o tratamento:

* Dados foram agregados no nível da chave analítica
* As duplicidades foram removidas
* E a unicidade foi garantida

Cada linha do dataset passa a representar uma observação única e consistente.

---

#### Remoção de registros inválidos

Foram excluídos registros que não atendiam critérios mínimos como:

* Datas não convertidas
* Volumes nulos ou inválidos

---

#### Saída da camada Silver

A camada Silver entrega um dataset:

* Consistente em granularidade (mensal)
* Padronizado em formatos e categorias
* Livre de duplicidades estruturais
* Pronto para modelagem analítica

Arquivo gerado na camada Silver:

[silver/antt_trafego_silver.parquet](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/silver)


---

#### Consideração

O valor da camada Silver não está apenas na limpeza, mas na garantia de consistência analítica.

Ao padronizar formatos e resolver conflitos de dados, esta etapa elimina ambiguidades que poderiam distorcer indicadores, assegurando que a camada Gold reflita o comportamento real do sistema.

*[Retornar ao sumário](#sumário)*

---

### Camada Gold

A camada Gold é a responsável por transformar os dados tratados na Silver em um modelo analítico estruturado, orientado à geração de indicadores de negócio e consumo em ferramentas de BI.

Nesta etapa, o foco deixa de ser tratamento e passa a ser modelagem e significado analítico, garantindo que os dados possam ser explorados de forma consistente, performática e alinhada ao problema de negócio.

Objetivo da camada:

- Estruturar os dados para análise multidimensional  
- Garantir consistência de granularidade  
- Viabilizar construção de indicadores operacionais  
- Suportar consumo direto em BI (Power BI)  

---

#### Modelagem dimensional

Foi adotado o modelo estrela, separando:

- **Fatos**: métricas  
- **Dimensões**: contexto analítico  

Essa abordagem reduz redundância, melhora performance e simplifica a construção de medidas.

---

#### Fatos

``fato_trafego``

Tabela central do modelo, representando o volume de veículos.

**Nível de detalhamento:**

- mês  
- praça  
- concessionária  
- tipo de veículo  
- categoria de eixo  

Esse nível garante alinhamento com a granularidade mensal da Silver e evita dupla contagem.

---

``fato_operacional``

Tabela complementar com foco em comportamento operacional.

**Nível de detalhamento:**

- mês  
- praça  
- tipo de cobrança  
- sentido  

Permite análises específicas de operação, sem misturar granularidades com a fato de tráfego.

---

#### Métricas derivadas

As métricas foram construídas diretamente no modelo para traduzir o comportamento do sistema.

**Volume Total**

Base de todas as análises:

```text
Volume Total = soma de veículos no período
````

---

**VMD (Volume Médio Diário)**

```text
VMD = volume_total / dias_mes
```

Normaliza o volume para uma escala diária, permitindo comparações entre períodos.

---

**Fator de Desgaste**

```text
fator_desgaste = eixo^4
```

Baseado na Lei da Quarta Potência, esse indicador estima o impacto estrutural dos veículos.

Como não há peso por eixo no dataset, a categoria de eixo foi utilizada como proxy de carga.
Valores nulos ou zero foram tratados como 1 (impacto mínimo).

---

**Participação da Praça**

```text
participacao = volume_praca / volume_total_mes
```

Permite analisar concentração de fluxo e relevância operacional das praças.

---

#### Dimensões

As dimensões fornecem contexto analítico ao modelo.

* **dim_tempo**: ano, mês, trimestre, ordenação temporal
* **dim_praca**: identificação das praças
* **dim_concessionaria**: segmentação por operador
* **dim_veiculo**: tipo + categoria de eixo

Classificação derivada:

```text
COMERCIAL → PESADO  
outros → LEVE
```

* **dim_cobranca**: tipo de pagamento
* **dim_sentido**: direção do fluxo

---

#### Chaves e integridade

As tabelas são conectadas pelas chaves:

* `id_tempo`
* `id_praca`
* `id_concessionaria`
* `id_veiculo`
* `id_cobranca`
* `id_sentido`

Essa estrutura garante:

* Integridade referencial
* Ausência de ambiguidade
* Compatibilidade com modelo estrela

---

#### Estrutura de saída

Os dados são disponibilizados em formato parquet:

```
gold/
├─ fato_trafego.parquet
├─ fato_operacional.parquet
├─ dim_tempo.parquet
├─ dim_praca.parquet
├─ dim_concessionaria.parquet
├─ dim_veiculo.parquet
├─ dim_cobranca.parquet
├─ dim_sentido.parquet
```

---

#### Consideração

A camada Gold define como o problema será analisado.

Ao estruturar o modelo em torno de volume, desgaste e concentração, os dados deixam de ser apenas descritivos e passam a representar a dinâmica operacional da rodovia.

Isso permite:

* Identificar intensidade de uso da via
* Medir impacto na infraestrutura
* Priorizar praças de maior pressão

Sem necessidade de transformações adicionais no consumo.


*[Retornar ao sumário](#sumário)*

---

### Indicadores

Os indicadores foram estruturados para garantir consistência de contexto, comparabilidade e interpretação operacional.

A lógica analítica segue três pilares:

- **Volume:** intensidade de uso  
- **Desgaste:** impacto estrutural  
- **Criticidade:** priorização operacional  

---

#### 1. Volume (base analítica)

O volume é a base de todas as análises.

```DAX
Volume Total = SUM(fato_trafego[volume_total])
```

A partir dele, derivam-se métricas de distribuição:

* **% Volume**: participação por tipo de veículo
* **% Fluxo Praça**: participação da praça no fluxo total
* **% Cobrança**: distribuição por tipo de pagamento

Essas medidas utilizam `ALLSELECTED`, garantindo que os percentuais sejam calculados dentro do contexto filtrado na página.

---

#### Volume Médio Diário (VMD)

```DAX
VMD_ =
DIVIDE(
    [Volume Total],
    SUMX(
        VALUES(dim_tempo[id_tempo]),
        CALCULATE(MAX(fato_trafego[dias_mes]))
    )
)
```

O VMD normaliza o volume mensal para escala diária, permitindo comparações entre períodos.

O cálculo considera corretamente o contexto temporal, evitando distorções em agregações multi-mês.

---

#### Segmentação por veículo

Indicadores específicos foram criados para analisar o papel dos veículos pesados:

* **Volume Pesado**
* **% Pesados**
* **% Volume Comercial**

Essas métricas permitem entender a composição do tráfego.

---

#### 2. Desgaste (impacto estrutural)

O desgaste captura o impacto real sobre a infraestrutura.

```DAX
Desgaste Total =
SUMX(
    fato_trafego,
    fato_trafego[volume_total] * fato_trafego[fator_desgaste]
)
```

Esse cálculo incorpora o fator de desgaste (Lei da Quarta Potência), refletindo o impacto não linear dos veículos pesados.

A partir dele, derivam-se:

* **Desgaste Pesado**
* **% Desgaste**
* **% Desgaste Praça**

---

#### Relação Volume vs Desgaste

Um dos principais insights do modelo é a comparação entre:

```text
participação no volume vs participação no desgaste
```

Essa relação evidencia distorções estruturais, como:

```text
veículos comerciais representam médio volume, mas maior impacto
```

Essa leitura é sintetizada na medida:

```DAX
Insight Comercial
```

---

#### Eixo médio ponderado

```DAX
Eixo Médio Ponderado =
DIVIDE(
    SUMX(fato_trafego, fato_trafego[categoria_eixo] * fato_trafego[volume_total]),
    [Volume Total]
)
```

Representa a carga média da frota, funcionando como proxy do nível de impacto estrutural.

---

#### 3. Criticidade (priorização operacional)

A criticidade consolida volume, desgaste e concentração em um único indicador.

---

**Índice de Gargalo**

```DAX
Indice Gargalo =
VAR PesoDesgaste =
    DIVIDE([Desgaste Total], [Volume Total])

VAR Concentracao =
    [% Fluxo Praça]

RETURN
    [Volume Total] * PesoDesgaste * Concentracao
```

Esse índice combina:

* volume: intensidade
* desgaste médio: impacto
* concentração: relevância

Na prática, identifica:

```text
onde há mais fluxo + mais impacto + mais concentração
```

---

**Normalização**

```DAX
Indice Gargalo Normalizado =
DIVIDE(
    [Indice Gargalo],
    CALCULATE(
        MAXX(
            ALLSELECTED(dim_praca),
            [Indice Gargalo]
        )
    )
)
```

A normalização permite comparar praças dentro do contexto filtrado (escala relativa).

---

**Classificação de criticidade**

```DAX
Categoria Gargalo
```

As praças são classificadas em:

* Alta Pressão
* Atenção
* Baixa Pressão

---

**Ordenação**

```DAX
Ordem Gargalo
```

Permite priorização visual das praças por nível de criticidade.

---

#### Consideração

Os indicadores foram desenhados para responder não apenas:

* Quanto passa?

Mas principalmente:
* Onde o sistema está mais pressionado?


Ao integrar volume, desgaste e concentração, o modelo transforma dados de tráfego em um instrumento direto de priorização operacional.

*[Retornar ao sumário](#sumário)* 

---

### Visualizações

O dashboard foi estruturado para traduzir os indicadores em uma leitura progressiva do sistema, guiando o usuário por três perguntas:

```text
Quanto passa? → Quem impacta? → Onde está o problema?
````

O objetivo não é apenas exibir dados, mas reduzir a carga cognitiva e permitir interpretação rápida, mesmo sem conhecimento prévio do modelo.

---

#### 1. Visão geral (KPIs)

O topo do painel apresenta os principais indicadores sintéticos:

* **Volume Médio Diário (VMD)**
* **Volume Total**
* **% de Veículos Pesados**
* **% de Desgaste gerado por Pesados**

Essa combinação permite leitura imediata do sistema:

* O VMD traduz o ritmo operacional diário
* O volume total indica escala de tráfego
* A comparação entre % pesados e % desgaste evidencia o impacto desproporcional dos veículos comerciais

---

#### Insight automático

Um destaque textual sintetiza o principal insight do período:

```text id="3bxtqf"
Veículos comerciais representam X% do volume, mas Y% do desgaste da via
```

Esse elemento elimina interpretação manual e direciona o foco do usuário para o principal desequilíbrio do sistema.

---

#### 2. Composição do tráfego (quem impacta)

**Volume vs Desgaste por tipo de veículo**

Gráfico de colunas comparando:

* **% Volume**
* **% Desgaste**

por tipo de veículo.

Essa visualização evidencia que:

```text id="qv6c6g"
veículos comerciais concentram a maior parte do impacto estrutural, mesmo sem representar todo o volume
```

---

**Distribuição por tipo de cobrança**

Gráfico de rosca mostrando a participação de:

* Cobrança automática
* Manual
* OCR/placa

Permite avaliar o nível de automação e possíveis pontos de fricção operacional.

---

#### 3. Dinâmica temporal (como o sistema evolui)

**Evolução do VMD**

Gráfico de linha com o VMD ao longo do tempo.

Permite identificar:

* Tendências de crescimento ou retração
* Padrões sazonais
* Variações operacionais

---

#### 4. Análise espacial (onde está o problema)

**Volume Total por praça**

Gráfico de barras comparando o volume entre praças.

Permite identificar concentração de tráfego no sistema.

---

**Tabela de criticidade operacional**

Tabela consolidando:

* **% de criticidade**
* **categoria de gargalo** (Alta Pressão, Atenção, Baixa Pressão)

Funciona como resumo operacional, permitindo identificar rapidamente:

```text id="g6a2h6"
Quais praças concentram maior pressão no sistema
```

---

**Interpretação do gargalo**

Bloco explicativo para suporte à leitura:

```text id="7fchx1"
Criticidade operacional combina:
• volume de tráfego  
• impacto dos veículos (desgaste)  
• participação da praça no fluxo total
```

Esse elemento garante compreensão do indicador sem necessidade de conhecimento técnico.

---

#### Consideração

As visualizações foram desenhadas para transformar dados em diagnóstico operacional.

O painel permite que qualquer usuário entenda:

* O nível de tráfego
* O impacto estrutural
* E os pontos críticos da operação

Sem necessidade de tratamento adicional ou conhecimento prévio do modelo.



*[Retornar ao sumário](#sumário)* 

---

### Limitações

O fator de desgaste foi estimado com base na categoria de eixo, como uma aproximação da carga dos veículos. Como o dataset não fornece peso real por eixo, o indicador representa uma proxy e não uma medição direta.

Além disso, em casos de inconsistência de dados, foi adotada uma abordagem conservadora (valor máximo) para evitar subestimação do volume, o que pode introduzir viés em cenários específicos.

**Essas limitações devem ser consideradas na interpretação dos resultados.**

*[Retornar ao sumário](#sumário)* 
