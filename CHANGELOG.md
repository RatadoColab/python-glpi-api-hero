# Changelog

## Não lançado

### Novidades
- Criação e atualização de localizações em lote a partir de qualquer fonte de dados, usando uma função de conversão (mapeador) definida por quem usa a biblioteca.
- Escolha do campo que identifica cada localização na atualização em lote (por padrão, o código externo).
- Exemplo de mapeador para converter uma lista de unidades organizacionais em localizações do GLPI.
- Exemplo de sincronização assíncrona via RabbitMQ, com nomes de filas configuráveis, tratamento de limite de requisições e fila de falhas.

### Mudanças
- A conversão específica de um catálogo de unidades organizacionais deixou de fazer parte da biblioteca e passou a ser um exemplo. Quem usava a atualização em lote com esse formato deve informar o mapeador do exemplo.
- Os microsserviços e os arquivos de Docker passaram a ser exemplos, na pasta de exemplos.
