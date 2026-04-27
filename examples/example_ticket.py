from glpi_api_hero import ApiCommunication
from glpi_api_hero import Ticket
from datetime import datetime
import sys

# Dados de acesso da VM (local) do Leonardo.
user = 'glpi'
passwd = 'glpi'
url = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'

ApiCommunication.setConnectionParameters(url=url, apptoken=apptoken, user=user, passwd=passwd)
ApiCommunication.initSession()
print("Sessão iniciada.")

ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)

data_string = datetime.now().strftime('%Y%m%d%H%M%S')

# ==============================================================
# Ticket: métodos herdados de CommonDBTM
# ==============================================================

# # Criar chamado
# input_ticket = {
#     'name': 'Chamado de teste ' + data_string,
#     'content': 'Descrição detalhada do problema encontrado.',
#     'itilcategories_id': '672',
#     'type': 1,               # 1=Incident, 2=Request
#     'priority': 3,           # 1=Very Low ... 6=Very High
#     '_user_requester': 9407,
# }
# result = Ticket.add(input_ticket)
# ticket_id = result[0]['id']
# print("Chamado criado. ID:", ticket_id)

# # # Obter chamado pelo ID
# ticket = Ticket.get(ticket_id)
# print("Chamado obtido:", ticket.get('name'))

# # # Atualizar chamado
# Ticket.update({'id': ticket_id, 'priority': 4})
# print("Chamado atualizado.")

# # Listar todos os chamados (paginado)
# todos = Ticket.get_all_items(range='0-9')
# print("Total de chamados retornados:", len(todos))

# # Buscar chamados (search)
resultado_busca = Ticket.search(criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'teste'}])
print("Busca realizada.")
print(resultado_busca)
sys.exit()

# ==============================================================
# FollowUp (Acompanhamento)
# ==============================================================

# # Adicionar acompanhamento
Ticket.addFollowUp(ticket_id, {'content': 'Estamos analisando o problema.'})
print("Acompanhamento adicionado.")

# # Obter acompanhamentos do chamado
followups = Ticket.getFollowUps(ticket_id)
print("Acompanhamentos:", followups)

# Atualizar acompanhamento (usar o ID retornado pela criação)
followup_id = 6 # <id do acompanhamento>
Ticket.updateFollowUp(followup_id, {'content': 'Atualização do acompanhamento.'})

# Deletar acompanhamento
followup_id = 6 # <id do acompanhamento>
Ticket.deleteFollowUp(followup_id)

# ==============================================================
# Solution (Solução)
# ==============================================================

# # Adicionar solução
Ticket.addSolution(ticket_id, {
    'content': 'Problema resolvido reinstalando o software.',
    'solutiontypes_id': 1,
})
print("Solução adicionada.")

# # Obter solução do chamado
solucao = Ticket.getSolution(ticket_id)
print("Solução:", solucao)

# Atualizar solução
solution_id = 4 # <id retornado>
Ticket.updateSolution(solution_id, {'content': 'Solução revisada.'})

# Deletar solução
Ticket.deleteSolution(solution_id)

# VERIFICAR: adicionar usuário e informar o id do mesmo para testar.
# ==============================================================
# Validation (Validação)
# ==============================================================

# Solicitar validação a um usuário
# Ticket.addValidation(ticket_id, {
#     'users_id_validate': 7,
#     'comment_submission': 'Por favor validar a solução.',
# })
# print("Validação solicitada.")

# Obter validações do chamado
# validacoes = Ticket.getValidations(ticket_id)
# print("Validações:", validacoes)

# Atualizar validação
# validation_id = <id retornado>
# Ticket.updateValidation(validation_id, {'status': 2})  # 2=Accepted, 4=Refused

# Deletar validação
# Ticket.deleteValidation(validation_id)

# VERIFICAR
# ==============================================================
# Task (Tarefa)
# ==============================================================

# # Adicionar tarefa
# Ticket.addTask(ticket_id, {
#     'content': 'Verificar logs do servidor.',
#     'taskcategories_id': 1,
#     'state': 1,  # 0=Informação, 1=A fazer, 2=Feito
#     'users_id_tech': 4, # 9407,
# })
# print("Tarefa adicionada.")

# # Obter tarefas do chamado
# tarefas = Ticket.getTasks(ticket_id)
# print("Tarefas:", tarefas)

# Atualizar tarefa
# task_id = <id retornado>
# Ticket.updateTask(task_id, {'state': 2})

# Deletar tarefa
# Ticket.deleteTask(task_id)

# VERIFICAR
# ==============================================================
# Actors (Atores: requerente, técnico, grupo, etc.)
# ==============================================================

# # Adicionar ator ao chamado
# Ticket.addActor(ticket_id, {
#     'type': 2,          # 1=Requerente, 2=Atribuído, 3=Observador
#     'users_id': 7, # 9407,
# })
# print("Ator adicionado.")

# # Obter atores do chamado
# atores = Ticket.getActors(ticket_id)
# print("Atores:", atores)

# Deletar ator
# actor_id = <id retornado>
# Ticket.deleteActor(actor_id)

# VERIFICAR
# ==============================================================
# Items associados (ativos vinculados ao chamado)
# ==============================================================

# # Associar item (ex: computador)
# Ticket.addItem(ticket_id, {
#     'itemtype': 'Computer',
#     'items_id': 42,
# })
# print("Item associado ao chamado.")

# # Obter itens vinculados
# itens = Ticket.getItems(ticket_id)
# print("Itens:", itens)

# Deletar vínculo de item
# item_link_id = <id retornado>
# Ticket.deleteItem(item_link_id)

# VERIFICAR
# ==============================================================
# Linked Tickets (Chamados vinculados)
# ==============================================================

# # Vincular outro chamado
# Ticket.addLinkedTicket(ticket_id, {
#     'tickets_id_2': 999,
#     'link': 1,  # 1=Linked, 2=Duplicate, 3=Child, 4=Parent
# })
# print("Chamado vinculado.")

# # Obter chamados vinculados
# vinculados = Ticket.getLinkedTickets(ticket_id)
# print("Chamados vinculados:", vinculados)

# Deletar vínculo
# linked_ticket_id = <id retornado>
# Ticket.deleteLinkedTicket(linked_ticket_id)

# ==============================================================
# Deletar chamado (ao final dos testes)
# ==============================================================

# Ticket.delete([{'id': ticket_id}], force_purge=True)
# print("Chamado deletado.")

ApiCommunication.killSession()
print("Sessão finalizada.")
