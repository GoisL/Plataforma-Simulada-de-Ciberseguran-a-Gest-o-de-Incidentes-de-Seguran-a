import sqlite3
from datetime import datetime
# Define uma função chamada criar_banco, que será responsável por criar as tabelas no banco
def criar_banco():
    # Conecta (ou cria) o banco de dados chamado 'sistema_incidentes.db'
    conn = sqlite3.connect('sistema_incidentes.db')
    cursor = conn.cursor()
    # Tabela de usuários com melhorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(80) NOT NULL,
            email VARCHAR(30) UNIQUE NOT NULL,
            senha VARCHAR(254) NOT NULL,
            precisa_trocar_senha INTEGER DEFAULT 1,
            perfil VARCHAR(15) CHECK(perfil IN ('analista', 'supervisor')) NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_login DATETIME,
            email_pessoal VARCHAR(30) UNIQUE,
            tentativas INTEGER DEFAULT 0,
            cod_verif VARCHAR(6) 
			
        );
    """)
    # Tabela de incidentes com melhorias
    cursor.execute("""
                   
        CREATE TABLE IF NOT EXISTS incidentes (
            id_incidente INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT CHECK(prioridade IN ('baixa', 'média', 'alta')) NOT NULL,
            status TEXT CHECK(status IN ('pendente', 'em análise', 'resolvido')) NOT NULL DEFAULT 'pendente',
            data_criacao TEXT NOT NULL,
            id_analista INTEGER NOT NULL,
            atualizado_por INTEGER,
            FOREIGN KEY(id_analista) REFERENCES usuarios(user_id),
            FOREIGN KEY(atualizado_por) REFERENCES usuarios(user_id)
        );
    """)
    # Tabela de logs com melhorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_atividades (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora DATETIME NOT NULL,
            id_usuario INTEGER NOT NULL,
            acao VARCHAR(100) NOT NULL,
            tipo_recurso VARCHAR(50),
            id_recurso INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuarios(id)
        );
    """)
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso.")
if __name__ == "__main__":
    criar_banco()

