# Volume de tráfego por Praça
``Concessionária Rota do Oeste (CRO)``

## Contexto
O objetivo inicial do projeto consiste em analisar o tráfego da concessionária Rota do Oeste (CRO), a partir dos dados abertos disponibilizados pela Agência Nacional de Transportes Terrestres (ANTT).

Embora o escopo proposto esteja centrado na CRO, o processo foi estruturado de forma mais abrangente, contemplando a ingestão completa do dataset nacional. Essa abordagem permite:

- Preservar o histórico integral dos dados
- Garantir consistência analítica
- Possibilitar comparações e extensões futuras

A análise foi conduzida com uma perspectiva não descritiva, mas também operacional e estratégica, buscando responder questões relevantes para o negócio da concessão rodoviária:

1. Qual o volume médio diário de veículos (VMD) ao longo do tempo?
2. Qual a participação de veículos pesados e seu impacto potencial no desgaste do pavimento?
3. Existem padrões de sazonalidade no tráfego?
4. Como se distribui o fluxo entre os diferentes tipos de cobrança?
5. Há indícios de gargalos operacionais nas praças de pedágio?

Essa abordagem permite utilizar os dados de tráfego não apenas como contagem de veículos, mas como um indicador indireto do comportamento logístico e operacional da rodovia.

## Ingestão
Antes de iniciar a análise solicitada, foi necessário realizar o processo de ingestão dos dados disponibilizados pela ANTT.
O portal de dados abertos da ANTT publica o conjunto "Volume de Tráfego por Praça de Pedágio" em diversos arquivos CSV, separados por ano e por tipo de consolidação (diário ou mensal). Como o objetivo do estudo á analisar o comportamento de tráfego da concessionária Rota do Oeste (CRO), optei por ingerir todos os arquivos disponíveis no dataset, em vez de baixar apenas um subconjunto específico.

A abordagem adotada garante trêm benefícios principais:
- Evita perda de histórico de dados
- Permite análises temporais mais completas
- Torna o processo reprodutível e automatizado

Para isso, foi desenvolvido um [script em Python](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/pipeline_bronze_antt.py) responsável por acessar automaticamente a API do portal de dados da ANTT, identificar todos os arquivos disponíveis e realizar o download dos arquivos em formato CSV.

### Processo de coleta automatizada

O pipeline de ingestão foi implementado utilizando as bibliiotecas ``requests`` e ``pandas``.

O fluxo de ingestão funciona da seguinte forma:
1. Consulta à API do portal de dados da ANTT para identificar todos os recursos disponíveis no dataset.
2. Registro das informações de cada recurso (nome do arquivo, formato, tamanho e URL) em um [log de ingestão](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/log), permitindo rastrear quais arquivos estavam disponíveis no momento da coleta.
3. Download automático de todos os arquivos CSV do dataset.
4. Armazenamento dos arquivos em uma pasta local para manter uma cópia bruta dos dados.
5. Leitura e consolidação dos arquivos em um único [dataset estruturado em formato parquet](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/bronze).

Durante essa etapa foram aplicadas apenas padronizações estruturais mínimas, como:

- Padronização do número de colunas
- Remoção de linhas duplicadas de cabeçalho presentes em alguns arquivos

Nenhuma transformação analítica foi realizada nesta fase. Todos os dados foram preservados em formato textual para que o tratamento e a modelagem fossem realizados posteriormente em outro script.

## Exploração

O [dataset consolidado](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/bronze) contém **7.045.039 registros** e as seguintes colunas:

| Coluna          | Descrição                                            |
| --------------- | ---------------------------------------------------- |
| concessionaria  | Identifica a concessionária responsável pela rodovia |
| mes_ano         | Período de referência do registro                    |
| sentido         | Direção do fluxo                                     |
| praca           | Praça de pedágio onde o tráfego foi registrado       |
| tipo_cobranca   | Modalidade de pagamento                              |
| categoria_eixo  | Categoria do veículo baseada no número de eixos      |
| tipo_de_veiculo | Classificação do veículo                             |
| volume_total    | Quantidade de veículos registrados                   |
| arquivo_origem  | Nome do arquivo de origem do dado                    |

