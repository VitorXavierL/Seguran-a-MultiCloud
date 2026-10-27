from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import jwt
import json
import time

app = Flask(__name__)

# A mesma chave secreta para validar a assinatura do JWT
JWT_SECRET = "super-senha-zero-trust-jwt"

# Chave AES-256 simulando o GCP Cloud KMS
AES_KEY = Fernet.generate_key()
cipher_suite = Fernet(AES_KEY)

@app.route('/api/audit', methods=['POST'])
def audit():
    inicio = time.time()
    
    # 1. Zero Trust: Filtra tráfego exigindo o JWT no Header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        print("Bloqueado: Tentativa de acesso sem Token JWT.")
        return jsonify({"erro": "Acesso negado. Token ausente."}), 401
    
    token = auth_header.split(" ")[1]
    
    # 2. Validação da Autenticidade do Token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"erro": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"erro": "Assinatura invalida"}), 401

    # 3. Gravação de Logs no Cloud Storage com AES-256
    # Extrai a identidade validada diretamente do token
    log_data = {
        "record_id": payload.get("record_id"),
        "usuario_auditado": payload.get("usuario"),
        "timestamp_validacao": time.time()
    }
    
    log_string = json.dumps(log_data).encode('utf-8')
    log_criptografado = cipher_suite.encrypt(log_string).decode('utf-8')

    # Gravação física: Simula o bucket do GCP Cloud Storage
    with open("gcp_cloud_storage_log.txt", "a") as arquivo_storage:
        arquivo_storage.write(f"{log_criptografado}\n")

    tempo_overhead = (time.time() - inicio) * 1000
    print(f"INFO: Log criptografado. Overhead JWT: {tempo_overhead:.2f} ms")

    return jsonify({"status": "audit_saved", "record_id": payload.get("record_id")}), 200

if __name__ == '__main__':
    app.run(port=5001)