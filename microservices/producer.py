"""
Producer: Lê as unidades organizacionais do SDA e publica uma mensagem por unidade no RabbitMQ.
"""
import json
import os
import sys
from pathlib import Path
# Importando bibliotecas necessárias para a interação com o RabbitMQ.
import pika
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent.parent

# Consultando parâmetros de configuração no arquivo ".env".
load_dotenv(_PROJECT_ROOT / '.env')

RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

# Definindo nomes das filas.
EXCHANGE     = 'ibge.endereco'
ROUTING_KEY  = 'atualizar_endereco'
QUEUE        = 'atualizar_endereco'
DLX          = 'ibge.endereco.dlx'
DLQ          = 'atualizar_endereco.dlq'

_DEFAULT_SDA = _PROJECT_ROOT / 'examples' / 'amostra-pequena.json'
_sda_env     = os.getenv('SDA_JSON')
SDA_JSON     = (_PROJECT_ROOT / _sda_env) if _sda_env else _DEFAULT_SDA


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


def consultar_unid_org() -> list:
    """Retorna a lista de unidades organizacionais do SDA.

    Em desenvolvimento lê o arquivo JSON definido por SDA_JSON (padrão:
    examples/amostra-pequena.json). Em produção esta função deve ser substituída
    por uma chamada HTTP à API real do SDA.
    """
    with open(SDA_JSON, encoding='utf-8') as f:
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
        print(f"  Publicado: {unit.get('SIGLA')} — {unit.get('NOME')}")

    connection.close()
    print(f"\n{len(units)} mensagem(ns) publicada(s) na fila '{QUEUE}'.")


if __name__ == '__main__':
    units = consultar_unid_org()
    print(f"Unidades encontradas no SDA: {len(units)}")
    publish(units)
