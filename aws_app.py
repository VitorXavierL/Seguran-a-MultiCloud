from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import jwt
import requests
import datetime
import uuid
import os

app = Flask(__name__)

# Simula o banco PostgreSQL 16.2 localmente na sua pasta
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aws_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Chaves de segurança (em produção ficam no AWS KMS)
JWT_SECRET = "super-senha-zero-trust-jwt"
# Gera uma chave AES-256 em tempo de execução para criptografia
AES_KEY = Fernet.generate_key()
cipher_suite = Fernet(AES_KEY)

# Modelo do Banco de Dados
class CoreData(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    encrypted_payload = db.Column(db.String(500))

# Cria o arquivo do banco de dados na primeira execução
with app.app_context():
    db.create_all()

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    record_id = str(uuid.uuid4())

    # 1. Criptografia em repouso AES-256 e gravação no DB
    dados_string = str(data).encode('utf-8')
    dados_criptografados = cipher_suite.encrypt(dados_string)
    
    novo_registro = CoreData(id=record_id, encrypted_payload=dados_criptografados.decode('utf-8'))
    db.session.add(novo_registro)
    db.session.commit()

    # 2. Geração do Token JWT (Zero Trust - RFC 7519)
    payload_jwt = {
        "record_id": record_id,
        "usuario": data.get("usuario"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    }
    token = jwt.encode(payload_jwt, JWT_SECRET, algorithm="HS256")

    # 3. Segurança Cross-Cloud: Envio com JWT no Header
    gcp_url = os.environ.get("GCP_AUDIT_URL", "http://localhost:5001/api/audit")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # A AWS envia a requisição de auditoria para a GCP
        resposta_gcp = requests.post(gcp_url, json={"trigger": "audit"}, headers=headers)
        status_gcp = "synced" if resposta_gcp.status_code == 200 else "failed"
    except Exception as e:
        status_gcp = "failed"

    return jsonify({"status": "success", "record_id": record_id, "audit_status": status_gcp}), 201

if __name__ == '__main__':
    app.run(port=5000)