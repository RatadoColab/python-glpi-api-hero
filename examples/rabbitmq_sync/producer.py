"""
Producer: reads records from a JSON file and publishes one message per record to RabbitMQ.
"""
import json
import os
from pathlib import Path

# Libraries needed to talk to RabbitMQ.
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
    the main queue must already be declared with the x-dead-letter-exchange argument pointing
    to the DLX. Rejected or expired messages are redirected to the DLQ.
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

    Opens a blocking connection, ensures the topology through _declare_topology and
    itera sobre a lista publicando cada item serializado como JSON. As mensagens
    are marked persistent (delivery_mode=Persistent) to survive
    broker restarts. The connection is closed at the end, regardless of the
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
