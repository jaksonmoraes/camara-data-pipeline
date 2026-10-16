import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "datasets"

API_BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# A legislatura 57 corresponde ao período de 2022 a 2026.
LEGISLATURA = 57

# Quantidade máxima permitida por página pela API.
ITENS_POR_PAGINA = 100

# Timeout de cada requisição.
REQUEST_TIMEOUT = 30

# Pausa pequena e conservadora entre requisições.
# O retry com backoff assume a espera maior quando a API sinaliza erro temporário.
REQUEST_DELAY = 0.05

# Número máximo de tentativas em caso de erro temporário.
MAX_RETRIES = 3

# Concorrência controlada para as consultas de despesas.
# Mantido baixo para reduzir o risco de rate limit na API pública.
MAX_WORKERS = 5


DATASETS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SESSION HTTP
# ============================================================

_thread_local = threading.local()


def create_session():
    """Cria uma sessão HTTP reutilizável com retry automático."""
    session = requests.Session()

    retry_strategy = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "Projeto-Dados-Camara/1.0",
    })

    return session


def get_session():
    """Retorna uma sessão exclusiva para a thread atual."""
    session = getattr(_thread_local, "session", None)

    if session is None:
        session = create_session()
        _thread_local.session = session

    return session


# Mantém o nome disponível para eventual código externo que importe o módulo.
# As requisições usam get_session(), evitando compartilhar Session entre threads.
SESSION = get_session()


# ============================================================
# FUNÇÃO BÁSICA DE REQUISIÇÃO
# ============================================================


def fetch_json(url, params=None):
    """Busca JSON de uma URL com tratamento de erros.

    Retorna um dicionário quando a requisição é bem-sucedida e None quando
    ocorre uma falha. A pausa é aplicada por thread, enquanto erros temporários
    são tratados pelo retry com backoff da sessão HTTP.
    """
    try:
        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

        response = get_session().get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        if "application/json" not in content_type:
            print("   [ERRO] Resposta não é JSON.")
            print(f"   URL: {response.url}")
            print(f"   Content-Type: {content_type}")
            return None

        return response.json()

    except requests.Timeout:
        print(f"   [ERRO] Timeout ao acessar:\n   {url}")
        return None

    except requests.HTTPError as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else "desconhecido"
        )
        print(f"   [ERRO HTTP {status_code}]\n   URL: {url}")
        return None

    except requests.ConnectionError:
        print(f"   [ERRO] Falha de conexão:\n   {url}")
        return None

    except requests.RequestException as error:
        print(
            f"   [ERRO REQUEST]"
            f"\n   URL: {url}"
            f"\n   Detalhes: {error}"
        )
        return None

    except ValueError:
        print(f"   [ERRO] JSON inválido:\n   {url}")
        return None


# ============================================================
# ESCRITA ATÔMICA DE CSV
# ============================================================


