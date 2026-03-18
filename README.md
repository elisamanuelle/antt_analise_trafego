# Volume de tráfego por Praça
``Concessionária Rota do Oeste (CRO)``

## Contexto

O objetivo do projeto é analisar o tráfego da concessionária Rota do Oeste (CRO) a partir dos dados abertos disponibilizados pela ANTT, com foco em transformar dados brutos em indicadores que apoiem leitura operacional da rodovia.

Embora o recorte analítico esteja centrado na CRO, a ingestão foi estruturada para considerar todo o dataset nacional. Essa decisão garante integridade histórica, padronização das métricas e comparabilidade entre concessionárias, além de permitir expansão futura do modelo sem necessidade de reprocessamento estrutural.

O pipeline foi construído em camadas (Bronze, Silver e Gold), com tratamento de inconsistências, deduplicação e consolidação de granularidade mensal, assegurando que os indicadores derivados reflitam o comportamento real do tráfego, e não artefatos de dados.

A análise vai além da descrição volumétrica e busca interpretar o sistema rodoviário sob uma ótica operacional. Para isso, foram definidos indicadores que capturam não apenas fluxo, mas também impacto e concentração, como o Volume Médio Diário (VMD) e o índice de criticidade (gargalo), que combina volume, desgaste e participação no fluxo.

Nesse contexto, o projeto busca responder, de forma estruturada:

- Como evolui o volume médio diário de veículos ao longo do tempo?
- Qual o papel dos veículos comerciais no desgaste da rodovia?
- Existem padrões de sazonalidade no tráfego?
- Como o fluxo se distribui entre diferentes formas de cobrança e sentidos?
- Quais praças concentram maior pressão operacional e potencial risco estrutural?

Com isso, o tráfego deixa de ser apenas uma contagem de veículos e passa a ser interpretado como um proxy de pressão sobre a infraestrutura, permitindo identificar pontos críticos, apoiar decisões operacionais e orientar priorização de investimentos.

## Ingestão

Antes da etapa analítica, foi necessário estruturar a ingestão dos dados disponibilizados pela ANTT de forma automatizada e controlada.

O dataset “Volume de Tráfego por Praça de Pedágio” é publicado em múltiplos arquivos CSV, variando por ano e por tipo de consolidação (diária e mensal). Como o objetivo do projeto é analisar o comportamento do tráfego da Rota do Oeste (CRO) com consistência histórica, a ingestão foi desenhada para percorrer todo o catálogo disponível na API, mas com critérios claros de seleção.

Foram considerados apenas arquivos com granularidade **mensal** e com período a partir de **2016**, garantindo comparabilidade temporal e evitando mistura de granularidades (um dos principais problemas identificados na fase inicial do projeto). Nos anos mais recentes, onde coexistem versões “mensal” e “mensal consolidado”, foi priorizada a versão consolidada, assegurando consistência dos dados.

Essa abordagem traz três benefícios principais:

- Preserva a integridade histórica relevante para análise
- Evita distorções causadas por dados diários e duplicidades de publicação
- Mantém o processo totalmente reprodutível

Para isso, foi desenvolvido um [script em Python](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/pipeline_bronze_antt.py) responsável por consumir a API da ANTT, filtrar os recursos válidos e realizar o download automatizado dos arquivos.

### Processo de coleta automatizada

O pipeline de ingestão foi implementado utilizando as bibliotecas `requests` e `pandas`, seguindo um fluxo estruturado:

1. Consulta à API do portal de dados da ANTT para listar todos os recursos do dataset.
2. Normalização dos nomes dos arquivos para viabilizar filtros consistentes (remoção de acentos e padronização textual).
3. Aplicação de regras de seleção:
   - inclusão apenas de arquivos CSV
   - exclusão de arquivos com granularidade diária
   - seleção de arquivos a partir de 2016
   - priorização de versões “mensal consolidado” quando disponíveis
4. Registro dos metadados dos recursos em um [log de ingestão](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/log), garantindo rastreabilidade da coleta.
5. Download automático dos arquivos selecionados, com controle de tentativas para evitar falhas de rede.
6. Armazenamento local dos arquivos brutos, preservando a fonte original.
7. Leitura e consolidação dos arquivos em um único [dataset em formato parquet](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/bronze), estruturado para as próximas etapas do pipeline.

### Considerações sobre a camada Bronze

