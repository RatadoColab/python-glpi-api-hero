from dotenv import load_dotenv
load_dotenv()

from glpi_api_hero import ApiCommunication, Ticket, Computer
from glpi_api_hero import ResumeDashboard

# Configuração da conexão GLPI
url      = 'http://127.0.0.1:8080/api.php/v1'
apptoken = 'lzzWhduotvkyWFuNRMKgS4tYjAOjButzqhAwSoUs'
user     = 'glpi'
passwd   = 'glpi'

# Requer: ANTHROPIC_API_KEY no .env e plotly instalado
# pip install -e ".[dashboard]"

ApiCommunication.setConnectionParameters(url=url, apptoken=apptoken, user=user, passwd=passwd)
ApiCommunication.initSession()
ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)
print("Sessão iniciada.")

caminho = ResumeDashboard.generate_dashboard(
    panels=[
        {
            "titulo": "Chamados por Status",
            "query":  "todos os tickets agrupados por status",
            # "query":  "todos os tickets",
            "entity": Ticket,
        },
        {
            "titulo": "Chamados por Prioridade",
            "query":  "todos os tickets agrupados por prioridade",
            "entity": Ticket,
        },
        {
            "titulo": "Chamados por Tipo",
            "query":  "todos os tickets agrupados por tipo (incidente ou requisição)",
            "entity": Ticket,
        },
        {
            "titulo": "Computadores por Sistema Operacional",
            "query":  "computadores agrupados por sistema operacional",
            "entity": Computer,
        },
    ],
    # output_path="dashboard_glpi.png",
    output_path="dashboard_glpi.html",
    titulo="Dashboard GLPI — IBGE",
)

print(f"Dashboard gerado em: {caminho}")

ApiCommunication.killSession()
print("Sessão encerrada.")
