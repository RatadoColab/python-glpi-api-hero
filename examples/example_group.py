from glpi_api_hero import ApiCommunication
from glpi_api_hero import Group
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
# Group: métodos herdados de CommonDBTM
# ==============================================================

# Criar grupo
novo_grupo = {
    'name': 'Grupo Teste ' + data_string,
    'comment': 'Grupo criado para testes automatizados.',
    'entities_id': 111,
    'is_recursive': 1,
    'is_assign': 1,   # pode ser atribuído em chamados
    'is_requester': 1,
    'is_watcher': 1,
}
result = Group.add(novo_grupo)
group_id = result[0]['id']
print("Grupo criado. ID:", group_id)
sys.exit()

# Obter grupo pelo ID
grupo = Group.get(group_id)
print("Grupo obtido:", grupo.get('name'))

# Atualizar grupo
Group.update({'id': group_id, 'comment': 'Comentário atualizado.'})
print("Grupo atualizado.")

# Listar todos os grupos (primeiros 10)
todos = Group.get_all_items(range='0-9')
print("Grupos retornados:", len(todos))

# Busca geral via search
resultado_busca = Group.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'Teste'}]
)
print("Busca realizada.")

# Busca por nome exato
por_nome = Group.getByName('N1 - Suporte')
print("Busca por nome:", por_nome)

# ==============================================================
# Gerenciamento de usuários no grupo
# ==============================================================

# ID de um usuário existente no GLPI para os testes abaixo
user_id = 9407

# Adicionar usuário ao grupo
Group.addUser(group_id, user_id)
print("Usuário adicionado ao grupo.")

# Listar todos os usuários do grupo
membros = Group.getAllUsers(group_id)
print("Membros do grupo:", membros)

# Remover usuário do grupo (localiza o vínculo Group_User e deleta)
Group.deleteUser(group_id, user_id)
print("Usuário removido do grupo.")

# Confirmar remoção
membros_apos = Group.getAllUsers(group_id)
print("Membros após remoção:", membros_apos)

# ==============================================================
# Chamados associados ao grupo
# ==============================================================

# Chamados onde o grupo é ATRIBUÍDO (padrão — técnicos responsáveis)
chamados_assigned = Group.getAllTickets(group_id, actor_type=Group.ASSIGNED)
print("Chamados como atribuído:", chamados_assigned)

# Chamados onde o grupo é REQUERENTE
chamados_requester = Group.getAllTickets(group_id, actor_type=Group.REQUESTER)
print("Chamados como requerente:", chamados_requester)

# Chamados onde o grupo é OBSERVADOR
chamados_observer = Group.getAllTickets(group_id, actor_type=Group.OBSERVER)
print("Chamados como observador:", chamados_observer)

# Com paginação: primeiros 5 chamados atribuídos ao grupo
chamados_paginados = Group.getAllTickets(group_id, actor_type=Group.ASSIGNED, range='0-4')
print("Chamados paginados:", chamados_paginados)

# ==============================================================
# Sub-itens via get_sub_items (CommonDBTM)
# ==============================================================

# Sub-grupos (grupos filhos)
sub_grupos = Group.get_sub_items(group_id, 'Group')
print("Sub-grupos:", sub_grupos)

# ==============================================================
# Deletar grupo criado no teste
# ==============================================================

Group.delete([{'id': group_id}], force_purge=True)
print("Grupo deletado.")

ApiCommunication.killSession()
print("Sessão finalizada.")