### Metadado de origem

Durante a ingestão, foi adicionada a coluna `arquivo_origem`, permitindo rastrear a origem de cada registro.

Esse metadado foi essencial para identificar diferenças estruturais entre os arquivos disponibilizados pela ANTT, especialmente:

- coexistência de dados diários e mensais
- variações no formato da coluna de data
- inconsistências de padronização entre anos

Essa abordagem garante maior rastreabilidade e evita interpretações incorretas decorrentes da mistura de diferentes granularidades.

### Colunas relevantes para análise

A estrutura do dataset permite analisar a concessão sob múltiplas perspectivas:

#### 1. Tráfego (demanda)

Utilizado para medir volume e evolução do fluxo:

- `volume_total`
- `mes_ano`
- `praca`


#### 2. Logística (direcionalidade)

Permite identificar padrões de deslocamento, como escoamento vs retorno:

- `sentido`
- `praca`

#### 3. Receita e desgaste

Permite analisar o impacto dos veículos na infraestrutura:

- `categoria_eixo`
- `tipo_de_veiculo`

Veículos pesados tendem a gerar maior receita, mas também maior desgaste do pavimento.

#### 4. Operação (eficiência de praça)

Permite avaliar a eficiência operacional das praças de pedágio:

- `tipo_cobranca`

Possibilita análises sobre distribuição entre pagamento manual e automático, além de potenciais gargalos operacionais.

#### Considerações gerais

O dataset permite uma análise integrada que vai além do volume de tráfego, possibilitando avaliar simultaneamente:

- comportamento da demanda
- padrões logísticos
- impacto na infraestrutura
- eficiência operacional

## Qualidade dos dados

A qualidade dos dados foi avaliada por meio de diagnósticos automatizados, com geração de evidências na pasta [evidencias](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias):

```
evidencias/
├─ nulos.csv
├─ duplicados_amostra.csv
├─ amostra_valores.csv
├─ tipos_mistos.csv
```

### Valores nulos

Não foram identificados valores nulos no dataset.

→ [evidencias/nulos.csv](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias/nulos.csv)

No entanto, essa ausência não garante qualidade plena, pois os dados foram ingeridos como texto, podendo mascarar valores ausentes representados como strings.

### Duplicidades e granularidade

Foram identificadas **72.035 linhas duplicadas**, representando pouco mais de 1% do dataset.

→ [evidencias/duplicados_amostra.csv](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias/duplicados_amostra.csv)

Essas duplicidades não são apenas registros repetidos, mas indicam a coexistência de diferentes níveis de granularidade:

- dados diários
- dados mensais consolidados

Esse cenário representa um risco crítico, pois pode levar à **dupla contagem de volumes**, distorcendo indicadores.

Portanto, torna-se necessário tratar a granularidade antes da análise, garantindo consistência temporal.

### Inconsistência semântica

Na coluna `tipo_de_veiculo`, foram identificadas múltiplas representações para a mesma categoria:

→ [evidencias/amostra_valores.csv](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias/amostra_valores.csv)

Exemplo:

```
Passeio
PASSEIO
Comercial
COMERCIAL
Moto
MOTO
Veículo Pequeno
```

Essa inconsistência indica ausência de padronização na origem, gerando duplicidade lógica de categorias e risco de distorção em análises segmentadas.

### Inconsistência estrutural

A coluna `categoria_eixo` apresenta mistura de formatos:

| tipo     | total registros |
| -------- | --------------- |
| Numérico | 6.290.836       |
| Texto    | 754.203         |

→ [evidencias/tipos_mistos.csv](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias/tipos_mistos.csv)

Isso evidencia inconsistência na modelagem do dado, com múltiplos padrões de registro.

### Inconsistência numérica

A coluna `volume_total` está armazenada como texto com formatação brasileira:

```
277638,00
24788,00
703,00
```

→ [evidencias/amostra_valores.csv](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/evidencias/amostra_valores.csv)

