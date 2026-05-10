import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# conexão com banco
engine = create_engine("postgresql://postgres:123@localhost:5432/estudos")

# base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def criar_schema(schema_name):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))


def carregar_e_processar(nome_arquivo, dominio, nome_tabela):
    csv_path = BASE_DIR / "datasets" / nome_arquivo

    print(f"\n📂 Processando: {nome_arquivo}")

    # Tentar diferentes encodings e delimitadores
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    separators = [',', ';']
    df = None
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, sep=sep)
                print(f"   → Encoding: {encoding} | Delimitador: {sep}")
                break
            except (UnicodeDecodeError, LookupError, pd.errors.ParserError):
                continue
        if df is not None:
            break
    
    if df is None:
        raise ValueError(f"Não foi possível ler o arquivo {csv_path} com nenhuma combinação de encoding e delimitador")

    # certificar que schemas existem
    criar_schema(f"{dominio}_raw")
    criar_schema(f"{dominio}_trusted")
    criar_schema(f"{dominio}_analytics")

    # =========================
    # 1. RAW (dados brutos)
    # =========================
    # Aqui o df.to_sql() é para salvar o df original (raw) na camada raw do banco de dados, usando o nome da tabela e domínio definidos
    df.to_sql(
        f"{nome_tabela}_raw",
        engine,
        schema=f"{dominio}_raw",
        if_exists="replace",
        index=False
    )
    print(f"✔ RAW: {dominio}_raw.{nome_tabela}_raw")

    # =========================
    # 2. TRUSTED (tratado)
    # =========================
    # Aqui é feito uma limpeza básica: padronização de nomes de colunas (lowercase, sem espaços, etc)
    # O df.copy() é para evitar alterações no meu df original (raw) que pode ser necessário para outras transformações ou análises futuras
    df_tratado = df.copy()

    df_tratado.columns = (
        df_tratado.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
    )
    # Aqui o df.tratado.tosql() é para salvar o df tratado na camada trusted do banco de dados, usando o nome da tabela e domínio definidos
    df_tratado.to_sql(
        f"{nome_tabela}_trusted",
        engine,
        schema=f"{dominio}_trusted",
        if_exists="replace",
        index=False
    )
    print(f"✔ TRUSTED: {dominio}_trusted.{nome_tabela}_trusted")

    # =========================
    # 3. ANALYTICS (limpeza básica)
    # =========================
    df_analise = df_tratado.copy()

    # O dropna(how="all") é para remover linhas que estão completamente vazias, ou seja, todas as colunas têm valores nulos. Isso ajuda a limpar o dataset e evitar análises com dados irrelevantes ou incompletos.
    df_analise = df_analise.dropna(how="all")
    
    # Aqui o df_analise.tosql() é para salvar o df tratado e limpo na camada analytics do banco de dados, usando o nome da tabela e domínio definidos. O if_exists="replace" é para garantir que, se a tabela já existir, ela seja substituída pelos novos dados processados.
    df_analise.to_sql(
        f"{nome_tabela}_analytics",
        engine,
        schema=f"{dominio}_analytics",
        if_exists="replace",
        index=False
    )
    print(f"✔ ANALYTICS: {dominio}_analytics.{nome_tabela}_analytics")


# 🔥 LISTA DE DATASETS
datasets = [
    (
        "deputados.csv",
        "deputados",
        "deputados"
    ),
    (
        "deputados_detalhes.csv",
        "deputados",
        "deputados_detalhes"
    ),
    (
        "deputados_despesas.csv",
        "deputados",
        "deputados_despesas"
    )
]

# 🔁 LOOP DE EXECUÇÃO
for nome_arquivo, dominio, nome_tabela in datasets:
    carregar_e_processar(nome_arquivo, dominio, nome_tabela)

print("\n🚀 Pipeline finalizado com sucesso!")