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
| [docs/locations.md](docs/locations.md) | `Location` | Localizações — hierarquia, itens associados e integração com o catálogo SDA |
| [docs/sub-resources.md](docs/sub-resources.md) | `Actor`, `Item`, `Task`, `LinkedTicket`, `ITILFollowup`, `ITILSolution`, `TicketValidation`, `Cluster`, `NetworkEquipment` | Sub-recursos de chamados e classes stub (que não tem métodos próprios de domínio ainda) |

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

## Microserviços

Par producer/consumer em `microservices/` para sincronização assíncrona de unidades organizacionais do SDA para Locations do GLPI via RabbitMQ.

```bash
# Subir com Docker
docker-compose up --build

# Executar standalone (requer .env)
cd microservices && python producer.py
cd microservices && python consumer.py
```

Preencha as variáveis no arquivo `.env` antes de executar.