Esse formato impede o uso direto em cálculos, exigindo conversão para tipo numérico.

### Inconsistência temporal

A coluna `mes_ano` apresenta múltiplos formatos dependendo do arquivo de origem:

- formato data (DD/MM/AAAA)
- formato textual (ex.: "jan/2024")

Essa variação dificulta a padronização da coluna e pode gerar perda de informação durante a transformação.

Essa inconsistência está diretamente relacionada à origem dos dados (diário vs mensal), reforçando a importância do uso do metadado `arquivo_origem`.


### Conclusão sobre qualidade

A qualidade dos dados é impactada principalmente por:

- falta de padronização entre arquivos
- coexistência de múltiplas granularidades
- inconsistências de formato (texto, numérico e data)

Esses fatores exigem tratamento na camada analítica, incluindo:

- padronização de categorias
- normalização de tipos de dados
- controle de granularidade

Garantindo, assim, a confiabilidade dos indicadores construídos.

## Camada Silver (Tratamento e Padronização)

A camada Silver tem como objetivo transformar os dados brutos da Bronze em um formato consistente, confiável e adequado para análise.

Nessa etapa, foram aplicados tratamentos para resolver os principais problemas de qualidade identificados durante a exploração dos dados.

Foram realizadas padronizações de texto, incluindo remoção de espaços e uniformização para letras maiúsculas, além da normalização de categorias de veículos, eliminando variações semânticas como “VEÍCULO PEQUENO” e “PASSEIO”. Também foi feita a conversão de campos numéricos que estavam armazenados como texto, como o volume de tráfego, e a extração de valores numéricos da coluna de categoria de eixo.

A coluna de data apresentava múltiplos formatos, incluindo datas completas e representações textuais como “jan/2026”. Para garantir consistência temporal, foi aplicada uma conversão padronizada, tratando ambos os formatos e consolidando todos os registros em um único padrão de data.

Outro ponto crítico foi o controle de granularidade. Os dados da ANTT incluem registros diários e mensais, o que pode gerar dupla contagem. Para evitar esse problema, foram removidos os dados diários com base no metadado de origem dos arquivos, mantendo apenas os dados mensais consolidados.

Também foram removidos registros inválidos, como aqueles com datas não convertidas ou volumes inconsistentes, garantindo integridade analítica.

Por fim, os dados foram agregados considerando concessionária, período, praça, sentido, tipo de cobrança, categoria de eixo e tipo de veículo, eliminando duplicidades e consolidando os volumes.

O resultado dessa camada é um dataset limpo, padronizado e consistente, salvo em:

[silver/antt_trafego_silver.parquet](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/silver)

## Camada Gold (Modelo Analítico)

A camada Gold tem como objetivo estruturar os dados para consumo analítico, organizando-os em um modelo dimensional adequado para ferramentas de visualização.

Foi adotado um modelo estrela, composto por uma tabela fato e múltiplas dimensões.

A tabela fato concentra as métricas principais, como volume de tráfego, volume médio diário (VMD), fator de desgaste e participação do fluxo por praça. Essas métricas permitem analisar tanto o comportamento da demanda quanto o impacto na infraestrutura.

As dimensões foram estruturadas para dar contexto aos dados, incluindo tempo, praça, concessionária, veículo, tipo de cobrança e sentido. Cada dimensão contém atributos descritivos que permitem segmentar e analisar os dados sob diferentes perspectivas.

Durante essa etapa, também foram criadas métricas derivadas importantes. O VMD foi calculado a partir do volume mensal ajustado pelo número de dias do mês. O fator de desgaste foi estimado com base na categoria de eixo, como uma aproximação do impacto dos veículos no pavimento. Já a participação por praça foi calculada para permitir análises de concentração de fluxo.

