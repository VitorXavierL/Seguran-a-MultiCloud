import os
import ssl
import time
import uuid
import base64
import hashlib
import sqlite3
import datetime
import jwt
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Flask, jsonify

app = Flask(__name__)

JWT_SECRET = "chave_super_secreta_multicloud_tars_2026"
JWT_ALGORITHM = "HS256"
GCP_AUDIT_URL = os.getenv("GCP_AUDIT_URL", "http://127.0.0.1:5001/audit")
DATABASE_URL = os.getenv("DATABASE_URL") # Ex: postgresql://user:pass@localhost:5432/multicloud

# Chave AES-256 para criptografia em repouso no banco da AWS
AES_KEY = hashlib.sha256(b"chave_aes256_aws_postgres_2026").digest()

# Adaptador HTTP que exige TLSv1.3 mínimo quando operando sobre HTTPS real
class TLS13Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=ctx)

sessao_http = requests.Session()
sessao_http.mount("https://", TLS13Adapter())

def cifrar_aes256_texto(texto: str) -> str:
    aesgcm = AESGCM(AES_KEY)
    nonce = os.urandom(12)
    cifrado = aesgcm.encrypt(nonce, texto.encode("utf-8"), None)
    return base64.b64encode(nonce + cifrado).decode("utf-8")

def persistir_no_banco_aws(evento_uuid: str, evento_cifrado: str, timestamp_atual: str):
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id VARCHAR(36) PRIMARY KEY,
                evento_cifrado TEXT,
                timestamp VARCHAR(50)
            )
        """)
        cursor.execute("INSERT INTO transacoes (id, evento_cifrado, timestamp) VALUES (%s, %s, %s)",
                       (evento_uuid, evento_cifrado, timestamp_atual))
        conn.commit()
        cursor.close()
        conn.close()
    else:
        # Emulação local automática caso o servidor PostgreSQL 16.2 não esteja ativo
        conn = sqlite3.connect("aws_postgres16_sim.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id TEXT PRIMARY KEY,
                evento_cifrado TEXT,
                timestamp TEXT
            )
        """)
        cursor.execute("INSERT INTO transacoes (id, evento_cifrado, timestamp) VALUES (?, ?, ?)",
                       (evento_uuid, evento_cifrado, timestamp_atual))
        conn.commit()
        conn.close()

@app.route('/processar', methods=['POST'])
def processar_evento():
    evento_uuid = str(uuid.uuid4())
    timestamp_atual = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Cifra em AES-256 e grava no banco relacional da AWS (PostgreSQL 16.2)
    evento_cifrado = cifrar_aes256_texto("Acesso_Critico_Sistema")
    persistir_no_banco_aws(evento_uuid, evento_cifrado, timestamp_atual)

    # 2. Gera Token JWT (RFC 7519) para Zero Trust
    payload_jwt = {
        "iss": "aws-core-app",
        "aud": "gcp-audit-service",
        "uuid": evento_uuid,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    }
    token = jwt.encode(payload_jwt, JWT_SECRET, algorithm=JWT_ALGORITHM)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "uuid": evento_uuid,
        "origem": "AWS-EC2",
        "evento": "Acesso_Critico_Sistema",
        "timestamp": timestamp_atual
    }

    # 3. Medição da Latência Inter-Nuvens conforme Quadro 2: time.perf_counter()
    inicio_req = time.perf_counter()
    resposta_gcp = sessao_http.post(GCP_AUDIT_URL, json=body, headers=headers)
    fim_req = time.perf_counter()

    latencia_ms = (fim_req - inicio_req) * 1000.0

    if resposta_gcp.status_code == 200:
        dados_gcp = resposta_gcp.json()
        return jsonify({
            "status": "concluido",
            "uuid": evento_uuid,
            "latencia_inter_nuvens_ms": latencia_ms,
            "overhead_jwt_ms": dados_gcp["jwt_overhead_ms"]
        }), 200
    else:
        return jsonify({"erro": "Falha na auditoria GCP"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)