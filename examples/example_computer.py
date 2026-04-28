from glpi_api_hero import ApiCommunication
from glpi_api_hero import Computer
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
# Computer: métodos herdados de CommonDBTM
# ==============================================================

# Criar computador
novo_computador = {
    'name': 'PC-TESTE-' + data_string,
    'serial': 'SN-' + data_string,
    'otherserial': 'PAT-' + data_string,
    'entities_id': 111,
    'comment': 'Computador criado para testes automatizados.',
}
result = Computer.add(novo_computador)
computer_id = result[0]['id']
print("Computador criado. ID:", computer_id)
sys.exit()

# Obter computador pelo ID
computador = Computer.get(computer_id)
print("Computador obtido:", computador.get('name'))

# Atualizar computador
Computer.update({'id': computer_id, 'comment': 'Comentário atualizado.'})
print("Computador atualizado.")

# Listar todos os computadores (primeiros 10)
todos = Computer.get_all_items(range='0-9')
print("Computadores retornados:", len(todos))

# Busca geral via search
resultado_busca = Computer.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'PC-TESTE'}]
)
print("Busca realizada.")

# ==============================================================
# Busca por nome, serial e patrimônio
# ==============================================================

# Buscar computador pelo nome
por_nome = Computer.getByName('PC-TESTE')
print("Busca por nome:", por_nome)

# Buscar computador pelo número de série
por_serial = Computer.getBySerial('SN-' + data_string)
print("Busca por serial:", por_serial)

# Buscar computador pelo número de patrimônio
por_patrimonio = Computer.getByPatrimonio('PAT-' + data_string)
print("Busca por patrimônio:", por_patrimonio)

# ==============================================================
# Sistema operacional
# ==============================================================

# Obter sistema operacional instalado
so = Computer.getOperatingSystem(computer_id)
print("Sistema operacional:", so)

# ==============================================================
# Softwares instalados
# ==============================================================

# Listar softwares instalados
softwares = Computer.getSoftwares(computer_id)
print("Softwares instalados:", softwares)

# ==============================================================
# Rede
# ==============================================================

# Listar portas de rede
portas = Computer.getNetworkPorts(computer_id)
print("Portas de rede:", portas)

# ==============================================================
# Hardware
# ==============================================================

# Listar processadores
processadores = Computer.getProcessors(computer_id)
print("Processadores:", processadores)

# Listar módulos de memória RAM
memorias = Computer.getMemories(computer_id)
print("Memórias:", memorias)

# Listar volumes/partições
volumes = Computer.getDisks(computer_id)
print("Volumes:", volumes)

# Listar discos rígidos/SSDs
hds = Computer.getHardDrives(computer_id)
print("Discos rígidos:", hds)

# ==============================================================
# Máquinas virtuais
# ==============================================================

# Listar VMs hospedadas no computador (quando é um host)
vms = Computer.getVirtualMachines(computer_id)
print("Máquinas virtuais:", vms)

# ==============================================================
# Chamados vinculados ao computador
# ==============================================================

# Listar chamados onde o computador é ativo vinculado
chamados = Computer.getTickets(computer_id)
print("Chamados vinculados:", chamados)

# Com paginação: primeiros 5 chamados
chamados_paginados = Computer.getTickets(computer_id, range='0-4')
print("Chamados paginados:", chamados_paginados)

# ==============================================================
# Informações financeiras e de garantia
# ==============================================================

# Obter infocom (compra, garantia, fornecedor)
infocom = Computer.getInfocom(computer_id)
print("Infocom:", infocom)

# ==============================================================
# Histórico de alterações
# ==============================================================

# Obter logs de mudanças do computador
logs = Computer.getLogs(computer_id)
print("Logs:", logs)

# ==============================================================
# Sub-itens via get_sub_items (CommonDBTM)
# ==============================================================

# Documentos vinculados
documentos = Computer.get_sub_items(computer_id, 'Document_Item')
print("Documentos:", documentos)

# ==============================================================
# Deletar computador criado no teste
# ==============================================================

Computer.delete([{'id': computer_id}], force_purge=True)
print("Computador deletado.")

ApiCommunication.killSession()
print("Sessão finalizada.")
