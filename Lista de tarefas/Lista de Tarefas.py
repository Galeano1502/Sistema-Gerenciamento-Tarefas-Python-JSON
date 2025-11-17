#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de Tarefas
Implemente as regras descritas na atividade de aplicação:
- Persistência em JSON (tarefas.json, tarefas_arquivadas.json)
- Menu principal com validações
- Funções separadas com docstrings
- Tratamento de exceções
- Arquivamento automático de tarefas concluídas há mais de 7 dias
- Exclusão lógica
- Cálculo de tempo de execução para tarefas concluídas
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# ------------------------------
# Declaração de variáveis globais
# ------------------------------
TASKS_FILE = "tarefas.json"
ARCHIVE_FILE = "tarefas_arquivadas.json"

# Lista principal de tarefas (cada tarefa é um dict)
TASKS: List[Dict] = []

# Lista acumulada de arquivadas (persistida em ARCHIVE_FILE)
ARCHIVED_TASKS: List[Dict] = []

# Contador de ID numérico único - gerenciado fora das funções principais
ID_COUNTER = 1

# Prioridades válidas e ordem para busca de urgência
PRIORITIES = ["Urgente", "Alta", "Média", "Baixa"]
PRIORITY_ORDER = PRIORITIES  # ordem já do mais urgente ao menos


# ------------------------------
# Funções de persistência e utilitárias
# ------------------------------
def print_debug(msg: str):
    """Imprime mensagens de debug padronizadas."""
    print(f"[DEBUG] {msg}")


def ensure_files_exist():
    """
    Verifica se arquivos JSON necessários existem; se não, cria com estrutura válida.
    """
    print_debug("Executando ensure_files_exist")
    for fname in (TASKS_FILE, ARCHIVE_FILE):
        if not os.path.exists(fname):
            with open(fname, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)


def carregar_dados():
    """
    Carrega os arquivos tarefas.json e tarefas_arquivadas.json para as variáveis globais.
    Ajusta o ID_COUNTER com base nas tarefas carregadas.
    """
    global TASKS, ARCHIVED_TASKS, ID_COUNTER
    print_debug("Executando carregar_dados")
    ensure_files_exist()
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            TASKS = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        TASKS = []

    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            ARCHIVED_TASKS = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        ARCHIVED_TASKS = []

    # Ajusta ID_COUNTER para ser maior que qualquer ID existente
    max_id = 0
    for t in TASKS + ARCHIVED_TASKS:
        try:
            tid = int(t.get("id", 0))
            if tid > max_id:
                max_id = tid
        except Exception:
            continue
    ID_COUNTER = max_id + 1


def salvar_dados():
    """
    Salva TASKS e ARCHIVED_TASKS nos arquivos JSON correspondentes.
    """
    print_debug("Executando salvar_dados")
    # salvar tarefas ativas
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(TASKS, f, ensure_ascii=False, indent=2, default=str)

    # salvar arquivadas
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(ARCHIVED_TASKS, f, ensure_ascii=False, indent=2, default=str)


def gerar_id() -> int:
    """
    Gera um ID numérico único para uma nova tarefa.
    Retorna: ID (int)
    """
    global ID_COUNTER
    print_debug("Executando gerar_id")
    current = ID_COUNTER
    ID_COUNTER += 1
    return current


def agora_iso() -> str:
    """Retorna a data-hora atual em formato ISO (string)."""
    return datetime.now().isoformat()


def parse_iso(dt_str: str) -> Optional[datetime]:
    """Converte string ISO para datetime; retorna None se inválido."""
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


# ------------------------------
# Funções de validação
# ------------------------------
def validar_prioridade(prio: str) -> bool:
    """
    Valida se a prioridade informada existe no sistema.
    Retorna True se válida, False caso contrário.
    """
    print_debug("Executando validar_prioridade")
    return prio.capitalize() in PRIORITIES


def validar_origem(orig: str) -> bool:
    """
    Valida origem: E-mail, Telefone, Chamado do Sistema
    """
    print_debug("Executando validar_origem")
    valid = ["E-mail", "Telefone", "Chamado do Sistema"]
    return orig.capitalize() in [v.capitalize() for v in valid]