Nesta etapa, foram aplicadas apenas transformações estruturais mínimas, com o objetivo de padronizar os dados sem alterar seu conteúdo analítico:

- Padronização do número de colunas
- Remoção de linhas de cabeçalho replicadas nos arquivos
- Inclusão de metadados de origem (arquivo) para rastreabilidade
- Remoção de duplicidades exatas entre arquivos

Nenhuma regra de negócio ou agregação foi aplicada nesta fase. A camada Bronze mantém os dados o mais próximo possível da origem, garantindo transparência e possibilitando reprocessamentos futuros sem perda de informação.

## Exploração

Após a ingestão e aplicação dos critérios de seleção (dados **mensais**, a partir de **2016** e priorizando versões consolidadas), o dataset resultante apresenta uma base consistente para análise, eliminando o principal risco identificado na etapa inicial: a mistura de granularidades.

O conjunto consolidado contém **804.335 registros** e mantém a seguinte estrutura:

| Coluna          | Descrição                                              |
| --------------- | ------------------------------------------------------ |
| concessionaria  | Identifica a concessionária responsável pela rodovia   |
| mes_ano         | Período de referência (padronizado para início do mês) |
| sentido         | Direção do fluxo                                       |
| praca           | Praça de pedágio onde o tráfego foi registrado         |
| tipo_cobranca   | Modalidade de pagamento                                |
| categoria_eixo  | Número de eixos do veículo (normalizado)               |
| tipo_de_veiculo | Classificação do veículo                               |
| volume_total    | Quantidade de veículos                                 |
| arquivo_origem  | Arquivo de origem do registro                          |

### Metadado de origem

A coluna `arquivo_origem` foi mantida como elemento de rastreabilidade ao longo do pipeline.

Ela foi essencial para identificar e corrigir problemas estruturais relevantes, como:

- coexistência de arquivos diários e mensais
- múltiplas versões para o mesmo período (mensal vs consolidado)
- variações no formato de datas entre anos

Esse controle permitiu aplicar regras de seleção na ingestão e evitar duplicidades estruturais ainda na camada Bronze.

### Estrutura analítica do dataset

Com os dados já padronizados, a base permite analisar o sistema sob diferentes dimensões operacionais.

#### 1. Tráfego (demanda)

Representa o volume e sua evolução temporal:

- `volume_total`
- `mes_ano`
- `praca`

Permite derivar indicadores como Volume Médio Diário (VMD) e identificar tendências de crescimento ou retração.

#### 2. Logística (fluxo direcional)

Captura padrões de deslocamento:

- `sentido`
- `praca`

Permite observar assimetrias de fluxo (ex.: ida vs volta), relevantes para entender dinâmica logística da rodovia.

#### 3. Impacto na infraestrutura

Relaciona características do veículo ao desgaste da via:

- `categoria_eixo`
- `tipo_de_veiculo`

A normalização da categoria de eixo possibilita aplicar modelos de desgaste, evidenciando o impacto desproporcional de veículos pesados.

#### 4. Operação (praça de pedágio)

Permite avaliar comportamento operacional:

- `tipo_cobranca`

Viabiliza análises sobre distribuição entre pagamento manual e automático, além de inferências sobre eficiência e possíveis pontos de fricção.

### Qualidade dos dados

A qualidade foi avaliada por meio de diagnósticos automatizados, com geração de evidências na pasta [evidencias](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias).

### Principais problemas identificados (e corrigidos)

#### Granularidade inconsistente

O principal problema do dataset original era a mistura de:

- dados diários
- dados mensais
- dados mensais consolidados

Isso gerava duplicidade lógica e inflava os volumes.

**Tratamento aplicado:**

- ingestão restrita a dados mensais
- priorização de versões consolidadas
- eliminação da necessidade de deduplicação posterior

#### Inconsistência de datas

Foram identificados múltiplos formatos:

- `DD/MM/AAAA`
- `MM/AAAA`
- formatos textuais (ex.: `jan/2026`)

**Tratamento aplicado:**

- padronização para datetime
- conversão para início do mês (`YYYY-MM-01`)

#### Inconsistência categórica

A coluna `tipo_de_veiculo` apresentava variações semânticas:

```
PASSEIO
Passeio
VEÍCULO PEQUENO
COMERCIAL
Comercial
```

**Tratamento aplicado:**

- padronização textual (upper + trim)
- unificação de categorias equivalentes

#### Inconsistência estrutural

