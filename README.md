# Projeto Educacional de Ingestão de Dados da Câmara dos Deputados Federais

Este projeto é uma base educativa em Python para aprender como extrair dados de uma API, gerar arquivos CSV e carregar esses dados em um banco PostgreSQL. O foco é ensino de programação, dados e uso de Git, com exemplos práticos e fáceis de entender.


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
4. Usar Git corretamente, ignorando arquivos temporários e ambientes locais.

## Dependências principais

Os principais pacotes Python usados neste projeto são:

- `requests`
- `pandas`
- `sqlalchemy`
- `psycopg2-binary`

## Configuração inicial

### Passo 1: Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Passo 2: Instalar dependências com `requirements.txt`

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

Cada linha do `requirements.txt` contém:

```text
nome_do_pacote==versão
```

Por exemplo:

```text
pandas==2.0.3           # ferramenta para trabalhar com dados (tabelas)
requests==2.31.0        # ferramenta para fazer requisições HTTP (chamar APIs)
sqlalchemy==2.0.20      # ferramenta para trabalhar com bancos de dados
psycopg2-binary==2.9.7  # ferramenta para conectar em PostgreSQL
```

Se preferir instalar manualmente (sem `requirements.txt`):

```powershell
pip install pandas requests sqlalchemy psycopg2-binary
```

Mas não recomendamos! O `requirements.txt` garante que todos usem as mesmas versões.

### Passo 3: Iniciar os serviços do Docker

Se você usar Docker (recomendado para ter PostgreSQL rodando localmente):

```powershell
docker compose up -d
```

Para parar os serviços:

```powershell
docker compose down
```

### Passo 4: Verificar o arquivo `.env`

Este arquivo contém as credenciais do PostgreSQL:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123
POSTGRES_DB=estudos
```

> ⚠️ **Importante**: Mantenha o `.env` privado. Ele já está listado no `.gitignore` e não será enviado ao GitHub.

## Fluxo de execução

### 1. Extrair dados da API

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

## Boas práticas de Git

Este projeto inclui um `.gitignore` para evitar envio de arquivos que não devem ficar no repositório:

- ambientes virtuais (`.venv/`)
- arquivos de configuração locais (`.env`, `.vscode/`)
- caches Python (`__pycache__/`)
- arquivos gerados (`datasets/*.csv`)

## Como contribuir / estudar

**Primeiros passos quando clonar o repositório:**

1. Crie o ambiente virtual: `python -m venv .venv`
2. Ative-o: `.\.venv\Scripts\Activate.ps1`
3. Instale as dependências: `pip install -r requirements.txt`
4. Inicie o Docker: `docker compose up -d`

**Agora estude o código:**

- Comece com `src/ingestao/consome_api_camara.py` para entender como funciona a extração de dados de uma API.
- Em seguida, estude `src/ingestao/ingestao.py` para ver como os dados são carregados no banco de dados.
- Use `docker compose ps` para verificar se o PostgreSQL e o pgAdmin estão rodando.
- Experimente modificar os scripts e executar novamente para ver os resultados.

## Notas finais

- O projeto foi pensado para aprendizado, então os comentários e nomes foram mantidos simples.
- O README usa caminhos relativos e não depende do nome da pasta raiz.
- O arquivo `requirements.txt` garante que todos os usuários tenham as mesmas versões dos pacotes Python.
- Sempre use um ambiente virtual (`.venv/`) para manter o projeto isolado do seu sistema Python global.

---