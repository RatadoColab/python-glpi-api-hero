Para instalar localmente:
> pip install -e .
Para executar após a instalação:
> helpdesk

Para instalar em outra máquina pode-se copiar os arquivos e instalar com "pip install" ou gerar um pacote na máquina de origem.

Para gerar pacote basta executar as linhas abaixo na raiz do projeto:
> pip install build
> python -m build
Será gerada a pasta "dist" com um arquivo "arquivo.whl".
Copiar o arquivo para outra máquina e executar a linha abaixo:
> pip install arquivo.whl
Para executar após a instalação:
> python-glpi-api-hero