A coluna `categoria_eixo` apresentava mistura de formatos (texto e numérico).

**Tratamento aplicado:**

- extração de valores numéricos
- conversão para tipo numérico

#### Inconsistência numérica

A coluna `volume_total` estava em formato textual com padrão brasileiro:

```
277638,00
```

**Tratamento aplicado:**

- remoção de separadores
- conversão para tipo numérico

### Resultado da limpeza

Após os tratamentos:

- **0 registros inválidos** (dados essenciais preservados)
- **0 duplicidades estruturais** no nível de análise
- granularidade consistente (mensal)
- tipagem adequada para cálculo


### Conclusão

A etapa de exploração revelou que os principais problemas do dataset não estavam na ausência de dados, mas na falta de padronização e consistência estrutural.

Ao corrigir esses pontos ainda no pipeline, foi possível transformar uma base potencialmente inconsistente em um dataset confiável, adequado para construção de indicadores operacionais e análises estratégicas.

Com isso, o tráfego passa a ser analisado de forma consistente ao longo do tempo, permitindo interpretar não apenas volume, mas também comportamento, impacto e concentração dentro da concessão.

## Camada Silver (Tratamento e Padronização)

A camada Silver tem como objetivo transformar os dados já filtrados na Bronze, **restritos à granularidade mensal**, em uma base consistente, padronizada e pronta para modelagem analítica.

Diferente da etapa anterior, aqui o foco não é mais selecionar dados, mas **corrigir inconsistências estruturais e semânticas**, garantindo que cada registro represente corretamente uma observação única do sistema.

### Padronização de texto

As colunas categóricas passaram por normalização para eliminar variações de formatação que poderiam gerar duplicidade lógica:

- remoção de espaços em branco
- conversão para letras maiúsculas
- padronização de valores equivalentes

Exemplo:

```text
VEÍCULO PEQUENO → PASSEIO
VEICULO PEQUENO → PASSEIO
```

Esse tratamento garante consistência nas análises segmentadas, evitando que a mesma categoria seja interpretada como múltiplos grupos distintos.

### Tratamento numérico

A coluna `volume_total`, originalmente armazenada como texto com formatação brasileira, foi convertida para tipo numérico, permitindo seu uso em cálculos.

Além disso, a coluna `categoria_eixo` passou por extração de valores numéricos, removendo inconsistências como textos misturados com números.

Esse processo garante que ambas as colunas possam ser utilizadas corretamente em agregações e métricas derivadas.

### Padronização temporal

A coluna `mes_ano` apresentava múltiplos formatos, mesmo após o filtro mensal na Bronze, incluindo:

- datas completas (`DD/MM/AAAA`)
- representações reduzidas (`MM/AAAA`)

Para garantir consistência temporal:

- todos os formatos foram convertidos para `datetime`
- os valores foram padronizados para o **primeiro dia do mês** (`YYYY-MM-01`)

Essa padronização permite agregações corretas e integração direta com dimensões de tempo na camada analítica.

### Resolução de conflitos de granularidade

Mesmo após a remoção de dados diários na Bronze, foram identificados casos em que múltiplos registros apresentavam:

```text
mesma chave analítica, mas valores diferentes de volume
```

A chave considerada foi:

- concessionária
- período (`mes_ano`)
- praça
- tipo de veículo
- categoria de eixo
- sentido
- tipo de cobrança

Esses conflitos indicam múltiplas versões de dados para a mesma observação (ex.: reprocessamentos ou inconsistências na origem).

**Tratamento aplicado:**

- identificação dos grupos conflitantes
- consolidação utilizando o valor **máximo de volume_total**

Essa decisão evita subestimação do tráfego e garante consistência sem inflar os valores (como ocorreria com soma).

### Consolidação e unicidade

Após a resolução de conflitos, os dados foram:

- agregados no nível da chave analítica
- deduplicados
- validados para garantir unicidade

Ao final do processo:

- não há duplicidades no nível de análise
- cada linha representa uma observação única e consistente

### Remoção de registros inválidos

Foram removidos registros que não atendiam aos critérios mínimos de qualidade:

- datas não convertidas
- volumes nulos ou inválidos

Esse passo garante integridade dos dados sem comprometer a representatividade do dataset.

### Resultado da camada Silver

A camada Silver entrega um dataset:

- consistente em granularidade (mensal)
- padronizado em categorias e tipos de dados
- livre de duplicidades estruturais
- confiável para construção de métricas

