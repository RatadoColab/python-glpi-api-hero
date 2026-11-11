"""
Producer: reads records from a JSON file and publishes one message per record to RabbitMQ.
"""
import json
import os
from pathlib import Path

# Importando bibliotecas necessárias para a interação com o RabbitMQ.
import pika
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).parent

# Load configuration from the ".env" file next to this script
load_dotenv(_BASE_DIR / '.env')

RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

# Queue topology names (overridable through environment variables)
EXCHANGE     = os.getenv('RABBITMQ_EXCHANGE', 'glpi.locations')
ROUTING_KEY  = os.getenv('RABBITMQ_ROUTING_KEY', 'locations.update')
QUEUE        = os.getenv('RABBITMQ_QUEUE', 'locations.update')
DLX          = f'{EXCHANGE}.dlx'
DLQ          = f'{QUEUE}.dlq'

# Source JSON file (list of records) and the field used to label log lines
SOURCE_JSON  = _BASE_DIR / os.getenv('SOURCE_JSON', 'data.json')
LABEL_FIELD  = os.getenv('ITEM_LABEL_FIELD', 'name')


def _declare_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declara exchanges, filas e bindings no RabbitMQ.

    Cria primeiro a infraestrutura de dead-letter (DLX/DLQ) para que a fila
    principal já seja declarada com o argumento x-dead-letter-exchange apontando
    para o DLX. Mensagens rejeitadas ou expiradas são redirecionadas ao DLQ.
    """
    # Dead-letter exchange (fanout) e fila de descarte
    channel.exchange_declare(exchange=DLX, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=DLQ, durable=True)
    channel.queue_bind(queue=DLQ, exchange=DLX)

    # Exchange principal (direct) e fila de trabalho com DLX configurado
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='direct', durable=True)
    channel.queue_declare(
        queue=QUEUE,
        durable=True,
        arguments={'x-dead-letter-exchange': DLX},
    )
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)


def load_records() -> list:
    """Return the list of records to publish.

    Reads the JSON file defined by SOURCE_JSON. In production, replace this
    function with a call to the real data source (HTTP API, database, etc.).
    """
    with open(SOURCE_JSON, encoding='utf-8') as f:
        return json.load(f)


def publish(units: list) -> None:
    """Publica cada unidade organizacional como uma mensagem separada no RabbitMQ.

    Abre uma conexão bloqueante, garante a topologia via _declare_topology e
    itera sobre a lista publicando cada item serializado como JSON. As mensagens
    são marcadas como persistentes (delivery_mode=Persistent) para sobreviver a
    reinicializações do broker. A conexão é fechada ao final, independente do
    tamanho da lista.
    """
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    _declare_topology(channel)

    for unit in units:
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=json.dumps(unit, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json',
            ),
        )
        print(f"  Published: {unit.get(LABEL_FIELD)}")

    connection.close()
    print(f"\n{len(units)} message(s) published to queue '{QUEUE}'.")


if __name__ == '__main__':
    units = load_records()
    print(f"Records found: {len(units)}")
    publish(units)