# ------------------------------
# Operações principais (modularizadas)
# ------------------------------
def criar_tarefa():
    """
    Cria uma nova tarefa solicitando informações ao usuário,
    valida os dados e adiciona a tarefa à lista global de tarefas.
    Parâmetros: nenhum
    Retorno: nenhum
    """
    print_debug("Executando a função criar_tarefa")
    global TASKS

    try:
        titulo = input("Título (obrigatório): ").strip()
        if not titulo:
            print("Título é obrigatório. Operação cancelada.")
            return

        descricao = input("Descrição (opcional): ").strip()

        # Prioridade - mostrar opções
        print("Opções de Prioridade:", ", ".join(PRIORITIES))
        prioridade = input("Prioridade (Urgente/Alta/Média/Baixa) (obrigatório): ").strip().capitalize()
        if not validar_prioridade(prioridade):
            print("Prioridade inválida. Operação cancelada.")
            return

        # Origem - mostrar opções
        print("Opções de Origem: E-mail, Telefone, Chamado do Sistema")
        origem = input("Origem (obrigatório): ").strip()
        # Normaliza primeiras letras
        origem_norm = origem.title()
        # Ajuste especial para "Chamado do Sistema"
        if origem_norm.lower() in ["chamado", "chamadodosistema", "chamado do sistema"]:
            origem_norm = "Chamado do Sistema"

        if not validar_origem(origem_norm):
            print("Origem inválida. Operação cancelada.")
            return

        tarefa = {
            "id": gerar_id(),
            "titulo": titulo,
            "descricao": descricao,
            "prioridade": prioridade,
            "status": "Pendente",
            "origem": origem_norm,
            "data_criacao": agora_iso(),
            "data_conclusao": None
        }

        TASKS.append(tarefa)
        print(f"Tarefa criada com sucesso. ID = {tarefa['id']}")
    except Exception as e:
        print("Erro ao criar tarefa:", e)


def encontrar_tarefa_por_id(tid: int) -> Optional[Dict]:
    """
    Retorna a tarefa na lista TASKS com dado ID ou None se não encontrada.
    """
    print_debug("Executando encontrar_tarefa_por_id")
    for t in TASKS:
        try:
            if int(t.get("id")) == int(tid):
                return t
        except Exception:
            continue
    return None


def verificar_urgencia():
    """
    Busca a próxima tarefa de maior prioridade disponível e atualiza seu status para 'Fazendo'.
    Exibe a tarefa selecionada (a primeira encontrada na ordem de prioridade).
    """
    print_debug("Executando verificar_urgencia")
    global TASKS

    # Filtra somente tarefas que estão Pendente
    pendentes = [t for t in TASKS if t.get("status") == "Pendente"]
    if not pendentes:
        print("Não há tarefas pendentes.")
        return

    # Percorre prioridades na ordem e pega a primeira tarefa encontrada
    selecionada = None
    for pr in PRIORITY_ORDER:
        for t in pendentes:
            if t.get("prioridade") == pr:
                selecionada = t
                break
        if selecionada:
            break

    if not selecionada:
        # pega a primeira pendente, se por algum motivo não encontrou por prioridade
        selecionada = pendentes[0]

    # Atualiza status
    selecionada["status"] = "Fazendo"
    print("Tarefa selecionada para execução:")
    mostrar_detalhes_tarefa(selecionada)


def atualizar_prioridade():
    """
    Permite alterar a prioridade de uma tarefa existente, validando a nova prioridade.
    """
    print_debug("Executando atualizar_prioridade")
    try:
        tid = int(input("Informe o ID da tarefa a alterar prioridade: ").strip())
    except Exception:
        print("ID inválido.")
        return

    t = encontrar_tarefa_por_id(tid)
    if not t:
        print("Tarefa não encontrada.")
        return

    print("Prioridade atual:", t.get("prioridade"))
    print("Opções:", ", ".join(PRIORITIES))
    nova = input("Informe a nova prioridade: ").strip().capitalize()
    if not validar_prioridade(nova):
        print("Prioridade inválida. Operação cancelada.")
        return

    t["prioridade"] = nova
    print(f"Prioridade da tarefa {tid} alterada para {nova}.")


