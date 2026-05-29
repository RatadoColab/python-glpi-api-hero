from glpi_api_hero import ApiCommunication
from glpi_api_hero.location import Location
import json
import sys

# Dados de acesso da VM (local) do Leonardo.
user = 'glpi'
passwd = 'glpi'
url = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'

ApiCommunication.setConnectionParameters(url=url, apptoken=apptoken, user=user, passwd=passwd)
ApiCommunication.initSession()
print("Sessão iniciada.")

ApiCommunication.setProfileEntity(profiles_id=4, entities_id=0, is_recursive=True)

# ==============================================================
# Importação de localizações a partir do JSON (amostra.json)
# ==============================================================

# Carrega a lista de unidades organizacionais do IBGE
with open('amostra-pequena.json', encoding='utf-8') as f:
    unidades = json.load(f)

# Adiciona todas as localizações de uma só vez.
# locations_id=0 → raiz (sem pai); entities_id=0 → entidade alvo no GLPI.
resultado = Location.addFromList(unidades, locations_id=0, entities_id=0)
print("Localizações criadas:", resultado)
sys.exit()

# # Listar todas as localizações (primeiras 10)
# locacoes = Location.get_all_items(range='0-20')
# # print(todas)
# for l in locacoes:
#     print(l["id"], l["name"], l["address"], sep=" | ")
# print("Localizações retornadas:", len(locacoes))
# sys.exit()

# Busca geral via search
resultado_busca = Location.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'Rio'}]
)
print("Busca realizada.")
sys.exit()

# ==============================================================
# Location: métodos herdados de CommonDBTM
# ==============================================================

# Criar uma localização simples
nova_localizacao = {
    'name': 'Teste001',
    'address': 'Avenida Franklin Roosevelt, 166',
    'building': 'Centro',
    'postcode': '20021-120',
    'town': 'Rio de Janeiro',
    'state': 'RJ',
    'comment': 'Sede principal do IBGE.',
    'entities_id': 0,
    'code': 123456
}
result = Location.add(nova_localizacao)
location_id = result[0]['id']
print("Localização criada. ID:", location_id)
sys.exit()

# Criar múltiplas localizações de uma vez
result_multi = Location.add(
    {'name': 'Sala 101', 'locations_id': sub_location_id, 'entities_id': 0},
    {'name': 'Sala 102', 'locations_id': sub_location_id, 'entities_id': 0},
)
print("Múltiplas localizações criadas:", result_multi)

# Obter localização pelo ID
localizacao = Location.get(location_id)
print("Localização obtida:", localizacao.get('name'))

# Atualizar localização
Location.update({'id': location_id, 'comment': 'Comentário atualizado.'})
print("Localização atualizada.")

# ==============================================================
# Busca por nome e nome completo
# ==============================================================

# Buscar localização pelo nome (busca parcial)
por_nome = Location.getByName('Sede')
print("Busca por nome:", por_nome)

# Buscar pelo caminho hierárquico completo
por_nome_completo = Location.getByCompleteName('Sede Rio de Janeiro > Bloco A')
print("Busca por nome completo:", por_nome_completo)

# ==============================================================
# Hierarquia
# ==============================================================

# Obter sub-localizações filhas diretas
filhas = Location.getChildren(location_id)
print("Localizações filhas:", filhas)

# Obter todas as localizações raiz (sem pai)
raizes = Location.getRoots()
print("Localizações raiz:", raizes)

# ==============================================================
# Itens na localização
# ==============================================================

# Computadores cadastrados na localização
computadores = Location.getComputers(location_id)
print("Computadores na localização:", computadores)

# Equipamentos de rede na localização
equipamentos = Location.getNetworkEquipments(location_id)
print("Equipamentos de rede:", equipamentos)

# Chamados abertos na localização
chamados = Location.getTickets(location_id)
print("Chamados na localização:", chamados)

# Usuários com a localização cadastrada
usuarios = Location.getUsers(location_id)
print("Usuários na localização:", usuarios)

# ==============================================================
# Histórico de alterações
# ==============================================================

logs = Location.getLogs(location_id)
print("Logs da localização:", logs)

# ==============================================================
# Deletar localizações criadas no teste
# ==============================================================

Location.delete([{'id': sub_location_id}], force_purge=True)
Location.delete([{'id': location_id}], force_purge=True)
print("Localizações deletadas.")

ApiCommunication.killSession()
print("Sessão finalizada.")