> O cálculo do fator de desgaste foi fundamentado em um princípio clássico da engenharia rodoviária conhecido como Lei da Quarta Potência, segundo o qual o dano causado ao pavimento por veículos é proporcional à quarta potência da carga aplicada por eixo. Esse modelo, amplamente utilizado em estudos de dimensionamento e conservação de pavimentos, parte da evidência empírica de que o desgaste não cresce de forma linear com o aumento da carga, mas sim de maneira exponencial, de modo que pequenos incrementos na carga resultam em aumentos desproporcionais no dano estrutural.
> Considerando que o conjunto de dados utilizado não disponibiliza informações diretas sobre o peso por eixo dos veículos, adotou-se a variável categoria_eixo como uma aproximação (proxy) da magnitude de carga. Essa escolha se apoia no entendimento de que, em média, veículos com maior número de eixos estão associados a operações de transporte mais pesado, sendo, portanto, mais representativos do impacto estrutural no pavimento. A partir dessa premissa, aplicou-se a elevação à quarta potência sobre essa variável, de forma a incorporar o comportamento não linear descrito pela teoria, resultando em um indicador proporcional de desgaste.
> Adicionalmente, valores nulos ou iguais a zero foram tratados como unidade, assumindo um nível mínimo de impacto equivalente ao de veículos leves. Essa decisão evita a introdução de valores nulos no modelo e preserva a coerência do indicador, impedindo que registros sem informação contribuam com desgaste inexistente, o que não seria fisicamente plausível.

A modelagem seguiu boas práticas, com separação clara entre fato e dimensões, eliminação de redundâncias e padronização de chaves, garantindo consistência e performance no consumo analítico.

Os dados finais são disponibilizados nos seguintes arquivos:

```
gold/
├─ fato_trafego.parquet
├─ dim_tempo.parquet
├─ dim_praca.parquet
├─ dim_concessionaria.parquet
├─ dim_veiculo.parquet
├─ dim_cobranca.parquet
├─ dim_sentido.parquet
```

A separação em camadas permite maior controle sobre a qualidade dos dados, facilita a manutenção do pipeline e garante que as análises sejam construídas sobre uma base confiável e consistente.


## Indicador

Os indicadores foram construídos com o objetivo de traduzir os dados de tráfego em métricas acionáveis, permitindo analisar volume, composição do tráfego, impacto na infraestrutura e eficiência operacional.

### Volume e Intensidade de Tráfego

#### Média VMD (Volume Médio Diário)

Calcula a média do volume diário de veículos ao longo do tempo.

```DAX
Média VMD = AVERAGE(fato_trafego[vmd])
```

Esse indicador permite acompanhar a intensidade média de uso da rodovia, sendo essencial para análise de capacidade e planejamento operacional.


#### Volume Total

Representa o total de veículos que passaram pela rodovia no período analisado.

```DAX
Volume Total = SUM(fato_trafego[volume_total])
```

É a principal métrica de escala da operação.

### Composição do Tráfego

#### Volume Pesado

Filtra o volume total considerando apenas veículos pesados.

```DAX
Volume Pesado = 
CALCULATE(
    [Volume Total],
    dim_veiculo[tipo_peso] = "PESADO"
)
```

#### % Pesados

Calcula a participação dos veículos pesados no tráfego total.

```DAX
% Pesados = 
DIVIDE([Volume Pesado], [Volume Total])
```

Permite entender a composição do tráfego, fator crítico para análise de desgaste da rodovia.

### Impacto na Infraestrutura

#### Desgaste Total

Calcula o impacto total no pavimento considerando o volume de veículos ponderado pelo fator de desgaste (baseado na categoria de eixo).

```DAX
Desgaste Total = 
SUMX(
    fato_trafego,
    fato_trafego[volume_total] * fato_trafego[fator_desgaste]
)
```

#### Desgaste Pesado

Isola o impacto gerado apenas por veículos pesados.

```DAX
Desgaste Pesado = 
CALCULATE(
    [Desgaste Total],
    dim_veiculo[tipo_peso] = "PESADO"
)
```

#### % Desgaste Pesado

Mede quanto do desgaste total é causado por veículos pesados.

```DAX
% Desgaste Pesado = 
DIVIDE([Desgaste Pesado], [Desgaste Total])
```