def save_dataframe_atomic(df, output_file):
    """Grava o DataFrame em arquivo temporário e faz substituição atômica."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            suffix=".tmp",
            prefix=f".{output_file.name}.",
            dir=output_file.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        df.to_csv(
            temporary_path,
            index=False,
            encoding="utf-8-sig",
        )

        os.replace(temporary_path, output_file)

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


# ============================================================
# PAGINAÇÃO GENÉRICA
# ============================================================


def fetch_all_pages(
    url,
    params=None,
    descricao="registros",
    return_status=False,
):
    """Busca todas as páginas de um endpoint paginado.

    Quando return_status=True, retorna (dados, consulta_completa). Isso evita
    tratar dados parciais como se fossem uma extração bem-sucedida.
    O padrão continua retornando somente a lista, preservando compatibilidade
    com chamadas existentes.
    """
    if params is None:
        params = {}

    request_params = params.copy()
    request_params["itens"] = ITENS_POR_PAGINA
    request_params["pagina"] = 1

    all_data = []
    consulta_completa = True

    while True:
        pagina_atual = request_params["pagina"]

        data = fetch_json(url, params=request_params)

        if data is None:
            print(f"   [ERRO] Falha ao carregar a página {pagina_atual}.")
            consulta_completa = False
            break

        page_data = data.get("dados", [])

        if not page_data:
            break

        all_data.extend(page_data)

        print(
            f"      Página {pagina_atual}: "
            f"{len(page_data)} {descricao}"
        )

        if len(page_data) < ITENS_POR_PAGINA:
            break

        request_params["pagina"] += 1

    if return_status:
        return all_data, consulta_completa

    return all_data


# ============================================================
# 1 - DEPUTADOS
# ============================================================


def load_deputados_from_api():
    """Lista todos os deputados da legislatura configurada."""
    print()
    print("=" * 70)
    print("1) CARREGANDO LISTAGEM DE DEPUTADOS")
    print("=" * 70)

    url = f"{API_BASE_URL}/deputados"
    params = {"idLegislatura": LEGISLATURA}

    data = fetch_all_pages(url, params=params, descricao="deputados")

    if not data:
        print("   [ERRO] Nenhum deputado foi carregado.")
        return pd.DataFrame()

    rows = []

    for deputy in data:
        # A API retorna cada item como objeto JSON/dicionário. A validação
        # explícita também informa isso ao Pylance/mypy antes dos .get().
        if not isinstance(deputy, dict):
            raise TypeError(
                "A API retornou um deputado em formato diferente de objeto."
            )

        rows.append({
            "id": deputy.get("id"),
            "nome": deputy.get("nome"),
            "sigla_partido": deputy.get("siglaPartido"),
            "sigla_uf": deputy.get("siglaUf"),
            "uri": deputy.get("uri"),
        })

    df = pd.DataFrame(rows)
    output_file = DATASETS_DIR / "deputados.csv"
    save_dataframe_atomic(df, output_file)

    print()
    print(f"   -> {len(df)} deputados carregados.")
    print(f"   -> Salvo em: {output_file}")

    return df


# ============================================================
# 2 - DETALHES DOS DEPUTADOS
# ============================================================


def load_detalhes_deputados(df_deputados):
    """Busca detalhes específicos de cada deputado."""
    print()
    print("=" * 70)
    print("2) CARREGANDO DETALHES DOS DEPUTADOS")
    print("=" * 70)

    detalhes_rows = []
    falhas = []
    total = len(df_deputados)

    for position, (_, row) in enumerate(df_deputados.iterrows(), start=1):
        dep_id = row["id"]

        print(f"   [{position}/{total}] Consultando deputado {dep_id}...")

        data = fetch_json(f"{API_BASE_URL}/deputados/{dep_id}")

        if data and "dados" in data:
            d = data["dados"]
            ultimo_status = d.get("ultimoStatus", {}) or {}
            gabinete = ultimo_status.get("gabinete", {}) or {}

            detalhes_rows.append({
                "id": d.get("id"),
                "nome_civil": d.get("nomeCivil"),
                "cpf": d.get("cpf"),
                "sexo": d.get("sexo"),
                "data_nascimento": d.get("dataNascimento"),
                "uf_nascimento": d.get("ufNascimento"),
                "municipio_nascimento": d.get("municipioNascimento"),
                "escolaridade": d.get("escolaridade"),
                "email_gabinete": gabinete.get("email"),
                "telefone_gabinete": gabinete.get("telefone"),
            })
        else:
            falhas.append({"id": dep_id, "nome": row["nome"]})
            print(
                f"      [AVISO] Falha ao carregar detalhes do deputado {dep_id}."
            )

    df_detalhes = pd.DataFrame(detalhes_rows)
    output_file = DATASETS_DIR / "deputados_detalhes.csv"
    save_dataframe_atomic(df_detalhes, output_file)

    print()
    print(f"   -> {len(df_detalhes)} detalhes carregados.")
    print(f"   -> Salvo em: {output_file}")

    if falhas:
        df_falhas = pd.DataFrame(falhas)
        falhas_file = DATASETS_DIR / "falhas_detalhes.csv"
        save_dataframe_atomic(df_falhas, falhas_file)

        print(f"   -> {len(falhas)} falhas registradas em:")
        print(f"      {falhas_file}")

    return df_detalhes


# ============================================================
# 3 - DESPESAS
# ============================================================

DESPESAS_COLUMNS = [
    "deputado_id",
    "deputado_nome",
    "ano",
    "mes",
    "tipo_despesa",
    "fornecedor",
    "cnpj_cpf_fornecedor",
    "valor_documento",
    "valor_liquido",
    "data_documento",
    "url_documento",
]


def fetch_despesas_deputado(dep_index, dep_id, dep_nome):
    """Worker de despesas; cada thread usa sua própria sessão HTTP."""
    url = f"{API_BASE_URL}/deputados/{dep_id}/despesas"
    params = {
        "ordem": "ASC",
        "ordenarPor": "ano",
        "idLegislatura": LEGISLATURA,
    }

    despesas, consulta_completa = fetch_all_pages(
        url,
        params=params,
        descricao=f"despesas do deputado {dep_id}",
        return_status=True,
    )

    return {
        "index": dep_index,
        "id": dep_id,
        "nome": dep_nome,
        "despesas": despesas,
        "consulta_completa": consulta_completa,
    }


def build_despesa_rows(result):
    """Converte o retorno de um deputado para as colunas do CSV final."""
    dep_id = result["id"]
    dep_nome = result["nome"]

    return [
        {
            "deputado_id": dep_id,
            "deputado_nome": dep_nome,
            "ano": desp.get("ano"),
            "mes": desp.get("mes"),
            "tipo_despesa": desp.get("tipoDespesa"),
            "fornecedor": desp.get("nomeFornecedor"),
            "cnpj_cpf_fornecedor": desp.get("cnpjCpfFornecedor"),
            "valor_documento": desp.get("valorDocumento"),
            "valor_liquido": desp.get("valorLiquido"),
            "data_documento": desp.get("dataDocumento"),
            "url_documento": desp.get("urlDocumento"),
        }
        for desp in result["despesas"]
    ]


def load_despesas_deputados(df_deputados, max_deputados=None):
    """Busca todas as despesas usando concorrência controlada.

    A consulta de cada deputado é independente. As páginas de um mesmo
    deputado continuam sendo consultadas sequencialmente para preservar a
    paginação e garantir a extração completa.
    """
    print()
    print("=" * 70)
    print("3) CARREGANDO DESPESAS DOS DEPUTADOS")
    print("=" * 70)
    print(f"   Workers simultâneos: {MAX_WORKERS}")

    if max_deputados is not None:
        df_to_process = df_deputados.head(max_deputados)
    else:
        df_to_process = df_deputados

    deputies = [
        (position, row["id"], row["nome"])
        for position, (_, row) in enumerate(df_to_process.iterrows(), start=1)
    ]
    total = len(deputies)

    # Sem a anotação, o analisador pode inferir list[None] e sinalizar erro
    # na atribuição posterior do dicionário retornado por cada future.
    resultados: list[dict | None] = [None] * total

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_despesas_deputado, *deputy): deputy[0]
            for deputy in deputies
        }

        for completed, future in enumerate(as_completed(futures), start=1):
            deputy_position = futures[future]

            try:
                result = future.result()
            except Exception as error:
                position, dep_id, dep_nome = deputies[deputy_position - 1]
                result = {
                    "index": position,
                    "id": dep_id,
                    "nome": dep_nome,
                    "despesas": [],
                    "consulta_completa": False,
                    "exception": error,
                }

            resultados[deputy_position - 1] = result

            quantidade = len(result["despesas"])
            status = "completa" if result["consulta_completa"] else "INCOMPLETA"
            print(
                f"   [{completed}/{total}] {result['nome']} "
                f"(ID: {result['id']}): {quantidade} despesas - {status}"
            )

    despesas_rows = []
    falhas = []

    # Ordenar pelo deputado original mantém um resultado determinístico,
    # mesmo com as requisições sendo executadas em paralelo.
    for result in resultados:
        if result is None:
            continue

        if not result["consulta_completa"]:
            falhas.append({
                "id": result["id"],
                "nome": result["nome"],
            })
            print(
                f"      [AVISO] Consulta incompleta para o deputado "
                f"{result['id']}; dados não gravados no CSV final."
            )
            continue

        # Lista vazia em uma consulta concluída é uma resposta legítima,
        # e não uma falha de comunicação.
        despesas_rows.extend(build_despesa_rows(result))

    df_despesas = pd.DataFrame(despesas_rows, columns=DESPESAS_COLUMNS)
    output_file = DATASETS_DIR / "deputados_despesas.csv"
    save_dataframe_atomic(df_despesas, output_file)

    print()
    print(f"   -> {len(df_despesas)} despesas carregadas.")
    print(f"   -> Salvo em: {output_file}")

    if falhas:
        df_falhas = pd.DataFrame(falhas)
        falhas_file = DATASETS_DIR / "falhas_despesas.csv"
        save_dataframe_atomic(df_falhas, falhas_file)

        print()
        print(f"   -> {len(falhas)} deputados apresentaram falhas.")
        print(f"   -> Falhas salvas em:")
        print(f"      {falhas_file}")

    return df_despesas


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================


if __name__ == "__main__":
    start_time = time.time()

    print()
    print("=" * 70)
    print("EXTRAÇÃO DE DADOS DA API DA CÂMARA DOS DEPUTADOS")
    print("=" * 70)
    print(f"API: {API_BASE_URL}")
    print(f"Legislatura: {LEGISLATURA}")
    print(f"Itens por página: {ITENS_POR_PAGINA}")
    print("=" * 70)

    try:
        df_lista = load_deputados_from_api()

        if df_lista.empty:
            print()
            print("[ERRO] A lista de deputados está vazia.")
            raise SystemExit(1)

        load_detalhes_deputados(df_lista)
        load_despesas_deputados(df_lista)

        elapsed = time.time() - start_time

        print()
        print("=" * 70)
        print("PROCESSO CONCLUÍDO")
        print("=" * 70)
        print(f"Tempo total: {elapsed:.2f} segundos")
        print("Arquivos gerados em:")
        print(DATASETS_DIR)
        print("=" * 70)

    except KeyboardInterrupt:
        print()
        print("[AVISO] Processo interrompido pelo usuário.")

    except Exception as exc:
        print()
        print("=" * 70)
        print("[ERRO FATAL]")
        print(str(exc))
        print("=" * 70)
