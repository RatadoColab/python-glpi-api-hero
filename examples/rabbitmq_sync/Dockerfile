FROM python:3.10-slim

WORKDIR /app

# Install the glpi_api_hero library (build context is the repository root)
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Install the example dependencies
COPY examples/rabbitmq_sync/requirements.txt examples/rabbitmq_sync/
RUN pip install --no-cache-dir -r examples/rabbitmq_sync/requirements.txt

# Copy the example scripts and mappers
COPY examples/ examples/