O resultado final é salvo em:

[silver/antt_trafego_silver.parquet](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/silver)

### Consideração final

O principal ganho desta etapa não está apenas na limpeza dos dados, mas na garantia de consistência analítica.

Ao resolver conflitos, padronizar formatos e assegurar unicidade, a camada Silver elimina ambiguidades que poderiam distorcer indicadores, permitindo que as análises da camada Gold reflitam o comportamento real do tráfego, e não inconsistências da fonte.

## Camada Gold (Modelo Analítico)

A camada Gold tem como objetivo transformar os dados tratados na Silver em um modelo analítico estruturado, orientado ao consumo em ferramentas de BI e à geração de indicadores de negócio.

Nesta etapa, o foco deixa de ser limpeza e passa a ser modelagem, garantindo que os dados possam ser explorados de forma eficiente, consistente e com significado operacional.

### Modelagem dimensional

Foi adotado um modelo estrela, separando claramente:

- **fatos** → onde estão as métricas
- **dimensões** → que dão contexto às análises

Essa abordagem reduz redundância, melhora performance e facilita a construção de medidas no Power BI.

### Tabela fato Tráfego

A tabela `fato_trafego` representa o núcleo analítico do modelo.

Ela foi construída a partir da agregação da Silver no seguinte grão:

- mês
- praça
- concessionária
- tipo de veículo
- categoria de eixo

Esse nível garante consistência com a granularidade mensal já tratada anteriormente e evita dupla contagem.

### Métricas derivadas

A partir dessa base, foram construídos indicadores fundamentais para análise:

#### Volume Total

Representa o total de veículos no período e serve como base para todos os cálculos.

#### VMD (Volume Médio Diário)

```text
VMD = volume_total / dias_mes
```

Permite comparar meses com diferentes quantidades de dias e traduz o fluxo para uma escala operacional diária.

#### Fator de Desgaste

Baseado na categoria de eixo:

```text
fator_desgaste = eixo^4
```

Esse cálculo segue o princípio da **Lei da Quarta Potência**, amplamente utilizada na engenharia rodoviária, segundo a qual o dano ao pavimento cresce de forma exponencial com o aumento da carga.

Como o dataset não possui peso por eixo, a `categoria_eixo` foi utilizada como proxy de carga. Valores nulos ou zero foram tratados como 1, assumindo impacto mínimo equivalente a veículos leves.

Esse indicador permite capturar um ponto essencial:

```text
poucos veículos pesados podem gerar a maior parte do desgaste
```

#### Participação da Praça

```text
volume_praca / volume_total_do_mes
```

Calculada dentro do contexto de cada mês, essa métrica permite analisar concentração de fluxo e identificar praças com maior relevância operacional.

### Tabela fato Operacional

Além da visão de tráfego, foi criada uma segunda fato (`fato_operacional`) com foco em comportamento operacional, agregando por:

- mês
- praça
- tipo de cobrança
- sentido

Essa separação evita misturar granularidades analíticas diferentes e permite análises específicas sobre operação (ex.: distribuição de cobrança e fluxo direcional).

### Dimensões

As dimensões foram estruturadas para enriquecer o contexto analítico:

#### Tempo (`dim_tempo`)

Inclui atributos como:

- ano
- mês
- nome do mês
- trimestre
- chave ordenável

Permite análises temporais consistentes e ordenação correta nos visuais.

#### Praça (`dim_praca`)

Identifica as praças de pedágio, permitindo análise espacial do fluxo.

#### Concessionária (`dim_concessionaria`)

Permite segmentar análises por operador, viabilizando comparações.

#### Veículo (`dim_veiculo`)

Combina:

- tipo de veículo
- categoria de eixo

Além disso, inclui classificação derivada:

```text
COMERCIAL → PESADO
outros → LEVE
```

Essa dimensão é fundamental para análises de impacto estrutural.

#### Cobrança (`dim_cobranca`)

Representa os tipos de pagamento, permitindo análises operacionais.

#### Sentido (`dim_sentido`)

Permite analisar o fluxo direcional da rodovia.

### Chaves e integridade

As tabelas foram conectadas por chaves consistentes:

- `id_tempo`
- `id_praca`
- `id_concessionaria`
- `id_veiculo`
- `id_cobranca`
- `id_sentido`

A construção das chaves garante:

- integridade referencial
- ausência de ambiguidade
- compatibilidade com modelo estrela

