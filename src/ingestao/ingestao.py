import pandas as pd
from sqlalchemy import text
from pathlib import Path

# Import relativo para evitar problemas de módulo quando executado como script
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db.connection import get_engine

engine = get_engine()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def criar_schema(schema_name):
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))


def carregar_e_processar(nome_arquivo, dominio, nome_tabela):
    csv_path = BASE_DIR / "datasets" / nome_arquivo

    print(f"\n📂 Processando: {nome_arquivo}")

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


    criar_schema(f"{dominio}_raw")
    criar_schema(f"{dominio}_trusted")
    criar_schema(f"{dominio}_analytics")

    # =========================
    # 1. RAW (dados brutos)
    # =========================
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
    df_tratado = df.copy()

    df_tratado.columns = (
        df_tratado.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
    )

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

    df_analise = df_analise.dropna(how="all")
    
    df_analise.to_sql(
        f"{nome_tabela}_analytics",
        engine,
        schema=f"{dominio}_analytics",
        if_exists="replace",
        index=False
    )
    print(f"✔ ANALYTICS: {dominio}_analytics.{nome_tabela}_analytics")


# LISTA DE DATASETS
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

for nome_arquivo, dominio, nome_tabela in datasets:
    carregar_e_processar(nome_arquivo, dominio, nome_tabela)

print("\n🚀 Pipeline finalizado com sucesso!")