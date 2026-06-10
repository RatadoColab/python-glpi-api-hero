# Users e Groups

`User` e `Group` representam usuários e grupos do GLPI. Ambos herdam o CRUD de `CommonDBTM` e adicionam métodos para navegação de chamados e membros.

---

## User

### Constantes de tipo de ator

Usadas em qualquer contexto que exija identificar o papel de um usuário em um chamado:

| Constante | Valor | Papel no chamado |
|-----------|-------|-----------------|
| `User.REQUESTER` | `1` | Requerente (solicitante) |
| `User.ASSIGNED` | `2` | Técnico atribuído |
| `User.OBSERVER` | `3` | Observador |

### CRUD básico

```python
from glpi_api_hero import User

# Criar
result = User.add({
    'name': 'joao.silva',
    'realname': 'Silva',
    'firstname': 'João',
    'password': 'Senha@123',
    'password2': 'Senha@123',
    'email': 'joao.silva@exemplo.com',
    'profiles_id': 4,
    'entities_id': 111,
    'is_active': 1,
})
user_id = result[0]['id']

# Obter
usuario = User.get(user_id)

# Atualizar
User.update({'id': user_id, 'realname': 'Silva Pereira'})

# Deletar
User.delete([{'id': user_id}], force_purge=True)
```

### Métodos de busca

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getByUsername(username)` | `username`: login exato | Busca por login |
| `getByEmail(email)` | `email`: e-mail exato | Busca por e-mail |

```python
por_login = User.getByUsername('joao.silva')
por_email = User.getByEmail('joao.silva@exemplo.com')

# Busca geral (parcial)
resultado = User.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'silva'}]
)
```

### Perfis e grupos do usuário

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getAllProfiles(user_id, **kwargs)` | `user_id`: ID do usuário | Lista perfis vinculados |
| `getAllGroups(user_id, **kwargs)` | `user_id`: ID do usuário | Lista grupos do usuário |

```python
perfis = User.getAllProfiles(user_id)
grupos = User.getAllGroups(user_id)

# Sub-itens diretos via CommonDBTM
emails = User.get_sub_items(user_id, 'UserEmail')
```

### Chamados do usuário

`getAllTickets` retorna chamados filtrando pelo papel do usuário no chamado.

```python
# Chamados onde é requerente (padrão)
chamados = User.getAllTickets(user_id)

# Por papel específico
chamados = User.getAllTickets(user_id, actor_type=User.ASSIGNED)
chamados = User.getAllTickets(user_id, actor_type=User.OBSERVER)

# Com paginação
chamados = User.getAllTickets(user_id, actor_type=User.REQUESTER, range='0-9')
```

**Mapeamento interno de `actor_type` → campo de busca do GLPI:**

| actor_type | field | Descrição |
|-----------|-------|-----------|
| `REQUESTER` (1) | 4 | Requerente |
| `ASSIGNED` (2) | 5 | Atribuído a |
| `OBSERVER` (3) | 66 | Observador |

---

## Group

### Constantes de tipo de ator

Idênticas às de `User`, mas aplicadas a grupos:

| Constante | Valor | Papel no chamado |
|-----------|-------|-----------------|
| `Group.REQUESTER` | `1` | Grupo requerente |
| `Group.ASSIGNED` | `2` | Grupo atribuído (padrão em `getAllTickets`) |
| `Group.OBSERVER` | `3` | Grupo observador |

### CRUD básico

```python
from glpi_api_hero import Group

# Criar
result = Group.add({
    'name': 'N1 - Suporte',
    'comment': 'Primeiro nível de suporte.',
    'entities_id': 111,
    'is_recursive': 1,
    'is_assign': 1,     # pode ser atribuído em chamados
    'is_requester': 1,
    'is_watcher': 1,
})
group_id = result[0]['id']

# Obter
grupo = Group.get(group_id)

# Atualizar
Group.update({'id': group_id, 'comment': 'Atualizado.'})

# Deletar
Group.delete([{'id': group_id}], force_purge=True)
```

### Métodos de busca

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getByName(name, **kwargs)` | `name`: nome exato do grupo | Busca por nome |

```python
grupo = Group.getByName('N1 - Suporte')

# Busca geral
resultado = Group.search(
    criteria=[{'field': 1, 'searchtype': 'contains', 'value': 'Suporte'}]
)
```

### Gerenciamento de membros

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getAllUsers(group_id, **kwargs)` | `group_id`: ID do grupo | Lista membros (`Group_User`) |
| `addUser(group_id, user_id)` | IDs do grupo e do usuário | Adiciona membro |
| `deleteUser(group_id, user_id)` | IDs do grupo e do usuário | Remove membro |

`deleteUser` localiza o vínculo `Group_User` automaticamente — não é necessário saber o ID do vínculo.

```python
# Adicionar membro
Group.addUser(group_id, user_id)

# Listar membros
membros = Group.getAllUsers(group_id)

# Remover membro
Group.deleteUser(group_id, user_id)

# Sub-grupos filhos
sub_grupos = Group.get_sub_items(group_id, 'Group')
```

### Chamados do grupo

```python
# Chamados onde o grupo é atribuído (padrão)
chamados = Group.getAllTickets(group_id)

# Por papel específico
chamados = Group.getAllTickets(group_id, actor_type=Group.REQUESTER)
chamados = Group.getAllTickets(group_id, actor_type=Group.OBSERVER)

# Com paginação
chamados = Group.getAllTickets(group_id, actor_type=Group.ASSIGNED, range='0-9')
```

**Mapeamento interno de `actor_type` → campo de busca do GLPI:**

| actor_type | field | Descrição |
|-----------|-------|-----------|
| `REQUESTER` (1) | 71 | Grupo requerente |
| `ASSIGNED` (2) | 8 | Grupo atribuído |
| `OBSERVER` (3) | 65 | Grupo observador |