### Resultado final

Os dados são disponibilizados na camada Gold em formato parquet:

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

### Consideração final

A camada Gold não apenas organiza os dados, ela define como o problema será analisado.

Ao estruturar o modelo em torno de volume, desgaste e concentração, o projeto deixa de ser apenas descritivo e passa a capturar a dinâmica real da rodovia, permitindo identificar:

- intensidade de uso
- impacto na infraestrutura
- pontos de maior pressão operacional

Com isso, os dados se tornam diretamente utilizáveis para tomada de decisão, sem necessidade de tratamentos adicionais no consumo.

## Indicadores

Após a reconstrução do modelo e das pipelines, todas as medidas do painel foram revisadas com foco em **consistência de contexto, comparabilidade e significado operacional**.

Os indicadores foram organizados em três blocos principais: **volume**, **desgaste** e **criticidade**, permitindo interpretar o sistema de forma integrada.

### Volume e distribuição de tráfego

A base de todas as análises é o volume de veículos.

```DAX
Volume Total = SUM(fato_trafego[volume_total])
```

A partir dele, derivam-se métricas de participação e segmentação:

- **% Volume** → distribuição do tráfego por tipo de veículo
- **% Fluxo Praça** → participação de cada praça no fluxo total
- **% Cobrança** → distribuição por tipo de pagamento

Essas medidas utilizam `ALLSELECTED`, garantindo que os percentuais sejam calculados **dentro do contexto do filtro ativo (ano, concessionária, etc.)**, evitando distorções.

### Volume Médio Diário (VMD)

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

O VMD traduz o volume mensal para uma escala diária, permitindo comparar períodos com diferentes quantidades de dias.

Diferente de uma simples divisão, o cálculo considera corretamente o contexto temporal filtrado, evitando erros em agregações multi-mês.

### Segmentação por tipo de veículo

Foram criadas medidas específicas para entender o papel dos veículos pesados:

- **Volume Pesado**
- **% Pesados**
- **% Volume Comercial**

Essas métricas permitem identificar o quanto da demanda está associada a transporte de carga.

### Desgaste da via

O desgaste é um dos pilares analíticos do projeto.

```DAX
Desgaste Total =
SUMX(
    fato_trafego,
    fato_trafego[volume_total] * fato_trafego[fator_desgaste]
)
```

Esse cálculo incorpora o fator de desgaste (baseado na Lei da Quarta Potência), permitindo capturar o impacto não linear dos veículos pesados.

A partir disso, derivam-se:

- **Desgaste Pesado** → impacto gerado apenas por veículos pesados
- **% Desgaste** → distribuição do desgaste por tipo de veículo
- **% Desgaste Praça** → concentração do impacto por praça

### Relação entre volume e desgaste

Um dos pontos centrais do projeto é comparar:

```text
quanto um grupo representa no volume vs quanto ele representa no desgaste
```

Exemplo:

```DAX
Insight Comercial
```

Essa medida traduz automaticamente o desequilíbrio entre volume e impacto, evidenciando que:

```text
veículos comerciais tendem a representar menos volume, mas maior desgaste
```

### Eixo médio ponderado

```DAX
Eixo Médio Ponderado =
DIVIDE(
    SUMX(fato_trafego, fato_trafego[categoria_eixo] * fato_trafego[volume_total]),
    [Volume Total]
)
```

Esse indicador sintetiza o “peso médio” da frota, funcionando como proxy da carga média circulante na rodovia.

### Índice de Gargalo (criticidade operacional)

O principal indicador do projeto é o índice de gargalo.

```DAX
Indice Gargalo =
VAR PesoDesgaste =
    DIVIDE([Desgaste Total], [Volume Total])

VAR Concentracao =
    [% Fluxo Praça]

RETURN
    [Volume Total] * PesoDesgaste * Concentracao
```

Esse índice combina três fatores:

- **volume** → intensidade de uso
- **desgaste médio** → impacto estrutural
- **concentração** → relevância da praça no sistema

Na prática, ele identifica:

```text
onde há mais fluxo + mais impacto + mais concentração
```

### Normalização do índice

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

A normalização transforma o índice em uma escala relativa (0 a 1), permitindo comparar praças dentro do contexto filtrado.

O uso de `ALLSELECTED` garante que a comparação seja feita **apenas dentro do recorte atual**, evitando distorções globais.

### Classificação de criticidade

