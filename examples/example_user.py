from glpi_api_hero import ApiCommunication
from glpi_api_hero import User
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
# User: métodos herdados de CommonDBTM
# ==============================================================

# Criar usuário
novo_usuario = {
    'name': 'usuario.teste.' + data_string,
    'realname': 'Usuário Teste',
    'firstname': 'Usuário',
    'password': 'Senha@123',
    'password2': 'Senha@123',
    'email': 'usuario.teste.' + data_string + '@exemplo.com',
    'profiles_id': 4,
    'entities_id': 111,
    'is_active': 1,
}
result = User.add(novo_usuario)
user_id = result[0]['id']
print("Usuário criado. ID:", user_id)
sys.exit()

# Obter usuário pelo ID
usuario = User.get(user_id)
print("Usuário obtido:", usuario.get('name'))

# Atualizar usuário
User.update({'id': user_id, 'realname': 'Usuário Teste Atualizado'})
print("Usuário atualizado.")

# Listar todos os usuários (primeiros 10)
todos = User.get_all_items(range='0-9')
print("Usuários retornados:", len(todos))

# Busca geral via search
resultado_busca = User.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'teste'}]
)
print("Busca realizada.")

# ==============================================================
# Busca por login e e-mail
# ==============================================================

# Buscar usuário pelo login (name)
por_login = User.getByUsername('glpi')
print("Busca por login:", por_login)

# Buscar usuário pelo e-mail
por_email = User.getByEmail('admin@exemplo.com')
print("Busca por e-mail:", por_email)

# ==============================================================
# Perfis e Grupos vinculados ao usuário
# ==============================================================

# Obter todos os perfis do usuário
perfis = User.getAllProfiles(user_id)
print("Perfis do usuário:", perfis)

# Obter todos os grupos do usuário
grupos = User.getAllGroups(user_id)
print("Grupos do usuário:", grupos)

# ==============================================================
# Chamados associados ao usuário
# ==============================================================

# Chamados onde o usuário é REQUERENTE (padrão)
chamados_requester = User.getAllTickets(user_id, actor_type=User.REQUESTER)
print("Chamados como requerente:", chamados_requester)

# Chamados onde o usuário é ATRIBUÍDO (técnico responsável)
chamados_assigned = User.getAllTickets(user_id, actor_type=User.ASSIGNED)
print("Chamados como atribuído:", chamados_assigned)

# Chamados onde o usuário é OBSERVADOR
chamados_observer = User.getAllTickets(user_id, actor_type=User.OBSERVER)
print("Chamados como observador:", chamados_observer)

# Com paginação: primeiros 5 chamados como requerente
chamados_paginados = User.getAllTickets(user_id, actor_type=User.REQUESTER, range='0-4')
print("Chamados paginados:", chamados_paginados)

# ==============================================================
# Sub-itens do usuário via get_sub_items (CommonDBTM)
# ==============================================================

# Listar emails do usuário
emails = User.get_sub_items(user_id, 'UserEmail')
print("E-mails do usuário:", emails)

# ==============================================================
# Deletar usuário criado no teste
# ==============================================================

User.delete([{'id': user_id}], force_purge=True)
print("Usuário deletado.")

ApiCommunication.killSession()
print("Sessão finalizada.")
