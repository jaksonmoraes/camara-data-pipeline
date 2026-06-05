import os
from sqlalchemy import create_engine

def get_engine():
    """
    Cria e retorna uma engine SQLAlchemy para PostgreSQL.
    
    Lê as credenciais de variáveis de ambiente (.env):
    - DATABASE_URL: URL completa de conexão (se fornecida, sobrescreve outros valores)
    - DB_HOST: Host do banco (padrão: localhost)
    - DB_PORT: Porta do banco (padrão: 5432)
    - DB_USER: Usuário (padrão: postgres)
    - DB_PASSWORD: Senha (padrão: 123)
    - DB_NAME: Nome do banco (padrão: estudos)
    
    Garante compatibilidade: se nenhuma variável estiver definida, usa valores padrão.
    """
    
    # Se DATABASE_URL está definida, usa ela diretamente
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return create_engine(database_url)
    
    # Caso contrário, monta a URL a partir de variáveis individuais
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '123')
    db_name = os.getenv('DB_NAME', 'estudos')
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return create_engine(database_url)