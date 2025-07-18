# Usa imagem base leve com Python
FROM python:3.10-slim

# Instala o Poppler (usado por pdf2image)
RUN apt-get update && apt-get install -y poppler-utils && apt-get clean

# Cria diretório de trabalho
WORKDIR /app

# Copia todos os arquivos do projeto para o container
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão do Flask
EXPOSE 5000

# Executa o app
CMD ["python", "app/app.py"]
