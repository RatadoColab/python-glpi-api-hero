# CommonDBTM

Classe base que possui métodos genéricos que podem ser herdados pelas demais classes da biblioteca.

---

## Métodos CRUD

### `add(*items)`

Cria um ou mais registros no GLPI.

```python
# Um registro
result = Ticket.add({'name': 'Problema na impressora', 'content': '...', 'type': 1})
novo_id = result[0]['id']

# Múltiplos registros de uma vez
result = Location.add(
    {'name': 'Sala 101', 'locations_id': 5, 'entities_id': 0},
    {'name': 'Sala 102', 'locations_id': 5, 'entities_id': 0},
)
```

### `update(*items)`

Atualiza um ou mais registros. O campo `id` é obrigatório em cada item.

```python
Ticket.update({'id': 42, 'priority': 5})

# Múltiplos de uma vez
User.update(
    {'id': 10, 'realname': 'João Silva'},
    {'id': 11, 'realname': 'Maria Santos'},
)
```

### `delete(*items, **kwargs)`

Remove um ou mais registros. Passe `force_purge=True` para excluir permanentemente sem mover para a lixeira.

```python
Ticket.delete([{'id': 42}])
Computer.delete([{'id': 7}], force_purge=True)
```

### `get(items_id, **kwargs)`

Retorna um registro pelo ID.

```python
chamado = Ticket.get(42)
print(chamado['name'])
```

### `get_all_items(**kwargs)`

Retorna todos os registros do itemtype. Suporta paginação via `range`.

```python
# Primeiros 50 chamados
chamados = Ticket.get_all_items(range='0-49')

# Todos os computadores (até 10 000)
computadores = Computer.get_all_items(range='0-9999')
```

---

## Busca

### `search(**kwargs)`

Busca registros usando critérios estruturados.

```python
resultado = Ticket.search(
    criteria=[
        {'field': 1, 'searchtype': 'contains', 'value': 'rede'},
        {'field': 12, 'searchtype': 'equals',   'value': 1},
    ],
    range='0-29',
)
```

**Formato de critérios:**

```python
criteria = [
    {
        'field':      <int>,       # ID do campo de busca
        'searchtype': 'equals'     # equals | contains | notequals | lessthan | morethan | under | notunder
                    | 'contains',
        'value':      <valor>,
    }
]
```

Para descobrir o `field` correto de um itemtype, use `list_search_options`.

### `list_search_options(items_id, raw=False)`

Retorna os campos de busca disponíveis para o itemtype, com seus IDs.

```python
opcoes = Ticket.list_search_options(1)   # qualquer ID de chamado existente
```

---

## Sub-itens e relacionamentos

### `get_sub_items(items_id, sub_itemtype, **kwargs)`

Retorna os sub-recursos vinculados a um registro.

```python
followups   = Ticket.get_sub_items(42, 'ITILFollowup')
softwares   = Computer.get_sub_items(7,  'Item_SoftwareVersion')
membros     = Group.get_sub_items(3,  'Group_User')
documentos  = Computer.get_sub_items(7,  'Document_Item')
```

---

## Referência de métodos

| Método | Assinatura | Descrição |
|--------|-----------|-----------|
| `add` | `add(*items)` | Cria registros |
| `update` | `update(*items)` | Atualiza registros (requer `id`) |
| `delete` | `delete(*items, **kwargs)` | Remove registros |
| `get` | `get(items_id, **kwargs)` | Obtém registro por ID |
| `get_all_items` | `get_all_items(**kwargs)` | Lista todos os registros |
| `search` | `search(**kwargs)` | Busca com critérios |
| `get_sub_items` | `get_sub_items(items_id, sub_itemtype, **kwargs)` | Lista sub-recursos vinculados |
| `list_search_options` | `list_search_options(items_id, raw=False)` | Descobre campos de busca disponíveis |
| `get_class_name` | `get_class_name()` | Retorna o itemtype usado nas chamadas à API |
