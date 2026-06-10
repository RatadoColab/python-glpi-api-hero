# Location

Gerencia localizações físicas no GLPI (prédios, salas, andares, etc.). Suporta hierarquia pai/filho e integração direta com o catálogo SDA de unidades organizacionais.

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
    'code': 123456,          # COD_SIORG ou outro código externo
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
| `getByCode(code, **kwargs)` | `code`: código exato (COD_SIORG) | Busca por código externo |
| `getByCompleteName(complete_name, **kwargs)` | `complete_name`: caminho hierárquico | Busca por nome completo |

```python
# Busca parcial por nome
resultados = Location.getByName('Rio')

# Busca exata por código (chave SDA)
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

## Histórico de alterações

```python
logs = Location.getLogs(location_id)
```

---

