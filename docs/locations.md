# Location

Gerencia localizações físicas no GLPI (prédios, salas, andares, etc.). Suporta hierarquia pai/filho e criação/atualização em lote a partir de qualquer fonte de dados, por meio de um mapeador configurável.

---

## CRUD básico

```python
from glpi_api_hero import Location

# Criar localização simples
result = Location.add({
    'name': 'Sede Rio de Janeiro',
    'address': 'Av. Franklin Roosevelt, 166',
    'building': 'Centro',
    'postcode': '20021-120',
    'town': 'Rio de Janeiro',
    'state': 'RJ',
    'code': 123456,          # código externo (chave de integração)
    'entities_id': 0,
})
location_id = result[0]['id']

# Criar sub-localização (filha)
result_sub = Location.add({
    'name': 'Bloco A',
    'locations_id': location_id,   # pai
    'entities_id': 0,
})

# Criar múltiplas de uma vez
Location.add(
    {'name': 'Sala 101', 'locations_id': location_id, 'entities_id': 0},
    {'name': 'Sala 102', 'locations_id': location_id, 'entities_id': 0},
)

# Obter
loc = Location.get(location_id)

# Atualizar
Location.update({'id': location_id, 'comment': 'Atualizado.'})

# Deletar
Location.delete([{'id': location_id}], force_purge=True)
```

---

## Busca

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getByName(name, **kwargs)` | `name`: nome parcial | Busca por nome (parcial) |
| `getByCode(code, **kwargs)` | `code`: código exato | Busca por código externo |
| `getByCompleteName(complete_name, **kwargs)` | `complete_name`: caminho hierárquico | Busca por nome completo |

```python
# Busca parcial por nome
resultados = Location.getByName('Rio')

# Busca exata por código externo
resultado = Location.getByCode(123456)

# Busca pelo caminho hierárquico (ex: "Sede > Bloco A > Sala 101")
resultado = Location.getByCompleteName('Sede Rio de Janeiro > Bloco A')

# Busca avançada
resultado = Location.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'Sala'}]
)
```

---

## Hierarquia

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getChildren(location_id, **kwargs)` | `location_id`: ID do pai | Filhos diretos |
| `getRoots(**kwargs)` | — | Localizações raiz (sem pai) |

```python
# Sub-localizações diretas de uma localização
filhos = Location.getChildren(location_id)

# Todas as localizações raiz
raizes = Location.getRoots()
```

---

## Itens na localização

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getComputers(location_id, **kwargs)` | `location_id` | Computadores na localização |
| `getNetworkEquipments(location_id, **kwargs)` | `location_id` | Equipamentos de rede |
| `getTickets(location_id, **kwargs)` | `location_id` | Chamados abertos na localização |
| `getUsers(location_id, **kwargs)` | `location_id` | Usuários com essa localização cadastrada |

```python
computadores  = Location.getComputers(location_id)
equipamentos  = Location.getNetworkEquipments(location_id)
chamados      = Location.getTickets(location_id)
usuarios      = Location.getUsers(location_id)
```

---

## Criação e atualização em lote

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addFromList(items, locations_id=0, entities_id=0, *, mapper=None)` | `items`: registros; `mapper`: função de conversão | Cria várias localizações |
| `updateFromList(items, locations_id=0, entities_id=0, *, mapper=None, key_field='code')` | `key_field`: campo GLPI usado como chave | Atualiza as existentes (chave, depois nome) e cria as ausentes |

Sem `mapper`, cada item deve já usar os nomes de campo do GLPI. Com `mapper`, a função recebe um registro da fonte e devolve um dicionário de campos do GLPI.

```python
def meu_mapper(registro: dict) -> dict:
    return {
        'name': registro['nome'],
        'code': registro['codigo'],
        'town': registro['cidade'],
    }

# Upsert usando 'code' como chave única
Location.updateFromList(registros, mapper=meu_mapper, key_field='code')

# Registros já no formato do GLPI
Location.addFromList([{'name': 'Sala 101'}, {'name': 'Sala 102'}], locations_id=location_id)
```

Um mapeador completo de exemplo está em `examples/org_units/mapper.py`.

---

## Histórico de alterações

```python
logs = Location.getLogs(location_id)
```

---

