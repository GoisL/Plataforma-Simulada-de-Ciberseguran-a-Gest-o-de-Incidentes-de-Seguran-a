import sqlite3 
from datetime import datetime, timedelta, timezone
import unicodedata
import random
import string
import extras
import tabelas


#FUNÇÕES PARA GERENCIAR USUARIOS


#a) Cadastrar analista
def cadastrar_analista(lead_id):
    nome = input("📝 Digite o nome completo do analista: ").strip()
    email_pessoal = input("📝Agora digite um email pessoal para recuperação de senhas: ").strip()
    senha = extras.gerar_senha_temporaria()

    while True:
        perfil = input("👤 Deseja cadastrar como Analista (A) ou Supervisor (S)? ").strip().lower()
        if perfil == 'a':
            perfil = 'analista'
            break
        elif perfil == 's':
            perfil = 'supervisor'
            break
        else:
            print("⚠️ Opção inválida. Digite apenas 'A' ou 'S'.")

    conn = extras.conectar_banco()
    cursor = conn.cursor()
    email = extras.gerar_email_unico(nome, cursor)

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, perfil, email_pessoal, ativo, precisa_trocar_senha)
            VALUES (?, ?, ?, ?,?, 1, 1)
        """, (nome, email, senha, perfil, email_pessoal))
        conn.commit()
        cursor.execute("SELECT last_insert_rowid()")
        id_novo = cursor.fetchone()[0]
        extras.registrar_log_atividade(lead_id, 'criar', 'usuario')
        print(f"\n✅ {perfil.capitalize()} cadastrado com sucesso!")
        print(f"📧 Email gerado: {email}")
        print(f"🔐 Senha temporária: {senha}")
        print("⚠️ O usuário deverá trocar a senha no primeiro acesso.")
    except sqlite3.IntegrityError:
        print(f"\n⚠️ Erro inesperado ao cadastrar.")
    finally:
        conn.close()


# b) Remover usuarios
def remover_usuario(lead_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    email = input("📧 Digite o email do usuario: ")

    cursor.execute("""
        SELECT user_id, nome, email, perfil
        FROM usuarios
        WHERE email = ? 
    """, (email,))
    usuario = cursor.fetchone()

    if usuario:
        print("\n🔍 Usuário encontrado:")
        print(f"ID: {usuario[0]}")
        print(f"Nome: {usuario[1]}")
        print(f"Email: {usuario[2]}")
        print(f"Perfil: {usuario[3]}")

        confirmacao = input("\n❓ Tem certeza que deseja remover esse usuário? (s/n): ").strip().lower()
        if confirmacao == 's':
            cursor.execute("DELETE FROM usuarios WHERE user_id = ?", (usuario[0],))
            conn.commit()
            extras.registrar_log_atividade(lead_id, 'remover', 'usuario')
            print("✅ Usuário removido com sucesso.")
        else:
            print("❌ Remoção cancelada.")
    else:
        print("⚠️ Nenhum analista ou supervisor encontrado com esse email.")

    conn.close()


# c) Promover analistas para supervisores
def promover_analista(lead_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    email = input("📧 Digite o email do analista: ")

    cursor.execute("""
        SELECT user_id, nome, email, perfil, ativo
        FROM usuarios
        WHERE email = ? AND perfil = 'analista'
    """, (email,))
    analista = cursor.fetchone()

    if analista:
        user_id, nome, email, perfil, ativo = analista

        print("\n📋 Informações do analista:")
        print(f"🆔 ID: {user_id}")
        print(f"👤 Nome: {nome}")
        print(f"📧 Email: {email}")
        print(f"🔐 Perfil atual: {perfil}")
        print(f"✅ Status: {'Ativo' if ativo else 'Bloqueado'}")

        confirmacao = input("\n❓ Deseja promover esse analista para supervisor? (s/n): ").strip().lower()
        if confirmacao == 's':
            cursor.execute("""
                UPDATE usuarios
                SET perfil = 'supervisor'
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            extras.registrar_log_atividade(lead_id, 'atualizar', 'usuario')
            print("✅ Analista promovido com sucesso!")
        else:
            print("❌ Promoção cancelada.")
    else:
        print("⚠️ Nenhum analista encontrado com esse email.")

    conn.close()


