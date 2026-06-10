# GS 2026.1 - Space Climate AI

## Integrantes

- Bruno Nogueira Burian

## Tema do Projeto

Monitoramento climatico inteligente com dados orbitais simulados para previsao de risco de seca.

## Proposta

Esta POC responde ao desafio da Global Solution ao demonstrar como Inteligencia Artificial e tecnologias digitais podem gerar impacto positivo na Terra a partir de um contexto inspirado na economia espacial.

A solucao simula o uso de dados de satelite para monitorar variaveis ambientais de diferentes regioes, como temperatura da superficie, indice de vegetacao, chuva acumulada, umidade do solo, cobertura de nuvens e evapotranspiracao. A partir desses dados, um modelo de Machine Learning estima o risco de seca de cada regiao.

O projeto foi pensado para ser simples de executar, facil de explicar em video e forte do ponto de vista academico, cobrindo conceitos de IA, analise de dados, pipeline de dados e integracao por API.

## Problema Resolvido

Eventos climaticos extremos afetam agricultura, abastecimento e planejamento ambiental. O monitoramento baseado em dados espaciais ajuda a identificar sinais de risco com antecedencia, permitindo respostas mais rapidas e melhores decisoes.

Nesta POC, o foco esta em prever risco de seca com base em indicadores inspirados em sensoriamento remoto.

## Objetivos

- Simular um fluxo de dados climaticos inspirado em observacao orbital.
- Aplicar Machine Learning para classificar risco de seca.
- Disponibilizar a previsao por meio de uma API local.
- Organizar o projeto de forma reprodutivel e facil de demonstrar.

## Tecnologias Utilizadas

- Python 3
- CSV e JSON para persistencia de dados
- Servidor HTTP nativo com `http.server`
- Modelo de regressao logistica implementado do zero
- Estrutura modular em Python para pipeline, treino e inferencia

## Estrutura do Projeto

```text
gs_space_climate_poc/
|-- artifacts/
|   |-- drought_model.json
|   `-- metrics.json
|-- data/
|   `-- satellite_climate_data.csv
|-- src/
|   `-- space_climate_ai/
|       |-- __init__.py
|       |-- api.py
|       |-- data.py
|       |-- predict.py
|       `-- train.py
|-- example_payload.json
|-- PDF_ENTREGA.md
|-- README.md
|-- requirements.txt
|-- run_api.py
`-- run_pipeline.py
```

## Fluxo da Solucao

```mermaid
flowchart LR
    A[Dados climaticos simulados] --> B[Pipeline de geracao CSV]
    B --> C[Treinamento do modelo]
    C --> D[Modelo salvo em JSON]
    D --> E[API local de predicao]
    E --> F[Classificacao de risco de seca]
```

## Como Funciona

### 1. Geracao dos dados

O script principal gera um dataset sintetico com 24 regioes e 365 dias de observacao por regiao. Cada registro contem:

- `surface_temp_c`
- `ndvi`
- `rainfall_mm_7d`
- `soil_moisture_pct`
- `cloud_cover_pct`
- `evapotranspiration_mm`
- `drought_risk`

Esses dados sao salvos em `data/satellite_climate_data.csv`.

### 2. Treinamento do modelo

O pipeline treina um classificador de regressao logistica implementado manualmente, sem dependencias externas pesadas. O objetivo e prever se a regiao apresenta risco alto ou baixo de seca.

O modelo treinado e salvo em `artifacts/drought_model.json`.

### 3. Exposicao da previsao em API

Depois do treinamento, a API local recebe um JSON com os indicadores climaticos e retorna:

- `risk_probability`
- `risk_label`
- `risk_text`

## Resultados Obtidos

Metricas atuais do modelo:

- Accuracy: 0.9648
- F1-score: 0.9806
- ROC AUC: 0.99
- Registros de treino: 6570
- Registros de teste: 2190

Esses resultados mostram que a POC conseguiu aprender bem o padrao sintetico de risco de seca construido no pipeline.

## Como Executar

### 1. Rodar o pipeline

```bash
python run_pipeline.py
```

Esse comando:

- gera o dataset CSV
- treina o modelo
- salva metricas e artefatos

### 2. Iniciar a API

```bash
python run_api.py
```

Servidor local:

- Dashboard web: `http://127.0.0.1:8000/`
- `GET /health`
- `POST /predict`

### 3. Exemplo de requisicao

Payload base:

```json
{
  "surface_temp_c": 33.4,
  "ndvi": 0.21,
  "rainfall_mm_7d": 3.2,
  "soil_moisture_pct": 22.0,
  "cloud_cover_pct": 18.0,
  "evapotranspiration_mm": 11.5
}
```

Exemplo em PowerShell:

```powershell
$payload = Get-Content .\example_payload.json -Raw
Invoke-RestMethod -Uri "http://127.0.0.1:8000/predict" -Method Post -ContentType "application/json" -Body $payload
```

## Exemplo de Resposta

```json
{
  "risk_probability": 0.997,
  "risk_label": 1,
  "risk_text": "high"
}
```

## Relacao com a Global Solution

O projeto atende ao desafio proposto porque integra:

- Inteligencia Artificial aplicada
- analise de dados climaticos
- pipeline reprodutivel
- servico de predicao via API
- contexto inspirado em dados espaciais e sensoriamento remoto

Mesmo sendo uma POC enxuta, a solucao demonstra com clareza como tecnologias digitais podem transformar dados ambientais em apoio a decisao com impacto direto na Terra.

## Link do Repositorio

- Preencher link do repositorio GitHub

## Link do Video

- Preencher link do video no YouTube como nao listado

## Observacoes Finais

- Este projeto nao utiliza bibliotecas externas pesadas para manter compatibilidade com o ambiente local.
- O README deve ser atualizado com os nomes finais dos integrantes antes da entrega.
- O arquivo `PDF_ENTREGA.md` pode ser usado como base para montar o documento final em PDF.
