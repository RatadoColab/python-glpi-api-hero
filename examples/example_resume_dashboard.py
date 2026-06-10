from dotenv import load_dotenv
load_dotenv()

from glpi_api_hero import ApiCommunication, Ticket, User, Computer, Group, Location
from glpi_api_hero import ResumeDashboard
import sys

# Configuração da conexão GLPI
url      = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'
user     = 'glpi'
passwd   = 'glpi'

ApiCommunication.setConnectionParameters(url=url, apptoken=apptoken, user=user, passwd=passwd)
ApiCommunication.initSession()
ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)
print("Sessão iniciada.\n")

# ==============================================================
# Location — consultas em linguagem natural
# ==============================================================

# print("\n--- Localizações no Rio de Janeiro ---")
# resultado = ResumeDashboard.search_natural(
#     # "localizações com nome completo contendo Rio de Janeiro",
#     # "localizações com nome contendo Colatina",
#     "todas as localizações",
#     # "contador com o número de localizações",
#     Location
# )
# print(resultado)
# sys.exit()

# ==============================================================
# Ticket — consultas em linguagem natural
# ==============================================================

print("--- Tickets criados em 2026 ---")
resultado = ResumeDashboard.search_natural(
    "todos os tickets criados em 2026",
    Ticket
)
print(resultado)
sys.exit()

print("\n--- Chamados abertos de alta prioridade ---")
resultado = ResumeDashboard.search_natural(
    "chamados abertos com prioridade alta ou muito alta",
    Ticket
)
print(resultado)

print("\n--- Incidentes pendentes ---")
resultado = ResumeDashboard.search_natural(
    "incidentes com status pendente",
    Ticket
)
print(resultado)

print("\n--- Requisições resolvidas essa semana ---")
resultado = ResumeDashboard.search_natural(
    "requisições resolvidas após 2026-05-26",
    Ticket
)
print(resultado)

# ==============================================================
# User — consultas em linguagem natural
# ==============================================================

print("\n--- Usuário pelo nome ---")
resultado = ResumeDashboard.search_natural(
    "usuários com sobrenome Silva",
    User
)
print(resultado)

print("\n--- Usuário pelo e-mail ---")
resultado = ResumeDashboard.search_natural(
    "usuário com e-mail contendo @ibge.gov.br",
    User
)
print(resultado)

# ==============================================================
# Computer — consultas em linguagem natural
# ==============================================================

print("\n--- Computadores por localização ---")
resultado = ResumeDashboard.search_natural(
    "computadores na localização 42",
    Computer
)
print(resultado)

print("\n--- Equipamentos com Windows ---")
resultado = ResumeDashboard.search_natural(
    "equipamentos com sistema operacional Windows",
    Computer
)
print(resultado)

# ==============================================================
# Group — consultas em linguagem natural
# ==============================================================

print("\n--- Grupos de infraestrutura ---")
resultado = ResumeDashboard.search_natural(
    "grupos cujo nome contém infraestrutura",
    Group
)
print(resultado)

# ==============================================================
# Encerramento
# ==============================================================

ApiCommunication.killSession()
print("\nSessão encerrada.")