# d) Visualizar todos os analistas e supervisores
def listar_usuarios():
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    colunas = ['user_id', 'nome', 'email', 'perfil', 'ativo', 'ultimo_login']

    colunas_sql = ', '.join(colunas)
    cursor.execute(f"""
        SELECT {colunas_sql}
        FROM usuarios
        WHERE perfil IN ('analista', 'supervisor')
    """)
    usuarios = cursor.fetchall()
    conn.close()

    if not usuarios:
        print("⚠️ Nenhum usuário encontrado.")
        return

    larguras = [max(len(col), 15) for col in colunas]

    cabecalho = " | ".join(col.ljust(w) for col, w in zip(colunas, larguras))
    print("\n" + cabecalho)
    print("-" * len(cabecalho))

    for usuario in usuarios:
        linha = []
        for valor, w, col in zip(usuario, larguras, colunas):
            if col == 'ativo':
                valor = 'Ativo' if valor else 'Bloqueado'
            linha.append(str(valor).ljust(w))
        print(" | ".join(linha))


# e) Atualizar status de usuário (bloqueado → ativo)
def ativar_usuario(lead_id):
    email = input("📧 Digite o email do analista: ")

    conn = extras.conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE usuarios
        SET ativo = 1
        WHERE email = ? AND ativo = 0
    """, (email,))
    conn.commit()
    if cursor.rowcount > 0:
        cursor.execute("SELECT user_id FROM usuarios WHERE email = ?", (email,))
        id_usuario_alvo = cursor.fetchone()[0]
        extras.registrar_log_atividade(lead_id, 'ativar conta', 'usuario')
    print("✅ Usuário ativado (se estava bloqueado).")
    conn.close()





#FUNÇÕES DE VISUALIZAR E GERENCIAR INCIDENTES

#a)Atualizar status do incidente

def atualizar_status_incidente(lead_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    id_incidente = input("🆔 Digite o ID do incidente: ").strip()
    novo_status = input("🔄 Novo status (pendente, em análise, resolvido): ").strip().lower()

    if novo_status not in ['pendente', 'em análise', 'resolvido']:
        print("⚠️ Status inválido.")
        return

    cursor.execute("""
        UPDATE incidentes
        SET status = ?, atualizado_por = ?
        WHERE id_incidente = ?
    """, (novo_status, lead_id, id_incidente))
    conn.commit()   

    extras.registrar_log_atividade(lead_id, 'atualizar status', 'incidente')
    print("✅ Status atualizado com sucesso.")
    conn.close()





#b)Alterar prioridade

def alterar_prioridade_incidente(lead_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    id_incidente = input("🆔 Digite o ID do incidente: ").strip()
    nova_prioridade = input("🚨 Nova prioridade (baixa, média, alta): ").strip().lower()

    if nova_prioridade not in ['baixa', 'média', 'alta']:
        print("⚠️ Prioridade inválida.")
        return

    cursor.execute("""
        UPDATE incidentes
        SET prioridade = ?, atualizado_por = ?
        WHERE id_incidente = ?
    """, (nova_prioridade, lead_id, id_incidente))
    conn.commit()

    extras.registrar_log_atividade(lead_id, 'atualizar prioridade', 'incidente')
    print("✅ Prioridade atualizada com sucesso.")
    conn.close()



#c)Mudar o responsável

def mudar_responsavel_incidente(lead_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    id_incidente = input("🆔 Digite o ID do incidente: ").strip()
    novo_email = input("📧 Email do novo responsável: ").strip()

    cursor.execute("SELECT user_id FROM usuarios WHERE email = ?", (novo_email,))
    novo_analista = cursor.fetchone()
    if not novo_analista:
        print("⚠️ Usuário não encontrado.")
        return

    novo_id = novo_analista[0]

    cursor.execute("""
        UPDATE incidentes
        SET id_analista = ?, atualizado_por = ?
        WHERE id_incidente = ?
    """, (novo_id, lead_id, id_incidente))
    conn.commit()

    extras.registrar_log_atividade(lead_id, 'alterar responsável', 'incidente')
    print("✅ Responsável atualizado com sucesso.")
    conn.close()





#d)Adicionar descrição adicional
def adicionar_descricao_incidente(lead_id):
    fuso_horario = timezone(timedelta(hours=-3))
    data_hora_atual = datetime.now(fuso_horario)
    incidente_id = input("🆔 Digite o ID do incidente: ")

    conn = extras.conectar_banco()
    cursor = conn.cursor()

    # Buscar incidente com permissão
    cursor.execute("""
        SELECT i.id_incidente, i.titulo, i.status, i.descricao, i.id_analista, u.nome
        FROM incidentes i
        JOIN usuarios u ON u.user_id = id_analista
        WHERE i.id_incidente = ? AND (i.id_analista = ? OR i.atualizado_por = ?)
    """, (incidente_id, lead_id, lead_id))

    incidente = cursor.fetchone()
    if not incidente:
        print("⚠️ Incidente não encontrado ou sem permissão.")
        conn.close()
        return

    user_id, titulo, status_atual, descricao_antiga, id_analista, nome_usuario = incidente

    print(f"\n📄 Incidente: {titulo} | Status atual: {status_atual}")
    
    nova_entrada = input("🗒️ Descrição complementar (ou Enter para pular): ").strip()


    descricao_formatada = ""
    if nova_entrada:
        datahora = data_hora_atual.strftime("%d/%m/%Y %H:%M")
        nova_tag = f"{nova_entrada} ({datahora}, {nome_usuario})"
        if descricao_antiga:
            descricao_formatada = f"{descricao_antiga} | {nova_tag}"
        else:
            descricao_formatada = nova_tag
    else:
        descricao_formatada = descricao_antiga  # mantém se não houver entrada nova

    # Atualiza o incidente
    cursor.execute("""
        UPDATE incidentes
        SET  descricao = ?
        WHERE id_incidente = ?
    """, (descricao_formatada, incidente_id))
    
    conn.commit()
    extras.registrar_log_atividade(lead_id, 'atualizar', 'descrição')
    conn.close()

    print("✅ Descrição atualizada com sucesso!")


#e)Visualizar todos os incidentes
def listar_incidentes():
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.id_incidente, i.titulo, i.prioridade, i.status, i.data_criacao, u.nome AS responsavel, i.id_analista
        FROM incidentes i
        JOIN usuarios u ON i.id_analista = u.user_id
        ORDER BY i.data_criacao DESC
    """)
    incidentes = cursor.fetchall()
    conn.close()

    if not incidentes:
        print("⚠️ Nenhum incidente encontrado.")
        return

    # Cabeçalhos
    colunas = ["Incidente", "Título", "Prioridade", "Status", "Data de Criação", "Responsável", "ID Responsável"]

    # Calcular larguras dinâmicas, mínimo de 15
    larguras = []
    for i in range(len(colunas)):
        max_conteudo = max(len(str(row[i])) for row in incidentes)
        larguras.append(max(len(colunas[i]), max_conteudo, 15))

    # Imprimir cabeçalho
    cabecalho = " | ".join(col.ljust(w) for col, w in zip(colunas, larguras))
    print("\n" + cabecalho)
    print("-" * len(cabecalho))

    # Imprimir linhas
    for inc in incidentes:
        linha = [str(valor).ljust(w) for valor, w in zip(inc, larguras)]
        print(" | ".join(linha))


