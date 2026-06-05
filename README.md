# Projeto Educacional de Ingestão de Dados da Câmara dos Deputados Federais

Este projeto é uma base educativa em Python para aprender uma forma de extrair dados de uma API, gerar arquivos CSV e carregar esses dados em um banco PostgreSQL, com exemplos práticos e fáceis de entender.


## Estrutura do projeto

- `src/ingestao/`
  - `consome_api_camara.py` - script que consome a API de deputados da Câmara e gera arquivos CSV em `datasets/`.
  - `ingestao.py` - script que carrega os CSVs de `datasets/` para o banco de dados PostgreSQL.
- `datasets/` - pasta de destino dos arquivos CSV gerados pelo script de extração.
- `docker-compose.yml` - definição de contêineres para PostgreSQL e pgAdmin.
- `.env` - arquivo de variáveis de ambiente com credenciais do banco. Deve ficar fora do Git.
- `.venv/` - ambiente virtual local Python. Não deve ser enviado ao Git.

## Objetivo

Este repositório serve para:

1. Aprender a trabalhar com APIs em Python.
2. Entender como gerar e organizar arquivos CSV.
3. Praticar pipeline de ingestão de dados com PostgreSQL.


## Dependências principais

Os principais pacotes Python usados neste projeto são:

- `requests`
- `pandas`
- `sqlalchemy`
- `psycopg2-binary`

## Configuração inicial

### Passo 1: Criar o arquivo `.env`

**ANTES de qualquer coisa**, você precisa criar um arquivo `.env` na raiz do projeto com as credenciais do PostgreSQL:
Depois, edite o `.env` e altere as credenciais para valores seguros:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_segura_aqui
POSTGRES_DB=estudos
```

### Passo 2: Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Passo 3: Instalar dependências com `requirements.txt`

Este projeto já possui um arquivo `requirements.txt` que lista todas as bibliotecas necessárias com suas versões exatas.

```powershell
pip install -r requirements.txt
```

#### O que é `requirements.txt`?

O `requirements.txt` é um arquivo de texto simples que lista todas as dependências Python do projeto, com suas versões específicas. Ele serve para:

- **Facilitar a instalação**: Em vez de instalar cada pacote manualmente, você instala todos com um comando.
- **Garantir compatibilidade**: Especificar versões exatas garante que o código funcione igual em qualquer computador.
- **Compartilhar o projeto**: Quando alguém clona seu repositório do GitHub, pode instalar as mesmas dependências com um comando.
- **Documentar**: É uma forma clara de documentar quais bibliotecas o projeto precisa.

#### Como funciona?

- **Criação Dinâmica:** O script lê os metadados dos CSVs e gera automaticamente os Schemas (`raw`, `trusted`) no PostgreSQL.
- **Data Typing:** Conversão automática de tipos de dados via Pandas/SQLAlchemy para garantir a integridade numérica.
- **Pipeline:** O fluxo garante que a estrutura do banco esteja pronta antes da inserção, ideal para ambientes de CI/CD.

---


Cada linha do `requirements.txt` contém:

```text
nome_do_pacote==versão
```

Por exemplo:

```text
pandas>=2.2.0           # ferramenta para trabalhar com dados (tabelas)
requests>=2.32.0        # ferramenta para fazer requisições HTTP (chamar APIs)
sqlalchemy>=2.0.23      # ferramenta para trabalhar com bancos de dados
psycopg2-binary>=2.9.9  # ferramenta para conectar em PostgreSQL
```

> 📌 **Nota**: As versões usam `>=` (igual ou maior), permitindo atualizações de bug fixes automaticamente enquanto mantém compatibilidade.

Se preferir instalar manualmente (sem `requirements.txt`):

```powershell
pip install pandas requests sqlalchemy psycopg2-binary
```

Mas não recomendo! O `requirements.txt` garante que todos usem as mesmas versões.

### Passo 4: Iniciar os serviços do Docker

Se você usar Docker (recomendado para ter PostgreSQL rodando localmente):

```powershell
docker compose up -d
```

Para parar os serviços:

```powershell
docker compose down
```

### Passo 5: Verificar a conexão

Após iniciar o Docker, aguarde alguns segundos para o PostgreSQL estar pronto. Você pode verificar o status com:

```powershell
docker compose ps
```

### 6. Extrair dados da API

Execute o script que consome a API da Câmara:

```powershell
python src/ingestao/consome_api_camara.py
```

Isso gera três arquivos CSV diretamente em `datasets/`:

- `datasets/deputados.csv`
- `datasets/deputados_detalhes.csv`
- `datasets/deputados_despesas.csv`

### 2. Carregar os dados no PostgreSQL

Depois de gerar os CSVs, execute:

```powershell
python src/ingestao/ingestao.py
```

Esse script lê os arquivos em `datasets/` e grava os dados em três camadas no banco:

- `*_raw` - dados brutos
- `*_trusted` - dados tratados
- `*_analytics` - dados com limpeza básica

## Explicação dos scripts

### `src/ingestao/consome_api_camara.py`

- Busca os deputados da legislatura atual.
- Salva a lista de deputados em `datasets/deputados.csv`.
- Busca detalhes adicionais de cada deputado e salva em `datasets/deputados_detalhes.csv`.
- Busca despesas por deputado e salva em `datasets/deputados_despesas.csv`.

### `src/ingestao/ingestao.py`

- Lê os arquivos CSV da pasta `datasets/`.
- Converte nomes de colunas para padrão limpo.
- Cria schemas PostgreSQL se não existirem.
- Insere dados em tabelas separadas para raw, trusted e analytics.

## 📊 Insights do Portfólio (SQL)

Para validar o sucesso da ingestão, incluí uma camada de análises que podem ser encontradas na pasta [`/sql`](./sql/). 

**Destaque:** Analiso a média de gastos por parlamentar, total de gastos por partido e o cruzamento de gastos por nível de escolaridade, demonstrando o uso de:
- **Joins** entre tabelas biográficas e financeiras.
- **Casts de Tipo** para precisão monetária.
- **Agregações** para extração de métricas de performance parlamentar.
- **CTE:** Para organização de consultas e melhor legibilidade do código.
- **Tipagem Dinâmica:** Uso de Casts para precisão em cálculos financeiros.


## Boas práticas de Git

Este projeto inclui um `.gitignore` para evitar envio de arquivos que não devem ficar no repositório:

- ambientes virtuais (`.venv/`)
- arquivos de configuração locais (`.env`, `.vscode/`)
- caches Python (`__pycache__/`)
- arquivos gerados (`datasets/*.csv`)

## 🔐 Boas Práticas de Segurança

**Checklist antes de fazer commit:**

- [x] Arquivo `.env` existe e não será commitado (está em `.gitignore`)
- [x] Nenhuma senha ou chave de API está visível no código Python
- [x] Os arquivos `ingestao.py` e `connection.py` usam variáveis de ambiente (não hardcoded)
- [x] O `docker-compose.yml` não expõe credenciais sensíveis (usar `.env`)
- [x] Nenhum arquivo CSV com dados pessoais será commitado

## Notas finais
- O projeto foi pensado para aprendizado, então os comentários e nomes foram mantidos simples.
- O README usa caminhos relativos e não depende do nome da pasta raiz.
- O arquivo `requirements.txt` garante que todos os usuários tenham as mesmas versões dos pacotes Python.
- Sempre use um ambiente virtual (`.venv/`) para manter o projeto isolado do seu sistema Python global.

---