Esse indicador evidencia o desbalanceamento entre volume e impacto, sendo essencial para decisões de manutenção.

---

### Sazonalidade

#### Volume Mensal

Agrega o volume de tráfego por período.

```DAX
Volume Mensal = SUM(fato_trafego[volume_total])
```

#### Índice Sazonal

Compara o volume de um período com a média geral, identificando padrões sazonais.

```DAX
Indice Sazonal = 
DIVIDE(
    [Volume Mensal],
    CALCULATE(
        [Volume Mensal],
        ALL(dim_tempo[mes])
    )
)
```

Valores acima de 1 indicam períodos com tráfego acima da média.

### Eficiência de Cobrança

#### Volume por Cobrança

Calcula o volume total por tipo de cobrança.

```DAX
Volume por Cobranca = 
SUM(fato_trafego[volume_total])
```

#### % Cobrança

Mostra a participação de cada tipo de cobrança no total.

```DAX
% Cobranca = 
DIVIDE(
    [Volume por Cobranca],
    CALCULATE([Volume Total], ALL(dim_cobranca))
)
```

Esse indicador permite avaliar a adoção de meios automáticos e oportunidades de otimização operacional.


### Distribuição e Gargalos Operacionais

#### % Fluxo por Praça

Mede a participação média de cada praça no fluxo total.

```DAX
% Fluxo Praca = 
AVERAGE(fato_trafego[participacao_praca])
```

#### Concentração por Praça

Identifica o maior nível de concentração de fluxo em cada praça.

```DAX
Concentracao Praca = 
MAX(fato_trafego[participacao_praca])
```

#### Ranking de Praças

Ordena as praças com base no volume total de tráfego.

```DAX
Ranking Praca = 
RANKX(
    ALL(dim_praca[praca]),
    [Volume Total],
    ,
    DESC
)
```

#### Índice de Gargalo

Combina volume e concentração para identificar potenciais gargalos operacionais.

```DAX
Indice Gargalo = 
SUMX(
    fato_trafego,
    fato_trafego[participacao_praca] * fato_trafego[vmd]
)
```

Esse indicador destaca praças que apresentam alto fluxo combinado com alta concentração, sendo um proxy para risco de sobrecarga operacional.

### Objetivo dos Indicadores

Os indicadores foram estruturados para responder, de forma integrada:

- Qual o volume e intensidade do tráfego
- Como o tráfego está distribuído entre tipos de veículos
- Qual o impacto sobre a infraestrutura
- Como o fluxo varia ao longo do tempo
- Onde estão os principais gargalos operacionais

## Visualizações

O [dashboard](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/trafego_cro_2024.pdf) foi estruturado com foco em responder, de forma clara e direta, as principais perguntas de negócio relacionadas ao tráfego, desgaste da infraestrutura e eficiência operacional da concessionária.

A escolha dos visuais seguiu o princípio de clareza analítica mais apoio à decisão, evitando excesso de elementos e priorizando leitura rápida.

### KPIs

Foram utilizados cartões para apresentar os principais indicadores:
- Volume Total de Tráfego
- Volume Médio Diário (VMD)
- Participação de Veículos Pesados (%)
- Participação no Desgaste (%)

Esses indicadores fornecem uma visão executiva imediata, permitindo compreender rapidamente a escala da operação e os principais fatores de impacto.

### Evolução do Tráfego ao Longo do Tempo

Foi utilizado um gráfico de linha para representar o VMD ao longo do tempo.

Esse visual permite identificar:
- tendências de crescimento ou redução
- variações sazonais
- possíveis anomalias operacionais

A escolha do gráfico de linha se justifica pela necessidade de acompanhar o comportamento temporal de forma contínua.

### Volume vs Desgaste por Tipo de Veículo

Foi utilizado um gráfico de barras comparando:
- Volume Total de Tráfego
- Desgaste Total

segmentado por tipo de veículo (leve vs pesado).

Esse visual evidencia de forma clara o desbalanceamento entre volume e impacto, destacando que veículos pesados concentram o desgaste da rodovia.

