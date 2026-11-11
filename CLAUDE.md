# CLAUDE.md

Este arquivo orienta o Claude Code (claude.ai/code) ao trabalhar neste repositório.

## Comandos

```bash
# Ambiente de desenvolvimento (Python >= 3.10)
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Testes (HTTP simulado, sem GLPI real) e lint
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests examples

# Pacote de distribuição
pip install build && python -m build

# Exemplo RabbitMQ (requer .env em examples/rabbitmq_sync)
cd examples/rabbitmq_sync && docker-compose up --build
```

Os testes unitários usam um simulador da API do GLPI 10 (`tests/conftest.py`). `tests/characterization/` fixa as
requisições HTTP e os retornos de cada método público (fixture em `tests/characterization/fixtures/`).

## Arquitetura

Pacote `glpi_api_hero` (distribuição `glpi-api-hero`), em camadas:

**1. Transporte e sessão — `core/`**
- `Connector` (`core/connector.py`): contrato entre os modelos e a API; `LegacyRestConnector` implementa a API REST do GLPI 10
  (`requests`, TLS verificado por padrão). Retornos normalizados: `add` → `int`, `update`/`delete` → `None`, `get` → `dict`,
  listas → `list[dict]`.
- `Glpi` (`core/session.py`): sessão global do processo (`Glpi.connect`/`disconnect`, context manager `Glpi.session`,
  `Glpi.set_profile_entity`, `Glpi.connector()`).
- `exceptions.py`: hierarquia a partir de `GlpiError`; erros do GLPI viram exceções específicas (`NotFoundError`, `RateLimitError`...).

**2. Base ORM — `core/`**
- `CommonDBTM`: CRUD genérico, busca e sub-itens. Todos os métodos são `classmethod` (modelos nunca são instanciados).
  `_glpi_name` só quando o itemtype difere do nome da classe.
- `CommonITILObject` (Ticket, Change, Problem), `CommonAsset`, `CommonTreeDropdown`, `GenericItem.of(itemtype)`.
- `core/capabilities.py`: mixins (`HasDocuments`, `HasInfocom`, `HasTickets`...) que dão os leitores de sub-itens. Cada classe combina
  só os mixins que o GLPI 10 permite para o itemtype (listas `$CFG_GLPI["<x>_types"]` de `inc/define.php`).

**3. Modelos por menu do GLPI**: `assets/`, `assistance/`, `management/`, `tools/`, `administration/`, `dropdowns/`, `components/`.
Sub-itens não têm classe pública: são métodos do pai (`Ticket.add_followup`, `Domain.get_records`...).

## Padrões importantes

- API pública em `snake_case`, com type hints e docstrings Google em inglês; comentários de linha com `#`, em inglês.
- Critérios de busca: `[{"field": <int>, "searchtype": "equals|contains|...", "value": <valor>}]`. Os ids de campo
  (`SEARCH_FIELD_*`) são constantes nomeadas conferidas no código do GLPI 10.
- Dicts recebidos nunca são alterados. Argumentos inválidos levantam `ValueError` antes de qualquer requisição.
- A API v1 filtra um sub-item pela coluna `<pai>s_id`, senão por `itemtype`+`items_id`; sem nenhuma das duas não filtra.
  Confira a tabela do sub-item antes de criar um leitor.
- `Location.add_from_list`/`update_from_list` aceitam `mapper` e `key_field` (exemplo em `examples/org_units/mapper.py`).
- Constantes de ator: `ActorType` (REQUESTER, ASSIGNED, OBSERVER), `ActorKind`, `LinkType` em `core/constants.py`.

## Exemplos (fora do pacote instalado)

`examples/org_units/` (mapeador), `examples/rabbitmq_sync/` (producer/consumer com retry por TTL e DLQ; copie `.env.example`
para `.env`) e `examples/ticket_dashboard/` (dashboard HTML/PNG, requer `plotly`).

## Documentação

`docs/` (inglês), um arquivo por subpacote, mais `migration.md`. Pendências abertas: ver `PENDING.md` na raiz, quando existir.
