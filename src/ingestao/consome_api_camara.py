import requests
import pandas as pd
import time
from pathlib import Path

# base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def fetch_json(url):
    """
    Função utilizada para buscar JSON de uma URL com tratamento de erros.
    """
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        content_type = r.headers.get('content-type', '')
        if 'application/json' not in content_type:
            return None
        return r.json()
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return None


def load_deputados_from_api():
    """
    1) Lista todos os deputados da legislatura atual.
    """
    print('1) Carregando listagem geral de deputados...')
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    data = fetch_json(url)
    if not data:
        return pd.DataFrame()
        
    rows = []
    for deputy in data.get('dados', []):
        rows.append({
            'id': deputy.get('id'),
            'nome': deputy.get('nome'),
            'sigla_partido': deputy.get('siglaPartido'),
            'sigla_uf': deputy.get('siglaUf'),
            'uri': deputy.get('uri'),
        })
    df = pd.DataFrame(rows)
    df.to_csv(BASE_DIR / "datasets" / "deputados.csv", index=False)
    print(f'   -> {len(df)} deputados carregados e salvos em datasets/deputados.csv')
    return df


def load_detalhes_deputados(df_deputados):
    """
    2) Busca detalhes específicos de cada deputado.
    """
    print('2) Carregando detalhes específicos de cada deputado...')
    detalhes_rows = []
    
    total = len(df_deputados)
    for index, row in df_deputados.iterrows():
        dep_id = row['id']
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{dep_id}"
        data = fetch_json(url)
        
        if data and 'dados' in data:
            d = data['dados']
            detalhes_rows.append({
                'id': d.get('id'),
                'nome_civil': d.get('nomeCivil'),
                'cpf': d.get('cpf'),
                'sexo': d.get('sexo'),
                'data_nascimento': d.get('dataNascimento'),
                'uf_nascimento': d.get('ufNascimento'),
                'municipio_nascimento': d.get('municipioNascimento'),
                'escolaridade': d.get('escolaridade'),
                'email_gabinete': d.get('ultimoStatus', {}).get('gabinete', {}).get('email'),
                'telefone_gabinete': d.get('ultimoStatus', {}).get('gabinete', {}).get('telefone')
            })
        
        if (index + 1) % 50 == 0:
            print(f"   -> Processados {index + 1} de {total} detalhes...")
            
    df_detalhes = pd.DataFrame(detalhes_rows)
    df_detalhes.to_csv(BASE_DIR / "datasets" / "deputados_detalhes.csv", index=False)
    print(f'   -> Detalhes salvos em datasets/deputados_detalhes.csv')
    return df_detalhes


def load_despesas_deputados(df_deputados, max_deputados=None):
    """
    3) Busca as despesas de cada deputado.
    Nota: A API de despesas é paginada. Para este exemplo, pegaremos a primeira página de cada um.
    """
    print('3) Carregando despesas de cada deputado...')
    despesas_rows = []
    
    total = len(df_deputados)
    if max_deputados:
        total = min(total, max_deputados)
        df_to_process = df_deputados.head(max_deputados)
    else:
        df_to_process = df_deputados

    for index, row in df_to_process.iterrows():
        dep_id = row['id']
        dep_nome = row['nome']
    
        url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{dep_id}/despesas?ordem=ASC&ordenarPor=ano"
        data = fetch_json(url)
        
        if data and 'dados' in data:
            for desp in data['dados']:
                despesas_rows.append({
                    'deputado_id': dep_id,
                    'deputado_nome': dep_nome,
                    'ano': desp.get('ano'),
                    'mes': desp.get('mes'),
                    'tipo_despesa': desp.get('tipoDespesa'),
                    'fornecedor': desp.get('nomeFornecedor'),
                    'cnpj_cpf_fornecedor': desp.get('cnpjCpfFornecedor'),
                    'valor_documento': desp.get('valorDocumento'),
                    'valor_liquido': desp.get('valorLiquido'),
                    'data_documento': desp.get('dataDocumento'),
                    'url_documento': desp.get('urlDocumento')
                })
        # Este if faz com que a cada 20 deputados processados, seja exibida uma mensagem de progresso no console, indicando quantos deputados já tiveram suas despesas processadas em relação ao total. Isso é útil para acompanhar o andamento do processo, especialmente quando se está lidando com um grande número de deputados.
        if (index + 1) % 20 == 0:
            print(f"   -> Processando despesas do deputado {index + 1} de {total}...")

    df_despesas = pd.DataFrame(despesas_rows)
    df_despesas.to_csv(BASE_DIR / "datasets" / "deputados_despesas.csv", index=False)
    print(f'   -> Despesas salvas em datasets/deputados_despesas.csv')
    return df_despesas


if __name__ == '__main__':
    start_time = time.time()
    try:
        print('=== Iniciando Extração de Dados da API da Câmara ===')
        
        # Rota 1: Listagem
        df_lista = load_deputados_from_api()
        
        if not df_lista.empty:
            # Rota 2: Detalhes (todos)
            load_detalhes_deputados(df_lista)
            
            # Rota 3: Despesas (todos)
            load_despesas_deputados(df_lista)
            
        end_time = time.time()
        print(f'\n=== Processo concluído com sucesso em {end_time - start_time:.2f} segundos! ===')
        
    except Exception as exc:
        print(f'\nErro durante a execução: {exc}')
