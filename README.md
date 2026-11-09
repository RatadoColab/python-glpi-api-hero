# python-glpi-api-hero

Biblioteca Python para integração com a API do GLPI.

## Instalação

```bash
# Modo desenvolvimento
pip install -e .
```

Para gerar um pacote distribuível:

```bash
pip install build && python -m build
# Instalar em outra máquina:
pip install dist/arquivo.whl
```

## Documentação

| Documento | Classes | Descrição |
|-----------|---------|-----------|
| [docs/common_dbtm.md](docs/common_dbtm.md) | `CommonDBTM` | Classe base — CRUD genérico, busca e sub-itens herdados por todos os modelos |
| [docs/tickets.md](docs/tickets.md) | `Ticket` | Chamados — CRUD, acompanhamentos, soluções, validações, tarefas, ativos e vínculos |
| [docs/users-groups.md](docs/users-groups.md) | `User`, `Group` | Usuários e grupos — busca, membros e chamados associados |
| [docs/computers.md](docs/computers.md) | `Computer` | Computadores — inventário, hardware, software, rede e chamados vinculados |
| [docs/locations.md](docs/locations.md) | `Location` | Localizações — hierarquia, itens associados e criação/atualização em lote com mapeador configurável |
| [docs/sub-resources.md](docs/sub-resources.md) | `Actor`, `Item`, `Task`, `LinkedTicket`, `ITILFollowup`, `ITILSolution`, `TicketValidation`, `Cluster`, `NetworkEquipment` | Sub-recursos de chamados e classes stub (que não tem métodos próprios de domínio ainda) |
| [docs/ticket_dashboard.md](docs/ticket_dashboard.md) | `TicketDashboard` | Dashboard visual de chamados por período e categoria — gera dashboard no formato HTML ou imagem estática com KPIs e gráficos |

## Pré-requisito: sessão ativa

Todos os métodos exigem uma sessão GLPI inicializada antes de serem chamados:

```python
from glpi_api_hero import ApiCommunication

ApiCommunication.setConnectionParameters(
    url='URL_API_GLPI',
    apptoken='SEU_APP_TOKEN',
    user='login',
    passwd='senha',
)
ApiCommunication.initSession()
ApiCommunication.setProfileEntity(profiles_id=4, entities_id=111, is_recursive=True)

# ... Chamadas aos métodos ...

ApiCommunication.killSession()
```

## Exemplos

A pasta `examples/` traz exemplos de uso:

- `examples/org_units/`: mapeador que converte um JSON de unidades organizacionais em localizações do GLPI.
- `examples/rabbitmq_sync/`: par producer/consumer com RabbitMQ para sincronizar registros com Locations do GLPI de forma assíncrona, com tratamento de rate limit e fila de falhas.

```bash
cd examples/rabbitmq_sync
cp .env.example .env   # preencha as variáveis
docker-compose up --build
```
