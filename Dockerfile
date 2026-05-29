FROM python:3.10-slim

WORKDIR /app

# Instala a biblioteca glpi_api_hero
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Instala dependências dos microserviços
COPY microservices/requirements.txt microservices/
RUN pip install --no-cache-dir -r microservices/requirements.txt

# Copia os scripts e os dados de exemplo do SDA
COPY microservices/ microservices/
# COPY examples/ examples/
