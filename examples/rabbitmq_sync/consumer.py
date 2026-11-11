"""
Consumer: processes RabbitMQ messages and updates locations in GLPI.
"""
import importlib
import json
import os
import sys
import time
from pathlib import Path

# Libraries needed to talk to RabbitMQ.
import pika
from dotenv import load_dotenv

_BASE_DIR = Path(__file__).parent
_PROJECT_ROOT = _BASE_DIR.parent.parent
# Make the library (src/) and sibling example packages importable when running from a checkout
sys.path.insert(0, str(_PROJECT_ROOT / 'src'))
sys.path.insert(0, str(_BASE_DIR.parent))

from glpi_api_hero import Glpi
from glpi_api_hero.dropdowns import Location
from glpi_api_hero.exceptions import GlpiConnectionError, RateLimitError

load_dotenv(_BASE_DIR / '.env')

# Queue topology names (overridable through environment variables)
RABBITMQ_URL     = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
EXCHANGE         = os.getenv('RABBITMQ_EXCHANGE', 'glpi.locations')
ROUTING_KEY      = os.getenv('RABBITMQ_ROUTING_KEY', 'locations.update')
QUEUE            = os.getenv('RABBITMQ_QUEUE', 'locations.update')
DLX              = f'{EXCHANGE}.dlx'
DLQ              = f'{QUEUE}.dlq'
RETRY_EXCHANGE   = f'{EXCHANGE}.retry'
RETRY_QUEUE      = f'{QUEUE}.retry'
# Optional mapper ("package.module:function") converting a record into GLPI Location fields
ITEM_MAPPER      = os.getenv('ITEM_MAPPER')
# Field of the incoming record used to label log lines
LABEL_FIELD      = os.getenv('ITEM_LABEL_FIELD', 'name')
# Key field used to match existing locations in GLPI
KEY_FIELD        = os.getenv('LOCATION_KEY_FIELD', 'code')
# GLPI connection parameters
GLPI_URL           = os.getenv('GLPI_URL')
GLPI_APPTOKEN      = os.getenv('GLPI_APPTOKEN')
GLPI_USER          = os.getenv('GLPI_USER')
GLPI_PASSWD        = os.getenv('GLPI_PASSWD')
GLPI_ENTITIES_ID   = int(os.getenv('GLPI_ENTITIES_ID', '0'))
GLPI_PROFILES_ID   = int(os.getenv('GLPI_PROFILES_ID', '4'))

_missing = [k for k, v in {'GLPI_URL': GLPI_URL, 'GLPI_APPTOKEN': GLPI_APPTOKEN,
                             'GLPI_USER': GLPI_USER, 'GLPI_PASSWD': GLPI_PASSWD}.items() if not v]
if _missing:
    raise OSError(f"Required variables missing from .env: {', '.join(_missing)}")
# Delay between messages (seconds): proactive throttle to stay under the rate limit
GLPI_REQUEST_DELAY = float(os.getenv('GLPI_REQUEST_DELAY', '0.5'))
# Time a message waits in the retry queue before going back to the main queue (ms)
GLPI_RETRY_DELAY_MS = int(os.getenv('GLPI_RETRY_DELAY_MS', '30000'))


def _load_mapper():
    """Resolve ITEM_MAPPER ("package.module:function") into a callable.

    Returns None when ITEM_MAPPER is not set, meaning records are expected to
    already hold GLPI Location fields.
    """
    if not ITEM_MAPPER:
        return None
    module_name, _, func_name = ITEM_MAPPER.partition(':')
    return getattr(importlib.import_module(module_name), func_name)


MAPPER = _load_mapper()


def _connect_glpi() -> None:
    """Configure and open an authenticated GLPI session.

    Sets the connection parameters (URL, app token, user and password), starts
    the session and selects the profile and entity given in the environment variables.
    Deve ser chamada uma vez antes de iniciar o consumo da fila.
    """
    Glpi.connect(GLPI_URL, GLPI_APPTOKEN, username=GLPI_USER, password=GLPI_PASSWD)
    Glpi.set_profile_entity(GLPI_PROFILES_ID, GLPI_ENTITIES_ID, is_recursive=True)


