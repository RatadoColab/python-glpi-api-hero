# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Instalar em modo de desenvolvimento
pip install -e .

# Gerar pacote de distribuição
pip install build && python -m build

# Subir o exemplo RabbitMQ com Docker (requer .env em examples/rabbitmq_sync)
cd examples/rabbitmq_sync && docker-compose up --build

# Executar producer/consumer standalone (requer .env)
cd examples/rabbitmq_sync && python producer.py
cd examples/rabbitmq_sync && python consumer.py
```

Não há suíte de testes automatizados. O diretório `examples/` contém exemplos de integração (mapeador de unidades organizacionais e sincronização via RabbitMQ) que podem ser executados manualmente contra uma instância GLPI real.

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

**Carga em lote em `Location`**: `addFromList()` e `updateFromList()` aceitam um `mapper` (função que converte um registro da fonte em campos de Location do GLPI) e, no upsert, um `key_field` (padrão `code`) usado como chave única. Sem `mapper`, os itens já devem usar os nomes de campo do GLPI. Exemplo de mapeador em `examples/org_units/mapper.py`.

## Exemplo de sincronização assíncrona (RabbitMQ)

Par producer/consumer em `examples/rabbitmq_sync/` para sincronizar registros com Locations do GLPI via RabbitMQ. Não faz parte do pacote instalado.

- **Producer**: lê um JSON (`SOURCE_JSON`) e publica uma mensagem por registro no exchange configurado.
- **Consumer**: recebe mensagens, chama `Location.updateFromList()` (com o mapeador definido em `ITEM_MAPPER`, formato `modulo:funcao`), trata erros de rate-limit 429 via fila de retry com TTL (`GLPI_RETRY_DELAY_MS`) e roteia falhas permanentes para uma DLQ.

Topologia (nomes padrão, configuráveis por `RABBITMQ_EXCHANGE`, `RABBITMQ_ROUTING_KEY` e `RABBITMQ_QUEUE`): exchange `glpi.locations` → fila `locations.update` → DLX `glpi.locations.dlx` → DLQ `locations.update.dlq` / fila retry `locations.update.retry`.

Copie `examples/rabbitmq_sync/.env.example` para `.env` e preencha as variáveis antes de executar.

## Classes stub

`ITILFollowup`, `ITILSolution`, `TicketValidation`, `Cluster` e `NetworkEquipment` são placeholders vazios que herdam `CommonDBTM`, marcados como `# To do` no código-fonte.