### Distribuição por Tipo de Cobrança

Foi utilizado um gráfico de rosca (donut) para representar a participação dos diferentes tipos de cobrança:
- Automática
- Manual
- OCR

Esse tipo de visual facilita a leitura da proporção entre categorias, permitindo identificar rapidamente oportunidades de otimização operacional.

### Identificação de Gargalos Operacionais

Para análise de gargalos, foram utilizados:

**Gráfico de barras (ranking)**

Exibe o índice de gargalo por praça, permitindo identificar rapidamente quais concentram maior fluxo.

**Tabela complementar**

Apresenta a participação percentual de cada praça no fluxo total, oferecendo maior precisão na análise.

Essa combinação permite identificar:
- concentração de tráfego
- possíveis pontos de sobrecarga
- desequilíbrios na distribuição operacional

### Organização do Dashboard

O dashboard foi estruturado em uma única página com organização hierárquica:

1. Topo: KPIs principais (visão executiva)
2. Centro: Análise temporal e estrutural do tráfego
3. Base: Distribuição operacional e identificação de gargalos


## Insights
A análise dos dados de tráfego da concessionária evidencia padrões relevantes tanto do ponto de vista operacional quanto de infraestrutura.

Analisando a concessionária [CRO em 2024](https://github.com/elisamanuelle/antt_analise_trafego/blob/main/trafego_cro_2024.pdf):

<img width="1474" height="828" alt="image" src="https://github.com/user-attachments/assets/33a26a9e-be22-45b4-8e6a-04605ddcdbb1" />

**1. Concentração de desgaste em veículos pesados**

Embora os veículos pesados representem aproximadamente metade do volume total de tráfego, eles são responsáveis por praticamente 100% do desgaste do pavimento.

Isso indica que o principal fator de deterioração da rodovia não está no volume total de veículos, mas na composição do tráfego, com forte impacto dos veículos comerciais.

**2. Variação temporal e indícios de sazonalidade**

O volume médio diário (VMD) apresenta um comportamento relativamente estável ao longo do tempo, porém com uma elevação significativa a partir do meio do ano, seguida de uma redução posterior.

Esse padrão sugere influência de fatores externos, como ciclos econômicos ou períodos sazonais (ex.: escoamento de produção), indicando a necessidade de planejamento operacional adaptativo.

**3. Concentração de fluxo e potenciais gargalos**

A distribuição do tráfego entre as praças não é homogênea. Observa-se uma alta concentração de fluxo em poucas praças, com destaque para a praça P2, que apresenta um índice de gargalo significativamente superior às demais.

Esse comportamento indica possíveis pontos de sobrecarga operacional, com impacto potencial em filas, tempo de atendimento e experiência do usuário.

**4. Desbalanceamento na utilização da infraestrutura**

Enquanto algumas praças concentram grande parte do fluxo, outras apresentam participação muito reduzida.

Esse cenário sugere um desbalanceamento na utilização da infraestrutura, indicando oportunidades para revisão de capacidade, redistribuição operacional ou reavaliação do posicionamento estratégico das praças.

**5. Oportunidades na otimização dos meios de cobrança**

Apesar da predominância do pagamento automático, ainda existe uma participação relevante de cobrança manual (~40%).

Esse dado indica potencial de melhoria operacional por meio do incentivo a meios automáticos, o que pode contribuir para:

- Redução de filas
- Aumento da fluidez do tráfego
- Maior eficiência operacional

**6. Pressão localizada sobre a infraestrutura**

A combinação entre alta presença de veículos pesados e concentração de fluxo em determinadas praças sugere que o desgaste do pavimento ocorre de forma não uniforme, podendo gerar necessidade de manutenção mais frequente em pontos específicos da rodovia.

### Conclusão Executiva

Os dados indicam que a operação da rodovia é fortemente influenciada pela presença de veículos pesados e pela concentração de fluxo em determinadas praças. Esses fatores impactam diretamente tanto a eficiência operacional quanto a durabilidade da infraestrutura.
