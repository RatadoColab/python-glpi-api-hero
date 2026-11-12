# Ticket dashboard example

Builds a visual report of GLPI tickets by period and ITIL category: KPI cards (total, closed, solved, open,
SLA due today, SLA overdue), a stacked horizontal bar chart, a donut chart and a detail table.
It is an example, not part of the installed package.

## Run

```bash
pip install -r examples/ticket_dashboard/requirements.txt
```

```python
from examples.ticket_dashboard.ticket_dashboard import TicketDashboard
from glpi_api_hero import Glpi

with Glpi.session(url, app_token, user_token=token):
    path = TicketDashboard.generate(
        date_from="2024-04-24",
        date_to="2024-05-14",
        categories={"Infrastructure": 3, "Systems": 5, "Support": 7},
        output_path="dashboard.html",
        titulo="IT",
    )
```

Static PNG/SVG output needs `kaleido`. SLA metrics use the Ticket search option `time_to_resolve` (id 18 in
GLPI 10); override `TicketDashboard.FIELD_PRAZO` if your instance differs.
