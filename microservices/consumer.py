"""
Consumer: Processa mensagens da fila RabbitMQ e atualiza as localizações no GLPI.
"""
import json
import os
import sys
import time
from pathlib import Path
# Importando bibliotecas necessárias para a interação com o RabbitMQ.
import pika
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / 'src'))

from glpi_api_hero import ApiCommunication
from glpi_api_hero.exceptions import ApiConnectionError, ApiRateLimitError
from glpi_api_hero.location import Location

load_dotenv(_PROJECT_ROOT / '.env')

# Definindo nomes das filas.
RABBITMQ_URL     = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
EXCHANGE         = 'ibge.endereco'
ROUTING_KEY      = 'atualizar_endereco'
QUEUE            = 'atualizar_endereco'
DLX              = 'ibge.endereco.dlx'
DLQ              = 'atualizar_endereco.dlq'
RETRY_EXCHANGE   = 'ibge.endereco.retry'
RETRY_QUEUE      = 'atualizar_endereco.retry'
# Consultando parâmetros com conexão com o GLPI.
GLPI_URL           = os.getenv('GLPI_URL')
GLPI_APPTOKEN      = os.getenv('GLPI_APPTOKEN')
GLPI_USER          = os.getenv('GLPI_USER')
GLPI_PASSWD        = os.getenv('GLPI_PASSWD')
GLPI_ENTITIES_ID   = int(os.getenv('GLPI_ENTITIES_ID', '0'))
GLPI_PROFILES_ID   = int(os.getenv('GLPI_PROFILES_ID', '4'))

_missing = [k for k, v in {'GLPI_URL': GLPI_URL, 'GLPI_APPTOKEN': GLPI_APPTOKEN,
                             'GLPI_USER': GLPI_USER, 'GLPI_PASSWD': GLPI_PASSWD}.items() if not v]
if _missing:
    raise EnvironmentError(f"Variáveis obrigatórias não definidas no .env: {', '.join(_missing)}")
# Delay entre mensagens (segundos) — throttle proativo para não atingir o rate limit
GLPI_REQUEST_DELAY = float(os.getenv('GLPI_REQUEST_DELAY', '0.5'))
# Tempo que a mensagem fica na fila de retry antes de voltar para a fila principal (ms)
GLPI_RETRY_DELAY_MS = int(os.getenv('GLPI_RETRY_DELAY_MS', '30000'))


def _connect_glpi() -> None:
    """Configura e abre uma sessão autenticada no GLPI.

    Define os parâmetros de conexão (URL, app token, usuário e senha), inicia
    a sessão e seleciona o perfil e entidade indicados nas variáveis de ambiente.
    Deve ser chamada uma vez antes de iniciar o consumo da fila.
    """
    ApiCommunication.setConnectionParameters(
        url=GLPI_URL,
        apptoken=GLPI_APPTOKEN,
        user=GLPI_USER,
        passwd=GLPI_PASSWD,
    )
    ApiCommunication.initSession()
    ApiCommunication.setProfileEntity(
        profiles_id=GLPI_PROFILES_ID,
        entities_id=GLPI_ENTITIES_ID,
        is_recursive=True,
    )


def _declare_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declara exchanges, filas e bindings necessários para o fluxo de mensagens.

    Cria três camadas:
    - DLX/DLQ: recebe mensagens com erro permanente (nack sem requeue).
    - Fila principal (QUEUE): fila de trabalho, com DLX configurado para desvio em caso de falha.
    - Fila de retry (RETRY_QUEUE): recebe mensagens com rate-limit; o TTL definido por
      GLPI_RETRY_DELAY_MS faz o RabbitMQ devolvê-las automaticamente à fila principal.
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

    # Fila de retry com TTL — após GLPI_RETRY_DELAY_MS a mensagem volta para a fila principal
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
    """Aplica a atualização de uma unidade organizacional no GLPI.

    Delega para Location.updateFromList, que cria ou atualiza o registro de
    localização correspondente à unidade recebida do SDA.
    """
    Location.updateFromList([unit], entities_id=GLPI_ENTITIES_ID)


def _on_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    _properties: pika.spec.BasicProperties,
    body: bytes,
) -> None:
    """Callback invocado pelo Pika para cada mensagem recebida da fila principal.

    Fluxo de tratamento de erros:
    - JSON inválido       → nack sem requeue (vai para a DLQ imediatamente).
    - ApiRateLimitError   → republica na RETRY_QUEUE com TTL e faz ack da mensagem original.
    - ApiConnectionError  → nack com requeue e para o consumer (espera reinício externo).
    - Qualquer outro erro → nack sem requeue (erro permanente, vai para a DLQ).
    """
    try:
        unit = json.loads(body)
    except json.JSONDecodeError as exc:
        print(f"[ERRO MENSAGEM] corpo inválido: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    sigla = unit.get('SIGLA', '?')
    nome  = unit.get('NOME',  '?')
    try:
        _process(unit)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[OK]   {sigla} — {nome}")
        time.sleep(GLPI_REQUEST_DELAY)

    except ApiRateLimitError as exc:
        # Rate limit atingido: republica na fila de retry e aguarda o TTL expirar.
        # O RabbitMQ devolve a mensagem à fila principal automaticamente após GLPI_RETRY_DELAY_MS.
        delay_s = GLPI_RETRY_DELAY_MS // 1000
        print(f"[RATE LIMIT] {sigla} — voltará à fila em {delay_s}s: {exc}")
        channel.basic_publish(
            exchange=RETRY_EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except ApiConnectionError as exc:
        # GLPI indisponível: devolve à fila e encerra o consumer.
        # O gerenciador de processos (Docker restart, systemd) deve reiniciá-lo.
        print(f"[GLPI INDISPONÍVEL] {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        channel.stop_consuming()

    except Exception as exc:
        # Erro permanente (dado inválido): envia para a DLQ, não reprocessa.
        print(f"[ERRO PERMANENTE] {sigla} — {nome}: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def consume() -> None:
    """Inicia o loop de consumo: conecta ao GLPI, ao RabbitMQ e processa mensagens indefinidamente.

    Configura prefetch_count=1 para garantir processamento um a um (sem sobrecarga do GLPI).
    Ao encerrar (CTRL+C ou stop_consuming interno), fecha a conexão com o RabbitMQ e
    encerra a sessão GLPI. Erros de conexão ao encerrar a sessão GLPI são silenciados,
    pois o processo está sendo finalizado de qualquer forma.
    """
    _connect_glpi()
    print("Sessão GLPI iniciada.")

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
            ApiCommunication.killSession()
        except ApiConnectionError:
            pass


if __name__ == '__main__':
    consume()