```DAX
Categoria Gargalo
```

As praças são classificadas em três níveis:

- **Alta Pressão**
- **Atenção**
- **Baixa Pressão**

Essa categorização simplifica a interpretação e transforma o indicador em um instrumento direto de decisão.

### Ordenação e priorização

```DAX
Ordem Gargalo
```

Permite ordenar visualmente as praças por criticidade, facilitando a identificação dos principais pontos de atenção.

### Consideração final

O conjunto de indicadores foi desenhado para responder não apenas “quanto passa”, mas principalmente:

```text
onde o sistema está mais pressionado
```

Ao combinar volume, desgaste e concentração, o modelo permite identificar pontos críticos da operação de forma objetiva, transformando dados de tráfego em um instrumento de priorização operacional.


## Visualizações

O dashboard foi estruturado para traduzir os indicadores em uma leitura direta do comportamento operacional da rodovia, organizando as informações em blocos que respondem, de forma progressiva:

```text
quanto passa → quem impacta → onde está o problema
```

### Visão geral (KPIs)

No topo do painel, são apresentados os principais indicadores sintéticos:

- **Volume Médio Diário (VMD)**
- **Volume Total**
- **% de Veículos Pesados**
- **% de Desgaste gerado por Pesados**

Essa combinação permite uma leitura imediata do sistema:

- o **VMD** traduz o ritmo diário da rodovia
- o **Volume Total** indica a escala do tráfego
- a comparação entre **% Pesados vs % Desgaste** evidencia o impacto desproporcional dos veículos comerciais

### Insight automático

Logo abaixo, um destaque textual sintetiza o principal insight do período:

```text
Veículos comerciais representam X% do volume, mas Y% do desgaste da via.
```

Essa frase elimina a necessidade de interpretação manual e evidencia diretamente o desequilíbrio entre demanda e impacto estrutural.

### Volume vs Desgaste por tipo de veículo

O gráfico de colunas compara:

- **% Volume**
- **% Desgaste**

por tipo de veículo (comercial, passeio e moto).

Essa visualização é central para o entendimento do modelo, pois demonstra que:

```text
veículos comerciais concentram a maior parte do desgaste, mesmo sem representar todo o volume
```

### Evolução do VMD ao longo do tempo

O gráfico de linha apresenta o VMD por mês, permitindo identificar:

- tendências de crescimento ou queda
- possíveis padrões sazonais
- variações operacionais ao longo do ano

Essa visão temporal complementa a análise estática dos KPIs.

### Distribuição por tipo de cobrança

O gráfico de rosca mostra a participação dos diferentes tipos de cobrança:

- automática
- manual
- OCR/placa

Essa visualização permite avaliar o nível de automação da operação e possíveis impactos na fluidez do tráfego.

### Índice de Gargalo por praça

O gráfico de barras apresenta o **Índice de Gargalo Normalizado**, permitindo comparar diretamente as praças dentro do contexto selecionado.

A normalização transforma o indicador em uma escala relativa (0 a 100%), facilitando a leitura e o ranking.

### Tabela de criticidade operacional

A tabela consolida a análise por praça, apresentando:

- **% de criticidade**
- **categoria de gargalo** (Alta Pressão, Atenção, Baixa Pressão)

Essa visualização funciona como um resumo operacional, permitindo identificar rapidamente:

```text
quais praças concentram maior pressão no sistema
```

### Interpretação do gargalo

Ao lado da tabela, um bloco explicativo orienta a leitura do indicador:

```text
Criticidade operacional combina:
• volume de tráfego
• impacto dos veículos (desgaste)
• participação da praça no fluxo total
```

Esse apoio conceitual garante que o usuário compreenda o significado do indicador sem necessidade de conhecer sua formulação técnica.

### Consideração final

As visualizações foram desenhadas para reduzir a carga cognitiva e priorizar interpretação rápida.

O painel não exige conhecimento prévio do modelo, permitindo que qualquer usuário entenda:

- o nível de tráfego
- o impacto estrutural dos veículos
- e, principalmente, onde estão os pontos críticos da operação

Com isso, o dashboard deixa de ser apenas descritivo e passa a atuar como um instrumento de diagnóstico operacional.

## Insights

### Cenário geral: CRO em 2025

<img width="1480" height="830" alt="image" src="https://github.com/user-attachments/assets/d3785a40-e4f2-40bf-8902-28dbf89649cf" />

