# Utilizando imagem oficial minimalista baseada em Debian
FROM python:3.11-slim

# Metadados acadêmicos
LABEL maintainer="Pesquisa MultiCloud Security"
LABEL version="1.0"

# Impede a gravação de arquivos .pyc e força o log no stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências isoladamente para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação (substituir <modulo.py> pelo módulo desejado no CI/CD)
COPY aws_app.py /app/app.py

# Cria um usuário não-root por questões de segurança (Zero Trust)
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expõe a porta padrão do micro-framework
EXPOSE 5000

# Executa com Gunicorn para suportar concorrência em produção
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]