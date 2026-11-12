# PENDING

Pendências abertas ao fechar o pipeline `glpi10-refactor` (registradas em 2026-11-11, sem dono salvo indicação).

## P-001 — GLPI 12: tradução de nomes de campo entre a API legada e a v3
- Contexto: o conector normaliza o formato dos retornos, mas os nomes de campo diferem (colunas da v1 × schemas da v3 do GLPI 12.0.1; referência `~/Desenvolvimento/glpi12/src/Glpi/Api/HL`).
- Pronto quando: o conector v3 traduz entrada e saída, ou a biblioteca adota um modelo de campos próprio, com decisão registrada.

## P-002 — Contagem total em get_all e search
- Contexto: `get_all`/`search` devolvem `list[dict]`; o total (`Content-Range`) só vai para o log.
- Pronto quando: existe API pública para o total ou a paginação (`search_page()` ou `iter_all()`), com teste, ou a decisão de não oferecer.

## P-004 — Defeitos remanescentes dos modelos migrados
- Contexto: `Location.get_by_code` (`code` não é campo do core; decidir campo/plugin) e `Group.delete_user` (releitura da primeira página já corrigida por `range`; confirmar em dados reais).
- Pronto quando: cada método corrigido com teste ou decisão de manter registrada.

## P-006 — Exemplos: RabbitMQ e dashboard
- Contexto: consumer sai com código 0 após `GlpiConnectionError` (compose `restart: on-failure` não reinicia); sessão expirada manda mensagens para a DLQ; JSON que não é objeto derruba o callback; dashboard sem docblocks, comentários em português, paleta de 7 cores, `search_body` fora do contrato `Connector`.
- Pronto quando: corrigidos ou registrados como "mantido por ser exemplo".

## P-009 — Acessores de rack/gabinete incompletos
- Contexto: `HasRack.get_racks` lê só `Item_Rack`; faltam `PDU_Rack` e `Item_Enclosure`.
- Pronto quando: acessores adicionados com teste ou decisão registrada.

## P-010 — Endurecimento do exemplo RabbitMQ
- Contexto: portas 5672/15672 em todas as interfaces, credenciais guest/guest, container root, imagem `python:3.10-slim` fora de suporte.
- Pronto quando: portas em 127.0.0.1, credenciais obrigatórias, `USER` não-root e imagem suportada, ou decisão registrada.

## P-011 — get_virtual_machines e get_consumables falham no GLPI 10.0.26
- Contexto: `ServerError (ERROR_UNKNOWN)` pelos endpoints de item; limitação documentada em `docs/assets.md`.
- Pronto quando: caminho alternativo via search engine com teste, ou decisão de manter.

## P-012 — Arestas do conector e de update_from_list
- Contexto: recusa de escrita chega como `BadRequestError` e não `PermissionDeniedError`; `datetime` no payload escapa como `TypeError`; `Location.update_from_list` baixa até 10 000 localizações por chamada.
- Pronto quando: cada item tratado com teste ou decisão registrada.

## P-013 — Código duplicado e morto
- Contexto: constantes `Ticket.SEARCH_FIELD_ITEM_*` sem uso, `Location.get_logs` duplica `HasLogs`, leitores de `Location` repetem `get_items_by_type`, `_find` duplicado, fixture `session` duplicada.
- Pronto quando: consolidado sem mudança de comportamento.