Na visão consolidada da concessionária, o tráfego apresenta um volume elevado (30,2 milhões de veículos no ano) com um VMD de aproximadamente 82 mil veículos/dia. À primeira vista, isso poderia sugerir que o principal desafio é capacidade de fluxo. Mas o dado mais relevante está na composição:
- 54,60% do volume é comercial
- 99,67% do desgaste vem desses veículos

Isso muda completamente a leitura do problema. O sistema não está pressionado apenas por quantidade, mas principalmente por tipo de carga circulante. O desgaste da rodovia é praticamente monopolizado por veículos pesados, o que indica que qualquer aumento marginal nesse grupo tem impacto desproporcional na infraestrutura.

Outro ponto importante é a distribuição de cobrança, com predominância de meios automáticos, mas ainda com participação relevante de cobrança manual. Isso sugere espaço para ganho operacional, especialmente em momentos de pico.

### Primeiro cenário: Praça P2 (Alta Pressão)

<img width="1478" height="828" alt="image" src="https://github.com/user-attachments/assets/669f5cae-099d-41f5-a445-a407736ef04a" />

Ao isolar a praça P2, o padrão estrutural se mantém, mas com intensificação do problema:
- VMD: 14.247
- Volume anual: 5,2 milhões
- Criticidade: 100% (máximo do modelo)

Aqui, a praça se posiciona como o principal gargalo da operação. O volume é alto, mas o fator crítico continua sendo a composição: mais da metade do tráfego é comercial e praticamente todo o desgaste vem desse grupo.

O ponto mais relevante é que a P2 não é apenas movimentada, ela é estrategicamente carregada, provavelmente associada a rotas logísticas importantes.

**Insight acionável:**
A P2 deve ser tratada como prioridade operacional. Possíveis ações incluem:
- aumento de capacidade (faixas, cabines, automação)
- monitoramento contínuo de fluxo pesado
- planejamento de manutenção preventiva mais frequente

### Segundo cenário: Praça P4 (Alta Pressão)

<img width="1479" height="830" alt="image" src="https://github.com/user-attachments/assets/da966d1c-4f90-4d42-8009-1124db502195" />

A praça P4 também aparece como crítica, mas com um comportamento ligeiramente diferente:
- VMD: 13.283
- Volume anual: 4,8 milhões
- Criticidade: 77,95% (ainda alta)

Embora o volume seja um pouco menor que o da P2, a P4 mantém um nível elevado de pressão operacional. Isso indica que o gargalo aqui não depende apenas de volume absoluto, mas da relação entre fluxo, desgaste e concentração.

A distribuição de cobrança mostra uma leve diferença, com maior participação de meios manuais em relação ao cenário geral. Isso pode contribuir para fricções operacionais.

**Insight acionável:**
Na P4, além da questão estrutural, existe um componente operacional relevante. A melhoria aqui pode vir de:
- incentivo ao uso de cobrança automática
- redistribuição de fluxo entre cabines
- ajustes operacionais antes de investimentos estruturais

### Terceiro cenário: Praça P6 (Transição para Alta Pressão)

<img width="1480" height="829" alt="image" src="https://github.com/user-attachments/assets/de4fe980-efa7-44d7-af88-589df676d6fa" />

A praça P6 apresenta um cenário interessante de transição:
- VMD: 9.363
- Volume anual: 3,4 milhões
- Criticidade: 53,09% (limite entre atenção e alta pressão)

Aqui, o volume é menor, mas a composição do tráfego mantém o padrão crítico: predominância de veículos comerciais e alto impacto no desgaste.

O que diferencia a P6 é que ela ainda não atingiu o nível máximo de pressão, mas está claramente no caminho. É um caso clássico de gargalo emergente.

**Insight acionável:**
A P6 é o melhor ponto para atuação preventiva:
- antecipar melhorias antes de virar gargalo crítico
- monitorar evolução do fluxo pesado
- testar intervenções operacionais com menor custo

### Conclusão estratégica

Os cenários mostram um padrão consistente: o problema não é apenas quanto passa, mas o que passa e onde passa.

- P2 → gargalo consolidado (agir imediatamente)
- P4 → gargalo estrutural + operacional (otimizar + ajustar)
- P6 → gargalo emergente (prevenir antes de escalar)

A combinação entre volume, composição e concentração permite priorizar ações com mais precisão, saindo de uma gestão reativa para uma abordagem orientada por dados.

