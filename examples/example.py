import glpi_api_hero.api_comunication
from glpi_api_hero.ticket import Ticket


user = 'sp-andre.proto'
passwd = 'sdsadasdasdad'
url = 'https://betacentral.ibge.gov.br/apírest.php'
apptoken = 'DSFdsfADSFADSgADFGFDSGDASFG'

ApiCommunication.setConnectionParameters(url = url, apptolen=apptoken, user=user, passwd=passwd );
ApiCommunication.initSession();

ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True);

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