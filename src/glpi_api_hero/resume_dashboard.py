import os
import anthropic
from collections import Counter
from typing import Type

from glpi_api_hero.common_dbtm import CommonDBTM


class ResumeDashboard:
    """Interface de consulta em linguagem natural para entidades GLPI.

    Utiliza a Claude API para traduzir perguntas em português para critérios
    de busca estruturados e executa a consulta na entidade correspondente.

    Pré-requisito: variável de ambiente ANTHROPIC_API_KEY configurada.

    Exemplo::

        from glpi_api_hero import ApiCommunication, Ticket
        from glpi_api_hero.resume_dashboard import ResumeDashboard

        ApiCommunication.setConnectionParameters(url, apptoken, user=user, passwd=passwd)
        ApiCommunication.initSession()

        resultado = ResumeDashboard.search_natural(
            "chamados abertos de alta prioridade criados essa semana",
            Ticket
        )
    """

    # Mapeamento field_id → metadados por entidade (classe Python).
    # Os IDs seguem o padrão do endpoint search do GLPI.
    _FIELDS: dict[str, dict[int, dict]] = {
        "Ticket": {
            1:  {"nome": "Título",              "descricao": "Título/nome do chamado"},
            4:  {"nome": "Requerente",          "descricao": "ID do usuário que abriu o chamado"},
            5:  {"nome": "Atribuído a",         "descricao": "ID do técnico/usuário responsável"},
            7:  {"nome": "Categoria",           "descricao": "ID da categoria do chamado"},
            12: {"nome": "Status",              "descricao": "Status do chamado",
                 "valores": {1: "Novo", 2: "Em andamento (atribuído)", 3: "Em andamento (planejado)",
                             4: "Pendente", 5: "Resolvido", 6: "Fechado"}},
            15: {"nome": "Data de abertura",    "descricao": "Data de criação (YYYY-MM-DD)"},
            16: {"nome": "Última atualização",  "descricao": "Data da última modificação (YYYY-MM-DD)"},
            17: {"nome": "Data de resolução",   "descricao": "Data em que foi resolvido (YYYY-MM-DD)"},
            21: {"nome": "Descrição",           "descricao": "Conteúdo/descrição do chamado"},
            23: {"nome": "Urgência",            "descricao": "Nível de urgência",
                 "valores": {1: "Muito alta", 2: "Alta", 3: "Média", 4: "Baixa", 5: "Muito baixa"}},
            24: {"nome": "Impacto",             "descricao": "Nível de impacto",
                 "valores": {1: "Muito alto", 2: "Alto", 3: "Médio", 4: "Baixo", 5: "Muito baixo"}},
            25: {"nome": "Prioridade",          "descricao": "Prioridade calculada",
                 "valores": {1: "Muito alta", 2: "Alta", 3: "Média", 4: "Baixa", 5: "Muito baixa"}},
            28: {"nome": "Tipo",                "descricao": "Tipo do chamado",
                 "valores": {1: "Incidente", 2: "Requisição"}},
            66: {"nome": "Observador",          "descricao": "ID do usuário observador"},
        },
        "User": {
            1:  {"nome": "Login",       "descricao": "Nome de login do usuário"},
            2:  {"nome": "Sobrenome",   "descricao": "Sobrenome"},
            3:  {"nome": "Nome",        "descricao": "Primeiro nome"},
            5:  {"nome": "E-mail",      "descricao": "Endereço de e-mail"},
            8:  {"nome": "Telefone",    "descricao": "Número de telefone"},
            34: {"nome": "Perfil",      "descricao": "ID do perfil de acesso"},
        },
        "Computer": {
            1:  {"nome": "Nome",                "descricao": "Nome do equipamento"},
            5:  {"nome": "Número de série",     "descricao": "Serial number"},
            6:  {"nome": "Patrimônio",          "descricao": "Número de patrimônio (asset tag)"},
            7:  {"nome": "Localização",         "descricao": "ID da localização"},
            11: {"nome": "Sistema operacional", "descricao": "Nome do SO instalado"},
            45: {"nome": "Status",              "descricao": "ID do status do equipamento"},
        },
        "Group": {
            1:  {"nome": "Nome",        "descricao": "Nome do grupo"},
            21: {"nome": "Descrição",   "descricao": "Descrição do grupo"},
        },
        "Location": {
            1:  {"nome": "Nome",            "descricao": "Nome da localização"},
            2:  {"nome": "Nome completo",   "descricao": "Nome completo com hierarquia (ex: Sede > Bloco A)"},
            11: {"nome": "Código",          "descricao": "Código COD_SIORG da unidade organizacional"},
        },
        "Actor": {
            3:  {"nome": "Tipo de ator",    "descricao": "Papel do ator no chamado",
                 "valores": {1: "Requerente", 2: "Atribuído", 3: "Observador"}},
            4:  {"nome": "Usuário",         "descricao": "ID do usuário ator"},
            5:  {"nome": "Grupo",           "descricao": "ID do grupo ator"},
        },
        "Item": {
            1:  {"nome": "Nome do ativo",   "descricao": "Nome do ativo vinculado ao chamado"},
            3:  {"nome": "Tipo do ativo",   "descricao": "Tipo do ativo (ex: Computer, Monitor)"},
        },
        "Task": {
            1:  {"nome": "Conteúdo",        "descricao": "Descrição da tarefa"},
            12: {"nome": "Status",          "descricao": "Estado da tarefa",
                 "valores": {0: "Informação", 1: "A fazer", 2: "Feito"}},
            13: {"nome": "Usuário técnico", "descricao": "ID do técnico responsável pela tarefa"},
        },
        "ITILFollowup": {
            1:  {"nome": "Conteúdo",    "descricao": "Texto do acompanhamento"},
            3:  {"nome": "Privado",     "descricao": "Visibilidade", "valores": {0: "Público", 1: "Privado"}},
        },
        "ITILSolution": {
            1:  {"nome": "Conteúdo",    "descricao": "Texto da solução"},
            2:  {"nome": "Tipo",        "descricao": "ID do tipo de solução"},
        },
        "LinkedTicket": {
            1:  {"nome": "Chamado vinculado",   "descricao": "ID do chamado de destino"},
            3:  {"nome": "Tipo de vínculo",     "descricao": "Relação entre chamados",
                 "valores": {1: "Relacionado", 2: "Duplicado", 3: "Filho de", 4: "Pai de"}},
        },
        "Cluster": {
            1:  {"nome": "Nome",        "descricao": "Nome do cluster"},
            7:  {"nome": "Localização", "descricao": "ID da localização do cluster"},
        },
        "NetworkEquipment": {
            1:  {"nome": "Nome",                "descricao": "Nome do equipamento de rede"},
            5:  {"nome": "Número de série",     "descricao": "Serial number"},
            7:  {"nome": "Localização",         "descricao": "ID da localização"},
        },
    }

    _SEARCHTYPES = {
        "equals":      "igual ao valor exato",
        "notequals":   "diferente do valor",
        "contains":    "contém (busca parcial em texto)",
        "notcontains": "não contém",
        "morethan":    "maior ou mais recente que",
        "lessthan":    "menor ou mais antigo que",
    }

    # Ferramenta exposta ao Claude para retornar critérios estruturados
    _TOOL_DEFINITION = {
        "name": "definir_criterios_busca",
        "description": "Define os critérios de busca estruturados para a API GLPI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "array",
                    "description": "Lista de critérios de busca.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field":      {"type": "integer", "description": "ID do campo"},
                            "searchtype": {"type": "string",  "description": "Tipo de comparação"},
                            "value":      {"description": "Valor a comparar (string ou número)"},
                            "link":       {"type": "string",  "description": "Operador lógico com critério anterior: AND ou OR",
                                           "enum": ["AND", "OR"]},
                        },
                        "required": ["field", "searchtype", "value"],
                    },
                }
            },
            "required": ["criteria"],
        },
    }

    @classmethod
    def _build_system_prompt(cls, entity_key: str) -> str:
        fields = cls._FIELDS[entity_key]
        campos = "\n".join(
            f"  - field {fid}: {info['nome']} — {info['descricao']}"
            + (f" [valores possíveis: {info['valores']}]" if "valores" in info else "")
            for fid, info in fields.items()
        )
        tipos = "\n".join(f"  - {k}: {v}" for k, v in cls._SEARCHTYPES.items())
        return (
            f"Você é um especialista em GLPI. Sua única função é converter consultas em português "
            f"para critérios de busca da entidade \"{entity_key}\" usando a ferramenta "
            f"definir_criterios_busca.\n\n"
            f"Campos disponíveis:\n{campos}\n\n"
            f"Tipos de busca:\n{tipos}\n\n"
            f"Se a consulta for ambígua, escolha os critérios mais prováveis. "
            f"Se não for possível mapear nenhum critério, retorne criteria vazio."
        )

    @classmethod
    def search_natural(
        cls,
        query: str,
        entity: Type[CommonDBTM],
        model: str = "claude-haiku-4-5-20251001",
        **kwargs,
    ) -> list:
        """Executa uma consulta em linguagem natural contra uma entidade GLPI.

        Traduz a consulta para critérios de busca usando a Claude API e executa
        o search na entidade informada.

        Args:
            query (str): Consulta em linguagem natural (ex: "chamados abertos urgentes").
            entity (Type[CommonDBTM]): Classe da entidade a consultar (ex: Ticket, User).
            model (str): Modelo Claude a usar. Padrão: claude-haiku-4-5-20251001.
            **kwargs: Parâmetros extras repassados ao search da entidade
                (ex: range, sort, forcedisplay).

        Returns:
            list: Resultado da busca retornado pela API GLPI.

        Raises:
            ValueError: Se a entidade não tiver mapeamento de campos definido.
            anthropic.APIError: Para erros de comunicação com a Claude API.
        """
        entity_key = entity.__name__
        if entity_key not in cls._FIELDS:
            supported = list(cls._FIELDS.keys())
            raise ValueError(
                f"Entidade '{entity_key}' não possui mapeamento de campos. "
                f"Entidades suportadas: {supported}"
            )

        client = anthropic.Anthropic()

        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=cls._build_system_prompt(entity_key),
            tools=[cls._TOOL_DEFINITION],
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": query}],
        )

        criteria = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "definir_criterios_busca":
                criteria = block.input.get("criteria", [])
                break

        if not criteria:
            return entity.search(**kwargs)

        return entity.search(criteria=criteria, **kwargs)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    _TOOL_PAINEL = {
        "name": "definir_painel_dashboard",
        "description": "Define critérios de busca e configuração de visualização para um painel do dashboard GLPI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "array",
                    "description": "Critérios de filtro. Use lista vazia para buscar todos os registros.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field":      {"type": "integer"},
                            "searchtype": {"type": "string"},
                            "value":      {},
                            "link":       {"type": "string", "enum": ["AND", "OR"]},
                        },
                        "required": ["field", "searchtype", "value"],
                    },
                },
                "campo_agrupamento": {
                    "type": "integer",
                    "description": "ID do campo pelo qual os resultados serão agrupados e contados no gráfico.",
                },
                "tipo_grafico": {
                    "type": "string",
                    "enum": ["barra", "pizza"],
                    "description": "'pizza' para distribuições/proporções, 'barra' para comparações quantitativas.",
                },
                "rotulos_valores": {
                    "type": "object",
                    "description": "Mapeamento de valor para rótulo legível (ex: {'1': 'Novo', '5': 'Resolvido'}).",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["criteria", "campo_agrupamento", "tipo_grafico"],
        },
    }

    @classmethod
    def _build_painel_prompt(cls, entity_key: str) -> str:
        fields = cls._FIELDS.get(entity_key, {})
        campos = "\n".join(
            f"  - field {fid}: {info['nome']} — {info['descricao']}"
            + (f" [valores: {info['valores']}]" if "valores" in info else "")
            for fid, info in fields.items()
        )
        return (
            f"Você é um especialista em GLPI e visualização de dados. "
            f"Converta a consulta sobre a entidade \"{entity_key}\" em critérios de busca e "
            f"configuração de gráfico usando a ferramenta definir_painel_dashboard.\n\n"
            f"Campos disponíveis:\n{campos}\n\n"
            f"Diretrizes:\n"
            f"- Use criteria=[] para buscar todos os registros sem filtro.\n"
            f"- Escolha campo_agrupamento como o campo mais relevante para visualização.\n"
            f"- Use 'pizza' para distribuições (ex: por status, por tipo).\n"
            f"- Use 'barra' para comparações (ex: por categoria, por localização).\n"
            f"- Preencha rotulos_valores com rótulos legíveis para valores numéricos."
        )

    @classmethod
    def _agregar_por_campo(
        cls,
        entity: Type[CommonDBTM],
        criteria: list,
        campo_agrupamento: int,
    ) -> dict[str, int]:
        search_kwargs: dict = {"forcedisplay": [campo_agrupamento], "range": "0-9999"}
        if criteria:
            search_kwargs["criteria"] = criteria

        result = entity.search(**search_kwargs)

        data = result.get("data", {}) if isinstance(result, dict) else {}
        rows = list(data.values()) if isinstance(data, dict) else (data if isinstance(data, list) else [])

        str_field = str(campo_agrupamento)
        values = []
        for row in rows:
            if isinstance(row, dict):
                val = row.get(str_field) or row.get(campo_agrupamento)
                values.append(str(val).strip() if val is not None else "N/D")

        return dict(Counter(values))

    @classmethod
    def generate_dashboard(
        cls,
        panels: list[dict],
        output_path: str = "dashboard.png",
        titulo: str = "Dashboard GLPI",
        model: str = "claude-haiku-4-5-20251001",
        width: int = 1400,
        height_per_row: int = 500,
    ) -> str:
        """Gera um dashboard com múltiplos painéis a partir de consultas em linguagem natural.

        O formato de saída é determinado pela extensão do ``output_path``:
        ``.png``, ``.jpg`` ou ``.svg`` geram imagem estática (requer ``kaleido``);
        ``.html`` gera página interativa.

        Args:
            panels (list[dict]): Lista de painéis. Cada item deve conter:
                - "titulo" (str): Título exibido no painel.
                - "query" (str): Consulta em linguagem natural (ex: "tickets por status").
                - "entity" (Type[CommonDBTM]): Classe da entidade GLPI a consultar.
            output_path (str): Caminho do arquivo de saída. Padrão: "dashboard.png".
            titulo (str): Título principal do dashboard.
            model (str): Modelo Claude a usar. Padrão: claude-haiku-4-5-20251001.
            width (int): Largura em pixels (apenas para imagens). Padrão: 1400.
            height_per_row (int): Altura por linha de painéis em pixels. Padrão: 500.

        Returns:
            str: Caminho absoluto do arquivo gerado.

        Raises:
            ImportError: Se plotly não estiver instalado (``pip install plotly``).
            ImportError: Se kaleido não estiver instalado ao exportar imagem
                (``pip install kaleido``).
            ValueError: Se alguma entidade não tiver mapeamento de campos.

        Exemplo::

            caminho = ResumeDashboard.generate_dashboard(
                panels=[
                    {"titulo": "Chamados por Status",    "query": "tickets agrupados por status",    "entity": Ticket},
                    {"titulo": "Chamados por Prioridade","query": "tickets agrupados por prioridade","entity": Ticket},
                ],
                output_path="dashboard_glpi.png",
                titulo="Dashboard de Chamados GLPI",
            )
            print(f"Dashboard gerado em: {caminho}")
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import plotly.io as pio
        except ImportError:
            raise ImportError(
                "plotly é necessário para gerar dashboards. "
                "Instale com: pip install plotly"
            )

        ext = os.path.splitext(output_path)[1].lower()
        image_formats = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".webp"}
        exportar_imagem = ext in image_formats

        if exportar_imagem:
            try:
                import kaleido  # noqa: F401
            except ImportError:
                raise ImportError(
                    f"kaleido é necessário para exportar dashboards como {ext}. "
                    "Instale com: pip install kaleido"
                )

        client = anthropic.Anthropic()
        figures_data = []

        for panel in panels:
            panel_titulo = panel.get("titulo", "Painel")
            query        = panel["query"]
            entity       = panel["entity"]
            entity_key   = entity.__name__

            if entity_key not in cls._FIELDS:
                raise ValueError(
                    f"Entidade '{entity_key}' não suportada. "
                    f"Suportadas: {list(cls._FIELDS.keys())}"
                )

            response = client.messages.create(
                model=model,
                max_tokens=512,
                system=cls._build_painel_prompt(entity_key),
                tools=[cls._TOOL_PAINEL],
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": query}],
            )

            panel_config: dict = {}
            for block in response.content:
                if block.type == "tool_use" and block.name == "definir_painel_dashboard":
                    panel_config = block.input
                    break

            criteria          = panel_config.get("criteria", [])
            campo_agrupamento = panel_config.get("campo_agrupamento")
            tipo_grafico      = panel_config.get("tipo_grafico", "barra")
            rotulos           = {str(k): v for k, v in panel_config.get("rotulos_valores", {}).items()}

            counter: dict[str, int] = {}
            if campo_agrupamento:
                counter = cls._agregar_por_campo(entity, criteria, campo_agrupamento)

            labels = [rotulos.get(k, k) for k in counter]
            values = list(counter.values())

            figures_data.append({
                "titulo": panel_titulo,
                "labels": labels,
                "values": values,
                "tipo":   tipo_grafico,
            })

        n    = len(figures_data)
        cols = min(n, 2)
        rows = (n + cols - 1) // cols

        specs = [
            [
                {"type": "domain" if figures_data[r * cols + c]["tipo"] == "pizza" else "xy"}
                if r * cols + c < n else {"type": "xy"}
                for c in range(cols)
            ]
            for r in range(rows)
        ]

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[fd["titulo"] for fd in figures_data],
            specs=specs,
        )

        for i, fd in enumerate(figures_data):
            row = i // cols + 1
            col = i % cols + 1

            if fd["tipo"] == "pizza":
                trace = go.Pie(
                    labels=fd["labels"],
                    values=fd["values"],
                    name=fd["titulo"],
                    hole=0.3,
                )
            else:
                trace = go.Bar(
                    x=fd["labels"],
                    y=fd["values"],
                    name=fd["titulo"],
                    marker_color="#1f77b4",
                )

            fig.add_trace(trace, row=row, col=col)

        total_height = height_per_row * rows

        fig.update_layout(
            title_text=titulo,
            title_font_size=22,
            width=width,
            height=total_height,
            template="plotly_white",
            showlegend=True,
        )

        abs_path = os.path.abspath(output_path)

        if exportar_imagem:
            import asyncio
            import kaleido
            asyncio.run(kaleido.write_fig(fig, abs_path))
        else:
            pio.write_html(fig, file=abs_path, auto_open=False)

        return abs_path
