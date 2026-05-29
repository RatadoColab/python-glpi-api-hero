from glpi_api_hero import ApiCommunication
from glpi_api_hero import Ticket
from datetime import datetime

# user = 'sp-andre.proto'
# passwd = 'sdsadasdasdad'
# url = 'https://betacentral.ibge.gov.br/apírest.php'
# apptoken = 'DSFdsfADSFADSgADFGFDSGDASFG'

# Dados de acesso da VM (local) do Leonardo.
user = 'glpi'
passwd = 'glpi'
url = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'

# Definição dos parâmetros de conexão.
ApiCommunication.setConnectionParameters(url = url, apptoken=apptoken, user=user, passwd=passwd )
# Iniciar seção.
ApiCommunication.initSession()
# Configuração de perfil e entidade.
ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)

data_string = datetime.now().strftime('%Y%m%d%H%M%S')

# Exemplo de criação de chamado
input = {
    'name': 'Titulo do chamado '+data_string,
    'content': 'Por favor resolver o meu problema',
    'itilcategories_id': '672',
    'type': 1,
    '_user_requester': 9407
}
result = Ticket.add(input)
#obter o ID do ticket
ticket_id = result[0]['id'] # result['id']
print("ticket_id:", ticket_id)
# print(result)

# Enviando um acompanhamento
input = {
    'content': 'Favor esquecer o que eu pedi'
}
Ticket.addFollowUp(ticket_id, input)
print("Acompanhamento adicionado!")

ApiCommunication.killSession()
print("Seção finalizada.")