def _declare_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declare the exchanges, queues and bindings of the message flow.

    Three layers are created:
    - DLX/DLQ: recebe mensagens com erro permanente (nack sem requeue).
    - Fila principal (QUEUE): fila de trabalho, com DLX configurado para desvio em caso de falha.
    - Fila de retry (RETRY_QUEUE): recebe mensagens com rate-limit; o TTL definido por
      GLPI_RETRY_DELAY_MS makes RabbitMQ return them to the main queue automatically.
    """
    # DLQ — mensagens com erro permanente
    channel.exchange_declare(exchange=DLX, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=DLQ, durable=True)
    channel.queue_bind(queue=DLQ, exchange=DLX)

    # Fila principal
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='direct', durable=True)
    channel.queue_declare(
        queue=QUEUE,
        durable=True,
        arguments={'x-dead-letter-exchange': DLX},
    )
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=ROUTING_KEY)

    # Retry queue with TTL: after GLPI_RETRY_DELAY_MS the message goes back to the main queue
    channel.exchange_declare(exchange=RETRY_EXCHANGE, exchange_type='direct', durable=True)
    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            'x-message-ttl':             GLPI_RETRY_DELAY_MS,
            'x-dead-letter-exchange':    EXCHANGE,
            'x-dead-letter-routing-key': ROUTING_KEY,
        },
    )
    channel.queue_bind(queue=RETRY_QUEUE, exchange=RETRY_EXCHANGE, routing_key=ROUTING_KEY)


def _process(unit: dict) -> None:
    """Apply one record to GLPI.

    Delegates to Location.update_from_list, which creates or updates the Location
    matching the received record (converted by MAPPER when configured).
    """
    Location.update_from_list(
        [unit], entities_id=GLPI_ENTITIES_ID, mapper=MAPPER, key_field=KEY_FIELD
    )


def _on_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    _properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Callback invocado pelo Pika para cada mensagem recebida da fila principal.

    Fluxo de tratamento de erros:
    - Invalid JSON        -> nack without requeue (goes straight to the DLQ).
    - RateLimitError   → republica na RETRY_QUEUE com TTL e faz ack da mensagem original.
    - GlpiConnectionError -> nack with requeue and stop the consumer (an external restart is expected).
    - Any other error     -> nack without requeue (permanent error, goes to the DLQ).
    """
    try:
        unit = json.loads(body)
    except json.JSONDecodeError as exc:
        print(f"[MESSAGE ERROR] invalid body: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    label = unit.get(LABEL_FIELD, '?')
    try:
        _process(unit)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[OK]   {label}")
        time.sleep(GLPI_REQUEST_DELAY)

    except RateLimitError as exc:
        # Rate limit atingido: republica na fila de retry e aguarda o TTL expirar.
        # RabbitMQ returns the message to the main queue automatically after GLPI_RETRY_DELAY_MS.
        delay_s = GLPI_RETRY_DELAY_MS // 1000
        print(f"[RATE LIMIT] {label} - back in the queue in {delay_s}s: {exc}")
        channel.basic_publish(
            exchange=RETRY_EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except GlpiConnectionError as exc:
        # GLPI unavailable: put the message back in the queue and stop the consumer.
        # The process manager (Docker restart, systemd) is expected to restart it.
        print(f"[GLPI UNAVAILABLE] {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        channel.stop_consuming()

    except Exception as exc:
        # Permanent error (invalid data): send to the DLQ, do not reprocess.
        print(f"[ERRO PERMANENTE] {label}: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def consume() -> None:
    """Inicia o loop de consumo: conecta ao GLPI, ao RabbitMQ e processa mensagens indefinidamente.

    Configura prefetch_count=1 para garantir processamento um a um (sem sobrecarga do GLPI).
    On exit (CTRL+C or an internal stop_consuming), closes the RabbitMQ connection and
    ends the GLPI session. Connection errors while ending the GLPI session are ignored,
    because the process is shutting down anyway.
    """
    _connect_glpi()
    print("GLPI session started.")

    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    _declare_topology(channel)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=_on_message)

    print(f"Aguardando mensagens na fila '{QUEUE}'. CTRL+C para sair.\n")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()
        try:
            Glpi.disconnect()
        except GlpiConnectionError:
            pass


if __name__ == '__main__':
    consume()
