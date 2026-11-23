# Utilizando imagem oficial minimalista baseada em Debian (Python 3.11 conforme Seção 3.1)
FROM python:3.11-slim

# Metadados acadêmicos
LABEL maintainer="Grupo TARS - Centro Universitário Impacta"
LABEL version="1.1"
LABEL description="PoC Arquitetura Multi-Cloud Segura (AWS + GCP)"

# Impede a gravação de arquivos .pyc e força o log no stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências isoladamente para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os scripts da PoC
COPY aws_app.py gcp_audit.py test_bateria.py /app/

# Cria diretório de logs (GCS simulado) e configura usuário não-root (Zero Trust)
RUN mkdir -p /app/gcs_bucket_logs && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expõe as portas da AWS (5000) e da GCP (5001)
EXPOSE 5000 5001

# Executa com Gunicorn suportando concorrência (padrão sobe a API da AWS na porta 5000)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "aws_app:app"]