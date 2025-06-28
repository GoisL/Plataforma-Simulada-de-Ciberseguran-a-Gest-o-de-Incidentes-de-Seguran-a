import sqlite3
import hashlib
import re
import getpass
import random
import string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import unicodedata
import extras

def menu_usuario(usuario):
    import supervisor
    import analista
    import extras

    user_id = usuario[0]

    extras.registrar_log_atividade(user_id,'Login no sistema','login')

    if usuario[2] == "supervisor":
        supervisor.menu_supervisor(usuario[0])
    elif usuario[2] == "analista":
        analista.menu_analista(usuario[0])
    else:
        print("❌ Perfil inválido. Acesso negado.")  

#LOGIN
def login():
    email = input("Email: ").strip()
    senha = getpass.getpass("Senha: ").strip()
    """Função de login com controle por e-mail e limite de tentativas."""
    if not email or not senha:
        print("❌ Email e senha são obrigatórios.")
        return None 

    if not extras.email_valido(email):
        print("❌ E-mail inválido.")
        return None

    try:
        conn = extras.conectar_banco()
        cursor = conn.cursor()

        
        cursor.execute("""
            SELECT user_id, nome, perfil, ativo, precisa_trocar_senha, tentativas FROM usuarios
            WHERE email = ?
        """, (email,))
        usuario = cursor.fetchone()

        if not usuario:
            print("❌ Usuário não encontrado.")
            return None

        user_id, nome, perfil, ativo, precisa_trocar_senha, tentativas = usuario

        if ativo == 0:
            print("❌ Conta bloqueada. Contate o administrador.")
            return None
        
        
        if tentativas >= 3:
            print("❌ Sua conta foi bloqueada após múltiplas tentativas falhas.")
            return None

        
        senha_hashed = extras.hash_senha(senha)
        cursor.execute("""
            SELECT user_id FROM usuarios WHERE email = ? AND senha = ?
        """, (email, senha_hashed))
        usuario_valido = cursor.fetchone()

        if usuario_valido:
            
            cursor.execute("UPDATE usuarios SET tentativas = 0 WHERE email = ?", (email,))
            conn.commit()

            if precisa_trocar_senha == 1:
                extras.senha_definitiva(email)

            print(f"✅ Bem-vindo, {nome} ({perfil})")
            menu_usuario(usuario)
            

            return {"user_id": user_id, "nome": nome, "perfil": perfil}
        else:
            
            tentativas += 1
            cursor.execute("UPDATE usuarios SET tentativas = ? WHERE email = ?", (tentativas, email))
            conn.commit()

            if tentativas >= 3:
                cursor.execute("UPDATE usuarios SET ativo = 0 WHERE email = ?", (email,))
                conn.commit()
                print("❌ Sua conta foi bloqueada após múltiplas tentativas falhas.")
                return None

            print(f"❌ Credenciais inválidas. Tentativas restantes: {3 - tentativas}")

            
            opcao = input("Deseja redefinir sua senha? (S/N): ").strip().upper()
            if opcao == 'S':
                email_pessoal = input("Digite seu e-mail pessoal registrado: ").strip()
                extras.redefinir_senha(email_pessoal)
                return None

    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")
        return None
    finally:
        conn.close()


 

print("🔐 LOGIN DO SISTEMA")

usuario = login()

if usuario:
        
    menu_usuario(usuario)


