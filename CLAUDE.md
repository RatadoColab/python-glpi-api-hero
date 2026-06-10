# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Instalar em modo de desenvolvimento
pip install -e .

# Gerar pacote de distribuição
pip install build && python -m build

# Subir microserviços com Docker
docker-compose up --build

# Executar producer standalone (requer .env)
cd microservices && python producer.py

# Executar consumer standalone (requer .env)
cd microservices && python consumer.py
```

Não há suíte de testes automatizados. O diretório `examples/` contém scripts de integração que podem ser executados manualmente contra uma instância GLPI real.

## Arquitetura

A biblioteca é organizada em três camadas:

**1. Camada de sessão — `ApiCommunication` (`api_communication.py`)**  
Singleton estático que gerencia o ciclo de vida da sessão GLPI. Deve ser inicializado antes de qualquer modelo ser usado:
```python
ApiCommunication.setConnectionParameters(url, apptoken, user_token=..., username=..., password=...)
ApiCommunication.initSession()
ApiCommunication.setProfileEntity(profiles_id, entities_id)
```
Todas as chamadas GLPI passam por `ApiCommunication.call()`, que mapeia `glpi_api.GLPIError` para exceções específicas do projeto.

**2. Base ORM — `CommonDBTM` (`common_dbtm.py`)**  
Classe base para todos os modelos de entidade. Fornece CRUD genérico (`add`, `update`, `delete`, `get`, `search`) e métodos de relacionamento (`get_sub_items`, `get_all_items`). Subclasses sobrescrevem `_glpi_name` quando o nome do itemtype no GLPI difere do nome da classe Python (ex: `Actor._glpi_name = "Ticket_User"`).

**3. Modelos de domínio (`ticket.py`, `user.py`, `computer.py`, `location.py`, `group.py`, …)**  
Classes de entidade que herdam de `CommonDBTM` e adicionam métodos específicos do domínio. Todos os métodos são classmethods — não há estado de instância.

## Padrões importantes

**Formato de critérios de busca** usado em todos os modelos:
```python
criteria = [{"field": <int>, "searchtype": "equals|contains|...", "value": <valor>}]
```

**Constantes de tipo de ator** (definidas em `user.py`): `REQUESTER = 1`, `ASSIGNED = 2`, `OBSERVER = 3`.

**Integração SDA** em `Location`: `_map_sda()` transforma JSON de unidades organizacionais do SDA em campos de Location do GLPI; `_dms_to_decimal()` converte coordenadas DMS para decimal. `COD_SIORG` é usado como chave única no upsert via `updateFromList()`.

## Microserviços (sincronização SDA → GLPI)

Par producer/consumer em `microservices/` para sincronização assíncrona de unidades organizacionais do SDA para Locations do GLPI via RabbitMQ.

- **Producer**: lê JSON do SDA, publica uma mensagem por unidade no exchange `ibge.endereco`.
- **Consumer**: recebe mensagens, chama `Location.updateFromList()`, trata erros de rate-limit 429 via fila de retry com TTL (`GLPI_RETRY_DELAY_MS`), e roteia falhas permanentes para uma DLQ.

Topologia RabbitMQ: exchange `ibge.endereco` → fila `atualizar_endereco` → DLX `ibge.endereco.dlx` → DLQ `atualizar_endereco.dlq` / fila retry `atualizar_endereco.retry`.

Copie `.env.example` para `.env` e preencha todas as variáveis antes de executar os microserviços.

## Consulta em linguagem natural — ResumeDashboard

`ResumeDashboard.search_natural(query, entity, **kwargs)` traduz uma consulta em português para critérios de busca GLPI usando a Claude API e executa o `search` na entidade informada.

```python
from glpi_api_hero import ResumeDashboard, Ticket, User, Computer

# Requer ANTHROPIC_API_KEY no ambiente
resultados = ResumeDashboard.search_natural(
    "chamados abertos de alta prioridade criados essa semana",
    Ticket
)
```

Entidades suportadas: `Ticket`, `User`, `Computer`, `Group`, `Location`, `Actor`, `Item`, `Task`, `ITILFollowup`, `ITILSolution`, `LinkedTicket`, `Cluster`, `NetworkEquipment`.

Para instalar com essa dependência: `pip install -e ".[ai]"`

## Classes stub

`ITILFollowup`, `ITILSolution`, `TicketValidation`, `Cluster` e `NetworkEquipment` são placeholders vazios que herdam `CommonDBTM`, marcados como `# To do` no código-fonte.
