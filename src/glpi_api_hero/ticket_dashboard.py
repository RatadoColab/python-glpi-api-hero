import os
from datetime import date
from datetime import datetime
from typing import Optional

from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.api_communication import ApiCommunication

class TicketDashboard(CommonDBTM):
    """Dashboard visual de chamados GLPI por período e categoria ITIL.

    Gera um arquivo HTML interativo (ou PNG/SVG estático) com:
    - 6 cards de KPIs: total, fechados, solucionados, abertos, SLA hoje, SLA vencido
    - Gráfico de barras horizontais empilhadas por categoria
    - Gráfico de rosca com distribuição percentual por categoria
    - Tabela detalhada por categoria

    Exemplo:

        from glpi_api_hero import ApiCommunication
        from glpi_api_hero.ticket_dashboard import TicketDashboard

        ApiCommunication.setConnectionParameters(url, apptoken, user_token=token)
        ApiCommunication.initSession()

        caminho = TicketDashboard.generate(
            date_from="2024-04-24",
            date_to="2024-05-14",
            categories={"Infraestrutura": 3, "Sistemas": 5, "Suporte": 7},
            output_path="dashboard_dti.html",
            titulo="DTI",
        )
        print(f"Dashboard gerado em: {caminho}")

    Nota sobre SLA:
        Os campos de SLA usam ``FIELD_PRAZO = 155`` (time_to_resolve).
        Sobrescreva este atributo de classe se seu GLPI usar um field_id diferente.
    """

    _glpi_name = "Ticket"

    # Códigos dos Status de Tickets do GLPI.
    STATUS_NOVO      = 1
    STATUS_ATRIB     = 2
    STATUS_PLANEJ    = 3
    STATUS_PEND      = 4
    STATUS_RESOLVIDO = 5
    STATUS_FECHADO   = 6

    # Field IDs padrão do GLPI para Ticket.
    FIELD_STATUS    = 12
    FIELD_CATEGORIA = 7    # itilcategories_id
    FIELD_ABERTURA  = 15
    FIELD_PRAZO     = 155  # time_to_resolve — usado para cálculo do SLA.

    _CARD_COLORS = ["#1a6b3c", "#1c2e4a", "#4a3080", "#1a7dc4", "#c48a00", "#c94040"]

    _BAR_COLORS = {
        "fechados":     "#1c2e4a",
        "solucionados": "#4a3080",
        "abertos":      "#1a7dc4",
        "sla_hoje":     "#f0b429",
        "sla_vencido":  "#e05c5c",
    }

    _PIE_PALETTE = [
        "#4a9fd4", "#e07c3a", "#1a3a5c",
        "#5b4ea0", "#e05c5c", "#8c8c8c", "#f0b429",
    ]

    # ------------------------------------------------------------------
    # Helpers de consulta GLPI
    # ------------------------------------------------------------------

    @classmethod
    def _count(cls, criteria: list) -> int:
        # glpi_api.search() descarta totalcount e retorna apenas data[].
        # Acessa o JSON bruto para ler totalcount antes do descarte.
        glpi   = ApiCommunication.glpi
        params = glpi._add_criteria(criteria, cls._itemtype())
        params["range"] = "0-0"
        response = glpi.session.get(
            glpi._set_method("search", cls._itemtype()),
            params=params,
        )
        if response.status_code in (200, 206):
            return int(response.json().get("totalcount", 0))
        return 0

    @classmethod
    def _base(cls, date_from: str, date_to: str, cat_id: int = None) -> list:
        """Critérios de busca."""
        crit = [
            {"field": cls.FIELD_ABERTURA, "searchtype": "morethan", "value": date_from},
            {"field": cls.FIELD_ABERTURA, "searchtype": "lessthan",  "value": date_to,  "link": "AND"},
        ]
        if cat_id is not None:
            crit.append(
                {"field": cls.FIELD_CATEGORIA, "searchtype": "equals", "value": cat_id, "link": "AND"}
            )
        return crit

    @classmethod
    def _base_sla(cls, cat_id: int = None) -> list:
        """Critérios base para SLA: sem filtro de data de abertura.

        SLA vencido/hoje considera todos os tickets, independente de quando
        foram criados.
        """
        if cat_id is not None:
            return [{"field": cls.FIELD_CATEGORIA, "searchtype": "equals", "value": cat_id}]
        return []

    @classmethod
    def _crit_status(cls, status: int) -> list:
        return [{"field": cls.FIELD_STATUS, "searchtype": "equals", "value": status, "link": "AND"}]

    @classmethod
    def _crit_sla_vencido(cls) -> list:
        # SLA vencido = prazo passou, independente de status (aberto, fechado ou resolvido).
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            {"field": cls.FIELD_PRAZO, "searchtype": "lessthan", "value": today, "link": "AND"},
        ]

    @classmethod
    def _crit_sla_hoje(cls) -> list:
        hoje   = date.today()
        inicio = f"{hoje} 00:00:00"
        fim    = f"{hoje} 23:59:59"
        return [
            {"field": cls.FIELD_STATUS, "searchtype": "notequals", "value": cls.STATUS_RESOLVIDO, "link": "AND"},
            {"field": cls.FIELD_STATUS, "searchtype": "notequals", "value": cls.STATUS_FECHADO,   "link": "AND"},
            {"field": cls.FIELD_PRAZO,  "searchtype": "morethan",  "value": inicio,              "link": "AND"},
            {"field": cls.FIELD_PRAZO,  "searchtype": "lessthan",  "value": fim,                 "link": "AND"},
        ]

    @classmethod
    def diagnose(cls, date_from: str, date_to: str, cat_id: int = None) -> None:
        """Imprime as URLs e totais de cada consulta para depuração.

        Util para verificar se os field IDs e criterios estao corretos.

        Exemplo::

            TicketDashboard.diagnose("2024-04-24", "2024-05-14")
            TicketDashboard.diagnose("2024-04-24", "2024-05-14", cat_id=3)
        """
        glpi = ApiCommunication.glpi
        b    = cls._base(date_from, date_to, cat_id)
        bsla = cls._base_sla(cat_id)

        queries = [
            ("total",        b),
            ("fechados",     b    + cls._crit_status(cls.STATUS_FECHADO)),
            ("solucionados", b    + cls._crit_status(cls.STATUS_RESOLVIDO)),
            ("sla_vencido",  bsla + cls._crit_sla_vencido()),
            ("sla_hoje",     bsla + cls._crit_sla_hoje()),
        ]

        print(f"\n{'='*60}")
        print(f"  DIAGNOSE TicketDashboard  |  {date_from} a {date_to}")
        if cat_id:
            print(f"  categoria_id = {cat_id}")
        print(f"{'='*60}")

        for nome, criteria in queries:
            params = glpi._add_criteria(criteria, cls._itemtype())
            params["range"] = "0-0"
            resp = glpi.session.get(glpi._set_method("search", cls._itemtype()), params=params)
            body  = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            total = body.get("totalcount", "N/A")
            print(f"  {nome:<14} | HTTP {resp.status_code} | totalcount={total}")
            print(f"               URL: {resp.url[:120]}")

        print(f"{'='*60}\n")

    @classmethod
    def _metrics(cls, date_from: str, date_to: str, cat_id: int = None) -> dict:
        b    = cls._base(date_from, date_to, cat_id)
        bsla = cls._base_sla(cat_id)
        total        = cls._count(b)
        fechados     = cls._count(b + cls._crit_status(cls.STATUS_FECHADO))
        solucionados = cls._count(b + cls._crit_status(cls.STATUS_RESOLVIDO))
        abertos      = max(total - fechados - solucionados, 0)
        sla_vencido  = cls._count(bsla + cls._crit_sla_vencido())
        sla_hoje     = cls._count(bsla + cls._crit_sla_hoje())
        return dict(
            total=total,
            fechados=fechados,
            solucionados=solucionados,
            abertos=abertos,
            sla_vencido=sla_vencido,
            sla_hoje=sla_hoje,
        )

    # ------------------------------------------------------------------
    # Método para coleta de dados.
    # ------------------------------------------------------------------

    @classmethod
    def collect_data(
        cls,
        date_from: str,
        date_to: str,
        categories: Optional[dict] = None,
    ) -> dict:
        """Coleta métricas de chamados do GLPI para o período informado.

        Args:
            date_from:  Data inicial no formato YYYY-MM-DD (inclusive).
            date_to:    Data final no formato YYYY-MM-DD (inclusive).
            categories: Mapeamento {nome_exibicao: glpi_itilcategory_id}.
                        Ex.: {"Infraestrutura": 3, "Sistemas": 5}.
                        Se None, retorna apenas totais globais.

        Returns:
            dict com chaves: total, fechados, solucionados, abertos,
            sla_hoje, sla_vencido e categorias (dict aninhado por categoria
            com as mesmas métricas).
        """
        result = cls._metrics(date_from, date_to)
        categorias = {}
        if categories:
            for nome, cat_id in categories.items():
                categorias[nome] = cls._metrics(date_from, date_to, cat_id)
        result["categorias"] = categorias
        return result

    # ------------------------------------------------------------------
    # Método para geração do dashboard.
    # ------------------------------------------------------------------

    @classmethod
    def generate(
        cls,
        date_from: str,
        date_to: str,
        categories: Optional[dict] = None,
        output_path: str = "dashboard_glpi.html",
        titulo: str = "DTI",
        data: Optional[dict] = None,
    ) -> str:
        """Gera o dashboard de chamados GLPI em HTML ou imagem.

        Args:
            date_from:   Data inicial YYYY-MM-DD.
            date_to:     Data final YYYY-MM-DD.
            categories:  Mapeamento {nome_categoria: glpi_itilcategory_id}.
            output_path: Caminho de saida — ``.html`` (interativo) ou
                         ``.png``/``.svg``/``.pdf`` (estatico, requer a biblioteca kaleido).
            titulo:      Titulo central exibido no cabecalho do dashboard.
            data:        Dados pre-coletados (saida de :meth:`collect_data`).
                         Se None, chama ``collect_data()`` automaticamente.

        Returns:
            Caminho absoluto do arquivo gerado.

        Raises:
            ImportError: Se plotly nao estiver instalado.
            ImportError: Se kaleido nao estiver instalado ao exportar imagem.
        """
        try:
            import plotly.graph_objects as go
            import plotly.io as pio
        except ImportError:
            raise ImportError(
                "É necessário instalar a biblioteca plotly."
            )

        if data is None:
            data = cls.collect_data(date_from, date_to, categories)

        categorias = data.get("categorias", {})
        nomes      = sorted(categorias.keys())

        # ----------------------------------------------------------------
        # Traces
        # ----------------------------------------------------------------

        traces = []

        # Stacked horizontal bar chart (esquerda)
        bar_defs = [
            ("fechados",     "Fechados",      cls._BAR_COLORS["fechados"]),
            ("solucionados", "Solucionados",  cls._BAR_COLORS["solucionados"]),
            ("abertos",      "Abertos",       cls._BAR_COLORS["abertos"]),
            ("sla_hoje",     "Vencendo Hoje", cls._BAR_COLORS["sla_hoje"]),
            ("sla_vencido",  "SLA Vencido",   cls._BAR_COLORS["sla_vencido"]),
        ]

        for key, label, color in bar_defs:
            vals = [categorias[c][key] for c in nomes]
            traces.append(
                go.Bar(
                    name=label,
                    y=nomes,
                    x=vals,
                    orientation="h",
                    marker_color=color,
                    text=[str(v) if v else "" for v in vals],
                    textposition="inside",
                    insidetextanchor="middle",
                    xaxis="x1",
                    yaxis="y1",
                )
            )

        # Donut chart (direita, superior)
        traces.append(
            go.Pie(
                labels=nomes,
                values=[categorias[c]["total"] for c in nomes],
                hole=0.45,
                domain={"x": [0.54, 0.98], "y": [0.42, 0.78]},
                marker_colors=cls._PIE_PALETTE[:len(nomes)],
                textinfo="percent",
                textposition="outside",
                showlegend=False,
                hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
            )
        )

        # Tabela detalhada (direita, inferior)
        n_rows   = len(nomes) + 1  # +1 para linha de totais
        alt_fill = ["#f5f5f5" if i % 2 == 0 else "#ffffff" for i in range(n_rows - 1)]
        alt_fill += ["#dce8f5"]  # destaque na linha de totais

        col_totals = {
            k: sum(categorias[c][k] for c in nomes)
            for k in ("abertos", "sla_vencido", "sla_hoje", "solucionados", "fechados", "total")
        }

        traces.append(
            go.Table(
                domain={"x": [0.54, 0.98], "y": [0.0, 0.38]},
                header=dict(
                    values=[
                        "<b>Categoria</b>", "<b>Abertos</b>", "<b>SLA Vencido</b>",
                        "<b>Venc. Hoje</b>", "<b>Solucionados</b>", "<b>Fechados</b>",
                        "<b>Total</b>",
                    ],
                    fill_color="#e8e8e8",
                    align="left",
                    font=dict(size=12, color="#333"),
                    line_color="#ccc",
                    height=28,
                ),
                cells=dict(
                    values=[
                        nomes + ["<b>Total</b>"],
                        [categorias[c]["abertos"]      for c in nomes] + [col_totals["abertos"]],
                        [categorias[c]["sla_vencido"]  for c in nomes] + [col_totals["sla_vencido"]],
                        [categorias[c]["sla_hoje"]     for c in nomes] + [col_totals["sla_hoje"]],
                        [categorias[c]["solucionados"] for c in nomes] + [col_totals["solucionados"]],
                        [categorias[c]["fechados"]     for c in nomes] + [col_totals["fechados"]],
                        [categorias[c]["total"]        for c in nomes] + [col_totals["total"]],
                    ],
                    align="left",
                    font=dict(size=11),
                    fill_color=alt_fill,
                    line_color="#eee",
                    height=24,
                ),
            )
        )

        # ----------------------------------------------------------------
        # Shapes e anotacoes (KPI cards + header)
        # ----------------------------------------------------------------

        shapes, annotations = [], []

        # Fundo do cabecalho
        shapes.append(dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0.94, x1=1, y1=1.01,
            fillcolor="#1c2e4a",
            line=dict(width=0),
            layer="below",
        ))

        # KPI cards
        kpi_labels = ["N Chamados",   "Fechados",    "Solucionados",
                      "Abertos",      "SLA Venc. Hoje", "SLA Vencido"]
        kpi_keys   = ["total",        "fechados",    "solucionados",
                      "abertos",      "sla_hoje",       "sla_vencido"]
        kpi_vals   = [data[k] for k in kpi_keys]

        gap   = 0.005
        width = (1.0 - gap * 7) / 6
        y0_c, y1_c = 0.805, 0.935

        for i, (label, val, color) in enumerate(zip(kpi_labels, kpi_vals, cls._CARD_COLORS)):
            x0 = gap + i * (width + gap)
            x1 = x0 + width
            xm = (x0 + x1) / 2
            ym = (y0_c + y1_c) / 2

            shapes.append(dict(
                type="rect",
                xref="paper", yref="paper",
                x0=x0, y0=y0_c, x1=x1, y1=y1_c,
                fillcolor=color,
                line=dict(color="white", width=2),
                layer="below",
            ))
            annotations += [
                dict(
                    text=f"<b>{val}</b>",
                    xref="paper", yref="paper",
                    x=xm, y=ym + 0.022,
                    showarrow=False,
                    font=dict(size=24, color="white"),
                    align="center",
                    xanchor="center", yanchor="middle",
                ),
                dict(
                    text=label,
                    xref="paper", yref="paper",
                    x=xm, y=ym - 0.025,
                    showarrow=False,
                    font=dict(size=10, color="rgba(255,255,255,0.9)"),
                    align="center",
                    xanchor="center", yanchor="middle",
                ),
            ]

        # Centro vertical da caixa do cabecalho: (0.94 + 1.01) / 2
        _header_cy = (0.94 + 1.01) / 2

        # Titulo centralizado dentro da caixa azul
        annotations.append(dict(
            text=f"<b>{titulo}</b>",
            xref="paper", yref="paper",
            x=0.5, y=_header_cy,
            showarrow=False,
            font=dict(size=28, color="#f0c030"),
            xanchor="center",
            yanchor="middle",
        ))

        # Periodo no canto superior direito
        annotations.append(dict(
            text=f"<b>{date_from}</b>  a  <b>{date_to}</b>",
            xref="paper", yref="paper",
            x=0.99, y=_header_cy,
            showarrow=False,
            font=dict(size=12, color="#cccccc"),
            align="right",
            xanchor="right",
            yanchor="middle",
        ))

        # ----------------------------------------------------------------
        # Legendas manuais (shapes + annotations na margem inferior)
        # ----------------------------------------------------------------

        leg_y   = -0.055   # centro vertical das legendas (abaixo de y=0)
        sq_h    = 0.030    # altura do quadrado de cor em coords de papel
        sq_w    = 0.018    # largura do quadrado
        gap_txt = 0.006    # espaço entre quadrado e texto

        # Legenda de status (gráfico de barras) — lado esquerdo [0.0, 0.50]
        bar_legend_items = [
            ("Fechados",      cls._BAR_COLORS["fechados"]),
            ("Solucionados",  cls._BAR_COLORS["solucionados"]),
            ("Abertos",       cls._BAR_COLORS["abertos"]),
            ("Vencendo Hoje", cls._BAR_COLORS["sla_hoje"]),
            ("SLA Vencido",   cls._BAR_COLORS["sla_vencido"]),
        ]
        n_bar      = len(bar_legend_items)
        item_w_bar = 0.50 / n_bar
        for i, (label, color) in enumerate(bar_legend_items):
            sx0 = i * item_w_bar + 0.005
            sx1 = sx0 + sq_w
            shapes.append(dict(
                type="rect", xref="paper", yref="paper",
                x0=sx0, y0=leg_y - sq_h / 2,
                x1=sx1, y1=leg_y + sq_h / 2,
                fillcolor=color, line=dict(width=0),
            ))
            annotations.append(dict(
                text=label, xref="paper", yref="paper",
                x=sx1 + gap_txt, y=leg_y,
                showarrow=False,
                font=dict(size=10, color="#333"),
                xanchor="left", yanchor="middle",
            ))

        # Legenda de categorias (donut) — lado direito [0.54, 0.98]
        n_cat      = len(nomes)
        item_w_cat = (0.98 - 0.54) / max(n_cat, 1)
        for i, nome in enumerate(nomes):
            color = cls._PIE_PALETTE[i % len(cls._PIE_PALETTE)]
            sx0   = 0.54 + i * item_w_cat + 0.005
            sx1   = sx0 + sq_w
            shapes.append(dict(
                type="rect", xref="paper", yref="paper",
                x0=sx0, y0=leg_y - sq_h / 2,
                x1=sx1, y1=leg_y + sq_h / 2,
                fillcolor=color, line=dict(width=0),
            ))
            annotations.append(dict(
                text=nome, xref="paper", yref="paper",
                x=sx1 + gap_txt, y=leg_y,
                showarrow=False,
                font=dict(size=10, color="#333"),
                xanchor="left", yanchor="middle",
            ))

        # ----------------------------------------------------------------
        # Layout
        # ----------------------------------------------------------------

        fig = go.Figure(data=traces)
        fig.update_layout(
            barmode="stack",
            xaxis=dict(domain=[0.0, 0.50], anchor="y1", showgrid=True, gridcolor="#eee"),
            yaxis=dict(domain=[0.0, 0.78], anchor="y1", showgrid=False, autorange="reversed"),
            template="plotly_white",
            width=1400,
            height=900,
            paper_bgcolor="#f8f9fa",
            plot_bgcolor="#ffffff",
            showlegend=False,
            shapes=shapes,
            annotations=annotations,
            margin=dict(l=20, r=20, t=30, b=70),
        )

        abs_path = os.path.abspath(output_path)
        ext      = os.path.splitext(output_path)[1].lower()

        if ext == ".html":
            pio.write_html(fig, file=abs_path, auto_open=False)
        else:
            try:
                import asyncio
                import kaleido
                asyncio.run(kaleido.write_fig(fig, abs_path))
            except ImportError:
                raise ImportError(
                    f"kaleido e necessario para exportar {ext}. "
                    "Instale com: pip install kaleido"
                )

        return abs_path
