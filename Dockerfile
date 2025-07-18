

# Instala o Poppler (usado por pdf2image)
RUN apt-get update && apt-get install -y poppler-utils && apt-get clean

# Cria diretório de trabalho
WORKDIR /app

FROM python:3.9-slim

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements.txt .

# Expõe a porta padrão do Flask
EXPOSE 5000

# Executa o app
CMD ["python", "app/app.py"]


RUN apt-get update && apt-get install -y poppler-utils