def concluir_tarefa():
    """
    Marca uma tarefa como concluída, preenche data de conclusão e altera status para 'Concluída'.
    """
    print_debug("Executando concluir_tarefa")
    try:
        tid = int(input("Informe o ID da tarefa a concluir: ").strip())
    except Exception:
        print("ID inválido.")
        return

    t = encontrar_tarefa_por_id(tid)
    if not t:
        print("Tarefa não encontrada.")
        return

    if t.get("status") == "Concluída":
        print("Tarefa já está concluída.")
        return

    # preencher data de conclusão
    t["data_conclusao"] = agora_iso()
    t["status"] = "Concluída"
    print(f"Tarefa {tid} marcada como Concluída em {t['data_conclusao']}")


def arquivar_tarefas_antigas():
    """
    Arquiva automaticamente tarefas concluídas há mais de 7 dias.
    Ao arquivar, as tarefas são registradas em tarefas_arquivadas.json e
    removidas da lista ativa TASKS.
    """
    print_debug("Executando arquivar_tarefas_antigas")
    global TASKS, ARCHIVED_TASKS

    agora = datetime.now()
    limite = agora - timedelta(days=7)
    a_mover = []
    for t in TASKS:
        if t.get("status") == "Concluída" and t.get("data_conclusao"):
            dt = parse_iso(t["data_conclusao"])
            if dt and dt < limite:
                a_mover.append(t)

    if not a_mover:
        print("Nenhuma tarefa concluída há mais de 7 dias para arquivar.")
        return

    # Registrar no arquivo de arquivadas (acumular histórico)
    for t in a_mover:
        ARCHIVED_TASKS.append(t)

    # Remover da lista ativa TASKS
    TASKS = [t for t in TASKS if t not in a_mover]

    salvar_dados()
    print(f"{len(a_mover)} tarefa(s) arquivada(s) e registrada(s) em '{ARCHIVE_FILE}'.")


def excluir_tarefa():
    """
    Implementa exclusão lógica: atualiza status para 'Excluída' sem remover da lista.
    """
    print_debug("Executando excluir_tarefa")
    try:
        tid = int(input("Informe o ID da tarefa a excluir (lógico): ").strip())
    except Exception:
        print("ID inválido.")
        return

    t = encontrar_tarefa_por_id(tid)
    if not t:
        print("Tarefa não encontrada.")
        return

    t["status"] = "Excluída"
    print(f"Tarefa {tid} marcada como 'Excluída' (exclusão lógica).")


def mostrar_detalhes_tarefa(t: Dict):
    """
    Exibe todas as informações de uma tarefa (detalhamento).
    """
    print_debug("Executando mostrar_detalhes_tarefa")
    print("-" * 40)
    print(f"ID: {t.get('id')}")
    print(f"Título: {t.get('titulo')}")
    print(f"Descrição: {t.get('descricao')}")
    print(f"Prioridade: {t.get('prioridade')}")
    print(f"Status: {t.get('status')}")
    print(f"Origem: {t.get('origem')}")
    print(f"Data de criação: {t.get('data_criacao')}")
    if t.get("data_conclusao"):
        print(f"Data de conclusão: {t.get('data_conclusao')}")
        # calcular tempo de execução
        dt_inicio = parse_iso(t.get("data_criacao"))
        dt_fim = parse_iso(t.get("data_conclusao"))
        if dt_inicio and dt_fim:
            dur = dt_fim - dt_inicio
            dias = dur.days
            horas, resto = divmod(dur.seconds, 3600)
            minutos, segundos = divmod(resto, 60)
            print(f"Tempo de execução: {dias}d {horas}h {minutos}m {segundos}s")
    print("-" * 40)


