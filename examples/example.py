# from glpi_api_hero.api_communication import ApiCommunication
from glpi_api_hero import ApiCommunication
# from glpi_api_hero.ticket import Ticket
# from glpi_api_hero import Ticket
import sys

# user = 'sp-andre.proto'
# passwd = 'sdsadasdasdad'
# url = 'https://betacentral.ibge.gov.br/apírest.php'
# apptoken = 'DSFdsfADSFADSgADFGFDSGDASFG'

# Dados de acesso da VM (local) do Leonardo.
user = 'glpi'
passwd = 'glpi'
url = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'

ApiCommunication.setConnectionParameters(url = url, apptolen=apptoken, user=user, passwd=passwd )
ApiCommunication.initSession()
print("Seção iniciada.")
ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)
ApiCommunication.killSession()
print("Seção finalizada.")

sys.exit()

# Exemplo de criação de chamado
input = {
    'name': 'Titulo do chamado',
    'content': 'Por favor resolver o meu problema',
    'itilcategories_id': '672',
    'type': 1,
    '_user_requester': 9407
}

result = Ticket.add(input)
#obter o ID do ticket
ticket_id = result['id']

# Enviando um acompanhamento
input = {
    'content': 'Favor esquecer o que eu pedi'
}

Ticket.addFollowUp(ticket_id, input)

