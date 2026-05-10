import pandas as pd

# carregar o csv deputados_despesas.csv para verificar o tipo de dados de cada coluna
df = pd.read_csv("datasets/deputados_despesas.csv")

# usar o df.info() para verificar o tipo de dados de cada coluna e identificar quais colunas precisam ser convertidas para o tipo correto no csv deputados_despesas.csv
#  (por exemplo, datas, números, etc.). Isso ajudará a garantir que os dados sejam tratados corretamente nas etapas posteriores do processo de ingestão e análise.

checar = df.info()