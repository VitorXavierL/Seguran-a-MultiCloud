import os
import json
import time
import base64
import hashlib
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Flask, request, jsonify

app = Flask(__name__)

# Chave secreta compartilhada (simulação de KMS/Segredo)
JWT_SECRET = "chave_super_secreta_multicloud_tars_2026"
JWT_ALGORITHM = "HS256"

# Chave simétrica de 256 bits (32 bytes) para criptografia em repouso AES-256
AES_KEY = hashlib.sha256(b"chave_aes256_gcs_multicloud_2026").digest()

# Diretório que emula o bucket do Google Cloud Storage (GCS)
GCS_BUCKET_DIR = "gcs_bucket_logs"
os.makedirs(GCS_BUCKET_DIR, exist_ok=True)

def cifrar_aes256(dados_dict: dict) -> str:
    aesgcm = AESGCM(AES_KEY)
    nonce = os.urandom(12)
    texto_plano = json.dumps(dados_dict).encode("utf-8")
    texto_cifrado = aesgcm.encrypt(nonce, texto_plano, None)
    return base64.b64encode(nonce + texto_cifrado).decode("utf-8")

@app.route('/audit', methods=['POST'])
def receive_audit_log():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"erro": "Token JWT ausente (Zero Trust bloqueou)"}), 401

    token = auth_header.split(" ")[1]

    # Medição exata conforme Quadro 2 do artigo: time.perf_counter_ns()
    inicio_jwt_ns = time.perf_counter_ns()
    try:
        jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="gcp-audit-service",
            issuer="aws-core-app"
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"erro": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"erro": "Assinatura JWT inválida"}), 401
    fim_jwt_ns = time.perf_counter_ns()

    jwt_overhead_ms = (fim_jwt_ns - inicio_jwt_ns) / 1_000_000.0

    dados_log = request.get_json()
    log_uuid = dados_log.get("uuid")

    if not log_uuid:
        return jsonify({"erro": "UUID ausente no payload"}), 400

    # Aplica criptografia em repouso AES-256 antes de gravar no Cloud Storage
    payload_criptografado = {
        "uuid": log_uuid,
        "algoritmo": "AES-256-GCM",
        "dados_cifrados": cifrar_aes256(dados_log)
    }

    caminho_arquivo = os.path.join(GCS_BUCKET_DIR, f"{log_uuid}.json")
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(payload_criptografado, f, indent=4)

    return jsonify({
        "status": "sucesso",
        "uuid_gravado": log_uuid,
        "jwt_overhead_ms": jwt_overhead_ms
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)