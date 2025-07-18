
# Imagem base com Python
FROM python:3.11-slim

# Instalar dependências do sistema (Poppler incluso)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && apt-get clean

# Criar diretório de trabalho
WORKDIR /app

# Copiar todos os arquivos
COPY . .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão do Flask
EXPOSE 5000

# Comando para rodar o Flask
CMD ["python", "app/app.py"]

