# Computer

Gerencia computadores do inventário GLPI. Herda o CRUD completo de `CommonDBTM` e adiciona métodos de busca e consulta de sub-recursos de hardware, software, rede e chamados.

---

## CRUD básico

```python
from glpi_api_hero import Computer

# Criar
result = Computer.add({
    'name': 'PC-FINANCAS-01',
    'serial': 'SN-ABC123',
    'otherserial': 'PAT-2024-001',   # número de patrimônio
    'entities_id': 111,
    'comment': 'Desktop do setor financeiro.',
})
computer_id = result[0]['id']

# Obter
computador = Computer.get(computer_id)
print(computador['name'])

# Atualizar
Computer.update({'id': computer_id, 'comment': 'Atualizado.'})

# Deletar
Computer.delete([{'id': computer_id}], force_purge=True)

# Listar (paginado)
todos = Computer.get_all_items(range='0-49')
```

---

## Busca

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `getByName(name, **kwargs)` | `name`: nome (busca parcial) | Busca por nome |
| `getBySerial(serial, **kwargs)` | `serial`: número de série exato | Busca por serial |
| `getByPatrimonio(otherserial, **kwargs)` | `otherserial`: número de patrimônio exato | Busca por patrimônio |

```python
# Por nome (busca parcial — usa "contains")
resultados = Computer.getByName('PC-FINANCAS')

# Por número de série (exato)
resultados = Computer.getBySerial('SN-ABC123')

# Por número de patrimônio (exato)
resultados = Computer.getByPatrimonio('PAT-2024-001')

# Busca avançada
resultado = Computer.search(
    criteria=[
        {'field': 1, 'searchtype': 'contains', 'value': 'PC-'},
        {'field': 3, 'searchtype': 'equals',   'value': 5},   # locations_id = 5
    ],
    range='0-29',
)
```

**Campos comuns de Computer para busca:**

| field | Descrição |
|-------|-----------|
| `1` | Nome |
| `2` | ID |
| `3` | Localização |
| `5` | Número de série |
| `6` | Número de patrimônio (`otherserial`) |

---

## Sistema operacional

```python
so = Computer.getOperatingSystem(computer_id)
# Retorna registros Item_OperatingSystem
```

---

## Softwares instalados

```python
softwares = Computer.getSoftwares(computer_id)
# Retorna registros Item_SoftwareVersion
```

---

## Rede

```python
portas = Computer.getNetworkPorts(computer_id)
# Retorna registros NetworkPort (IP, MAC, interface)
```

---

## Hardware

| Método | Sub-itemtype | Descrição |
|--------|-------------|-----------|
| `getProcessors(computer_id)` | `Item_DeviceProcessor` | Processadores |
| `getMemories(computer_id)` | `Item_DeviceMemory` | Módulos de memória RAM |
| `getDisks(computer_id)` | `ComputerDisk` | Volumes e partições |
| `getHardDrives(computer_id)` | `Item_DeviceHardDrive` | Discos rígidos e SSDs |

```python
processadores = Computer.getProcessors(computer_id)
memorias      = Computer.getMemories(computer_id)
volumes       = Computer.getDisks(computer_id)
discos        = Computer.getHardDrives(computer_id)
```

---

## Máquinas virtuais

Quando o computador é um host de virtualização:

```python
vms = Computer.getVirtualMachines(computer_id)
# Retorna registros ComputerVirtualMachine
```

---

## Chamados vinculados

```python
# Todos os chamados onde o computador é ativo vinculado
chamados = Computer.getTickets(computer_id)

# Com paginação
chamados = Computer.getTickets(computer_id, range='0-9')
```

O método busca via campo `131` (item vinculado ao chamado) na pesquisa de `Ticket`.

---

## Informações financeiras e de garantia

```python
infocom = Computer.getInfocom(computer_id)
# Retorna registro Infocom: data de compra, garantia, fornecedor, valor, etc.
```

---

## Histórico de alterações

```python
logs = Computer.getLogs(computer_id)
# Retorna registros Log com todas as modificações do computador
```

---

## Referência de métodos

| Método | Descrição |
|--------|-----------|
| `getByName(name)` | Busca por nome (parcial) |
| `getBySerial(serial)` | Busca por número de série |
| `getByPatrimonio(otherserial)` | Busca por patrimônio |
| `getOperatingSystem(computer_id)` | Sistema operacional instalado |
| `getSoftwares(computer_id)` | Softwares instalados |
| `getNetworkPorts(computer_id)` | Portas de rede |
| `getProcessors(computer_id)` | Processadores |
| `getMemories(computer_id)` | Módulos de memória RAM |
| `getDisks(computer_id)` | Volumes e partições |
| `getHardDrives(computer_id)` | Discos rígidos/SSDs |
| `getVirtualMachines(computer_id)` | Máquinas virtuais hospedadas |
| `getTickets(computer_id)` | Chamados vinculados |
| `getInfocom(computer_id)` | Dados financeiros e de garantia |
| `getLogs(computer_id)` | Histórico de alterações |