#RELATORIO DE LOGS

def listar_logs_atividades():
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.user_id, l.data_hora, u.nome, l.acao, l.tipo_recurso, l.id_recurso
        FROM log_atividades l
        JOIN usuarios u ON l.id_usuario = u.user_id
        ORDER BY l.data_hora DESC
    """)
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        print("⚠️ Nenhuma atividade registrada.")
        return

    colunas = ["ID", "Data/Hora", "Usuário", "Ação", "Recurso", "ID Recurso"]

    larguras = []
    for i in range(len(colunas)):
        max_conteudo = max(len(str(row[i])) for row in logs)
        larguras.append(max(len(colunas[i]), max_conteudo, 15))

    cabecalho = " | ".join(col.ljust(w) for col, w in zip(colunas, larguras))
    print("\n" + cabecalho)
    print("-" * len(cabecalho))

    for log in logs:
        linha = [str(valor).ljust(w) for valor, w in zip(log, larguras)]
        print(" | ".join(linha))







def menu_supervisor(lead_id):
    while True:
        print("""
        === Menu Supervisor ===
        1. Listar usuários
        2. Cadastrar analista
        3. Remover usuário
        4. Promover analista
        5. Ativar usuário
        6. Listar incidentes
        7. Atualizar status de incidente
        8. Alterar prioridade de incidente
        9. Mudar responsável de incidente
        10. Adicionar descrição ao incidente
        11. Listar Logs
        0. Sair
        """)
        opcao = input("Escolha uma opção: ").strip()
        if opcao == '1':
            listar_usuarios()
        elif opcao == '2':
            cadastrar_analista(lead_id)
        elif opcao == '3':
            remover_usuario(lead_id)
        elif opcao == '4':
            promover_analista(lead_id)
        elif opcao == '5':
            ativar_usuario(lead_id)
        elif opcao == '6':
            listar_incidentes()
        elif opcao == '7':
            atualizar_status_incidente(lead_id)
        elif opcao == '8':
            alterar_prioridade_incidente(lead_id)
        elif opcao == '9':
            mudar_responsavel_incidente(lead_id)
        elif opcao == '10':
            adicionar_descricao_incidente(lead_id)
        elif opcao == "11":
            listar_logs_atividades()
        elif opcao == '0':
            break
        else:
            print("⚠️ Opção inválida.")

      