import extras
from datetime import datetime


def registrar_incidente(user_id):
    
    titulo = input("📝 Título do incidente: ").strip()
    descricao = input("📄 Descrição inicial: ").strip()

    conn = extras.conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO incidentes (titulo, descricao, prioridade, id_analista, data_criacao)
        VALUES (?, ?, 'média', ?, ?)
    """, (titulo, descricao, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()

    cursor.execute("SELECT last_insert_rowid()")
    id_incidente = cursor.fetchone()[0]


    print(f"✅ Incidente registrado com ID: {id_incidente}")

    conn.close()

    extras.registrar_log_atividade(user_id, 'criar', 'incidente')
    print("✅ Incidente registrado com sucesso!")


#b) Visualizar incidentes (onde é responsável ou criador)
def visualizar_meus_incidentes(user_id):
    conn = extras.conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.id_incidente, i.titulo, i.status, i.prioridade, u.nome as responsavel, i.data_criacao
        FROM incidentes i
        JOIN usuarios u ON i.id_analista = u.user_id
        WHERE i.id_analista = ? OR i.atualizado_por = ?
        ORDER BY i.data_criacao DESC
    """, (user_id, user_id))
    
    incidentes = cursor.fetchall()
    conn.close()

    if not incidentes:
        print("⚠️ Nenhum incidente encontrado.")
        return

    print("\n📋 Incidentes:")
    print("ID Incidente  | Título".ljust(40) +"| Status     | Prioridade | Criado por       | Criado em")
    print("-" * 100)
    for id_incidente, titulo, status, prioridade, id_analista, data in incidentes:
        print(f"{str(id_incidente).ljust(4)} | {titulo.ljust(30)} | {status.ljust(10)} | {prioridade.ljust(10)} | {str(id_analista).ljust(16)} | {data}")



#c)Atualizar status e adicionar descrição
def atualizar_incidente_analista(user_id):
    incidente_id = input("🆔 Digite o ID do incidente: ")

    conn = extras.conectar_banco()
    cursor = conn.cursor()

    # Buscar incidente com permissão
    cursor.execute("""
        SELECT i.id_incidente, i.titulo, i.status, i.descricao, i.id_analista, u.nome
        FROM incidentes i
        JOIN usuarios u ON u.user_id = i.id_analista
        WHERE i.id_incidente = ? AND (i.id_analista = ? OR i.atualizado_por = ?)
    """, (incidente_id, user_id, user_id))

    incidente = cursor.fetchone()
    if not incidente:
        print("⚠️ Incidente não encontrado ou sem permissão.")
        conn.close()
        return

    user_id, titulo, status_atual, descricao_antiga, id_analista, nome_usuario = incidente

    print(f"\n📄 Incidente: {titulo} | Status atual: {status_atual}")
    novo_status = input("📌 Novo status (pendente/em análise/resolvido): ").strip().lower()
    nova_entrada = input("🗒️ Descrição complementar (ou Enter para pular): ").strip()

    if novo_status not in ['pendente', 'em análise', 'resolvido']:
        print("⚠️ Status inválido.")
        conn.close()
        return

    descricao_formatada = ""
    if nova_entrada:
        datahora = datetime.now().strftime("%d/%m/%Y %H:%M")
        nova_tag = f"{nova_entrada} ({datahora}, {nome_usuario})"
        if descricao_antiga:
            descricao_formatada = f"{descricao_antiga} | {nova_tag}"
        else:
            descricao_formatada = nova_tag
    else:
        descricao_formatada = descricao_antiga 

    # Atualiza o incidente
    cursor.execute("""
        UPDATE incidentes
        SET status = ?, descricao = ?, atualizado_por = ?
        WHERE id_incidente = ?
    """, (novo_status, descricao_formatada, user_id, incidente_id))
    
    conn.commit()
    conn.close()

    extras.registrar_log_atividade(user_id, 'atualizar', 'incidente')

    print("✅ Incidente atualizado com sucesso!")


def menu_analista(user_id):
    while True:
        print("""
        === Menu Analista ===
        1. Registrar novo incidente 
        2. Visualizar meus incidentes
        3. Atualizar meus incidentes
        0. Sair
        """)
        opcao = input("Escolha uma opção: ").strip()
        if opcao == '1':
            registrar_incidente(user_id)
        elif opcao == '2':
            visualizar_meus_incidentes(user_id)
        elif opcao == '3':
            atualizar_incidente_analista(user_id)
        elif opcao == '0':
            break
        else:
            print("⚠ Opção inválida.")  
