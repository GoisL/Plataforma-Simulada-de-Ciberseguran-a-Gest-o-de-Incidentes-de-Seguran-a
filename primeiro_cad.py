import sqlite3
import hashlib
from email.mime.text import MIMEText
import extras

def cadastro():
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    print("\n=== CADASTRO DE USUÁRIO ===")
    while True:
        nome = input("📝 Digite seu nome e último sobrenome: ").strip()
        email_pessoal = input("Agora digite um email pessoal para recuperação de senhas: ")
        perfil = ""
        while perfil not in ("analista", "supervisor"):
            perfil = input("Digite 1 para analista e 2 para supervisor: ").strip()
            if perfil == '1':
                perfil = 'analista'
                break
            elif perfil == '2':
                perfil = 'supervisor'
                break
            else:
                print("⚠️ Opção inválida. Digite apenas '1' ou '2'.")

        print(f"As informações estão corretas? \n Nome: {nome} \n Email pessoal: {email_pessoal} \n Perfil 1 para analista e 2 para supervisor: {perfil}")
        confirma = ""
        while confirma not in ("S", "N"):
            confirma = input("S/N:") .upper()
        if confirma == "S":
            break
    senha = extras.gerar_senha_temporaria()
    senha_hashed = extras.hash_senha(senha)
    email = extras.gerar_email_unico(nome, cursor)

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, perfil, email_pessoal, ativo, precisa_trocar_senha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, email, senha_hashed, perfil, email_pessoal, 1, 1))
        conn.commit()
        #registrar_log(conn, id_usuario_logado, 'criar', 'usuario', id_novo)
        print("✅ Perfil cadastrado com sucesso!")
    except sqlite3.IntegrityError as e:
        print(f"⚠️ Erro de integridade: {e}")
    except sqlite3.Error as e:
        print(f"⚠️ Erro no SQLite: {e}")
    finally:
        conn.close()


cadastro()           