def relatorio_tarefas():
    """
    Exibe todas as tarefas (inclusive Pendente, Fazendo, Concluída, Arquivado, Excluída).
    Para tarefas concluídas calcula o tempo de execução.
    """
    print_debug("Executando relatorio_tarefas")
    if not TASKS:
        print("Nenhuma tarefa ativa registrada.")
        return

    for t in TASKS:
        mostrar_detalhes_tarefa(t)


def relatorio_arquivadas():
    """
    Exibe a lista de tarefas arquivadas (aquelas presentes em tarefas_arquivadas.json).
    Tarefas excluídas não devem ser listadas neste relatório.
    """
    print_debug("Executando relatorio_arquivadas")
    # Filtra as arquivadas que não estão com status Excluída
    arquivadas_validas = [t for t in ARCHIVED_TASKS if t.get("status") != "Excluída"]
    if not arquivadas_validas:
        print("Nenhuma tarefa arquivada (ou somente tarefas excluídas).")
        return

    for t in arquivadas_validas:
        mostrar_detalhes_tarefa(t)


def limpar_tarefas_excluidas_do_arquivo_de_arquivadas():
    """
    (Auxiliar) Remove do arquivo de arquivadas entradas duplicadas ou com status
    'Excluída' se desejado — opcional, implementado para manutenção.
    """
    print_debug("Executando limpar_tarefas_excluidas_do_arquivo_de_arquivadas")
    global ARCHIVED_TASKS
    # aqui apenas demonstrativo; não chamado automaticamente
    ARCHIVED_TASKS = [t for t in ARCHIVED_TASKS if t.get("status") != "Excluída"]
    salvar_dados()
    print("Limpeza concluída em arquivos de arquivadas.")


# ------------------------------
# Menu principal e fluxo
# ------------------------------
def mostrar_menu():
    """
    Exibe o menu principal com todas as opções do sistema.
    """
    print_debug("Executando mostrar_menu")
    print("\n" + "=" * 40)
    print("GERENCIADOR DE TAREFAS - MENU PRINCIPAL")
    print("1 - Criar tarefa")
    print("2 - Verificar urgência (pegar próxima tarefa para fazer)")
    print("3 - Atualizar prioridade")
    print("4 - Concluir tarefa")
    print("5 - Arquivar tarefas antigas (concluídas há > 7 dias)")
    print("6 - Excluir tarefa (exclusão lógica)")
    print("7 - Relatório: todas tarefas ativas")
    print("8 - Relatório: tarefas arquivadas")
    print("9 - Salvar agora")
    print("0 - Sair (salva e finaliza)")
    print("=" * 40)


def opcao_valida(op: str) -> bool:
    """
    Verifica se a opção informada existe no menu.
    """
    print_debug("Executando opcao_valida")
    return op in [str(i) for i in range(0, 10)]


def main():
    """
    Corpo principal do programa: carrega dados, roda menu e salva antes de sair.
    """
    print_debug("Executando main")
    carregar_dados()

    # Ao iniciar, executar arquivamento automático (requisito)
    arquivar_tarefas_antigas()

    while True:
        mostrar_menu()
        opc = input("Escolha uma opção: ").strip()
        if not opcao_valida(opc):
            print("Opção inválida. Tente novamente.")
            continue

        try:
            if opc == "1":
                criar_tarefa()
            elif opc == "2":
                verificar_urgencia()
            elif opc == "3":
                atualizar_prioridade()
            elif opc == "4":
                concluir_tarefa()
            elif opc == "5":
                arquivar_tarefas_antigas()
            elif opc == "6":
                excluir_tarefa()
            elif opc == "7":
                relatorio_tarefas()
            elif opc == "8":
                relatorio_arquivadas()
            elif opc == "9":
                salvar_dados()
                print("Dados salvos com sucesso.")
            elif opc == "0":
                # antes de finalizar, salvar dados obrigatoriamente
                salvar_dados()
                print("Dados salvos. Encerrando programa.")
                exit(0)
        except Exception as e:
            # Tratamento geral para evitar que o programa quebre
            print("Ocorreu um erro durante a operação:", e)
            print("Voltando ao menu principal.")


if __name__ == "__main__":
    main()
