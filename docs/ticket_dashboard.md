# TicketDashboard

A classe `TicketDashboard` gera um dashboard visual de chamados GLPI para um período e conjunto de categorias ITIL definidos.

O resultado é um arquivo HTML interativo (padrão) ou uma imagem estática (PNG/SVG/PDF), contendo:

- **6 cards de KPIs**: total de chamados, fechados, solucionados, abertos, SLA vencendo hoje e SLA vencido
- **Gráfico de barras horizontais empilhadas** com a distribuição de status por categoria
- **Gráfico de rosca** com a participação percentual de cada categoria no total
- **Tabela detalhada** por categoria com todas as métricas

## Instalação das dependências

```bash
# Dependência obrigatória (para HTML interativo)
pip install plotly

# Dependência adicional (para exportar PNG/SVG/PDF)
pip install kaleido
```

---

## Métodos públicos

### `generate`

Método principal. Coleta os dados do GLPI e gera o arquivo de saída.

```python
TicketDashboard.generate(
    date_from,
    date_to,
    categories=None,
    output_path="dashboard_glpi.html",
    titulo="DTI",
    data=None,
) -> str
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_from` | str | Data inicial no formato `YYYY-MM-DD` (inclusive). |
| `date_to` | str | Data final no formato `YYYY-MM-DD` (inclusive). |
| `categories` | dict \| None | Mapeamento `{nome_exibido: glpi_itilcategory_id}`. Se `None`, exibe apenas totais globais. |
| `output_path` | str | Caminho do arquivo de saída. A extensão determina o formato: `.html` (interativo, padrão) ou `.png`/`.svg`/`.pdf` (estático, requer `kaleido`). |
| `titulo` | str | Título exibido no cabeçalho do dashboard. |
| `data` | dict \| None | Dados pré-coletados (saída de `collect_data`). Se informado, pula a consulta à API. |

**Retorna:** caminho absoluto do arquivo gerado (`str`).

**Exceções:**
- `ImportError` — se `plotly` não estiver instalado.
- `ImportError` — se `kaleido` não estiver instalado ao exportar imagem.

#### Exemplo básico

```python
from glpi_api_hero import ApiCommunication
from glpi_api_hero.ticket_dashboard import TicketDashboard

ApiCommunication.setConnectionParameters(url, apptoken, user_token=token)
ApiCommunication.initSession()

caminho = TicketDashboard.generate(
    date_from="2026-04-24",
    date_to="2026-06-25",
    categories={"Infraestrutura": 1, "Hardware": 2, "Software": 3},
    output_path="dashboard_dti.html",
    titulo="DTI",
)
print(f"Dashboard gerado em: {caminho}")
```

#### Exemplo — exportar como imagem

```python
caminho = TicketDashboard.generate(
    date_from="2026-04-24",
    date_to="2026-06-25",
    categories={"Infraestrutura": 1, "Hardware": 2},
    output_path="dashboard_dti.png",
    titulo="DTI",
)
```

---

### `collect_data`

Coleta as métricas do GLPI sem gerar o arquivo. Útil para inspecionar os dados ou reutilizá-los em múltiplas chamadas a `generate` sem repetir as consultas à API.

```python
TicketDashboard.collect_data(
    date_from,
    date_to,
    categories=None,
) -> dict
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_from` | str | Data inicial `YYYY-MM-DD`. |
| `date_to` | str | Data final `YYYY-MM-DD`. |
| `categories` | dict \| None | Mapeamento `{nome: cat_id}`. Se `None`, retorna apenas totais globais. |

**Retorna:** dicionário com as métricas globais e, se `categories` for informado, um dicionário aninhado por categoria:

```python
{
    "total":        int,
    "fechados":     int,
    "solucionados": int,
    "abertos":      int,
    "sla_hoje":     int,
    "sla_vencido":  int,
    "categorias": {
        "Infraestrutura": {"total": int, "fechados": int, ...},
        "Hardware":        {"total": int, "fechados": int, ...},
    }
}
```

#### Exemplo — separar coleta e geração

```python
# Coleta uma única vez
dados = TicketDashboard.collect_data(
    date_from="2026-04-24",
    date_to="2026-06-25",
    categories={"Infraestrutura": 1, "Hardware": 2},
)

print(f"Total: {dados['total']} | Abertos: {dados['abertos']}")

for categoria, m in dados["categorias"].items():
    print(f"  {categoria}: total={m['total']}  sla_vencido={m['sla_vencido']}")

# Gera HTML reutilizando os dados já coletados (sem novas chamadas à API)
TicketDashboard.generate(
    date_from="2026-04-24",
    date_to="2026-06-25",
    output_path="dashboard_dti.html",
    titulo="DTI",
    data=dados,
)
```

---

### `diagnose`

Imprime no terminal as URLs de cada consulta e os totais retornados. Útil para verificar se os `field_id` e critérios estão corretos para a sua instância GLPI.

```python
TicketDashboard.diagnose(date_from, date_to, cat_id=None) -> None
```

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `date_from` | str | Data inicial `YYYY-MM-DD`. |
| `date_to` | str | Data final `YYYY-MM-DD`. |
| `cat_id` | int \| None | ID de categoria ITIL para filtrar (opcional). |

#### Exemplo

```python
# Diagnóstico global
TicketDashboard.diagnose("2026-04-24", "2026-06-25")

# Diagnóstico para uma categoria específica
TicketDashboard.diagnose("2026-04-24", "2026-06-25", cat_id=3)
```

Saída esperada:

```
============================================================
  DIAGNOSE TicketDashboard  |  2026-04-24 a 2026-06-25
============================================================
  total          | HTTP 200 | totalcount=128
               URL: http://.../apirest.php/search/Ticket?...
  fechados       | HTTP 200 | totalcount=47
  ...
============================================================
```

---

## Constantes

### Status de chamado

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `STATUS_NOVO` | `1` | Novo |
| `STATUS_ATRIB` | `2` | Atribuído |
| `STATUS_PLANEJ` | `3` | Planejado |
| `STATUS_PEND` | `4` | Pendente |
| `STATUS_RESOLVIDO` | `5` | Resolvido |
| `STATUS_FECHADO` | `6` | Fechado |

### Field IDs padrão

| Constante | Valor | Campo GLPI |
|-----------|-------|------------|
| `FIELD_STATUS` | `12` | Status do chamado |
| `FIELD_CATEGORIA` | `7` | `itilcategories_id` |
| `FIELD_ABERTURA` | `15` | Data de abertura |
| `FIELD_PRAZO` | `155` | `time_to_resolve` — usado para cálculo do SLA |

---

## Personalizar o field ID do SLA

O cálculo de SLA utiliza `FIELD_PRAZO = 155` (`time_to_resolve`). Se a sua instância GLPI usar um campo diferente, sobrescreva o atributo antes de chamar qualquer método:

```python
TicketDashboard.FIELD_PRAZO = 180  # substitua pelo field_id correto
```

Use `diagnose` para confirmar que o campo está retornando os valores esperados após a alteração.
