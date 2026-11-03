Prova de Conceito (PoC) — Arquitetura Multi-Cloud Segura (AWS + GCP)

Este repositório contém a implementação prática da Prova de Conceito (PoC) para o artigo acadêmico "Segurança em Ambientes MultiCloud: Riscos, Desafios Arquiteturais e Padrões de Interoperabilidade em Infraestruturas de Nuvem".

📋 Visão Geral da Arquitetura

A aplicação simula uma arquitetura de microsserviços distribuída entre dois provedores de nuvem pública (AWS e GCP), aplicando princípios de Zero Trust, criptografia de dados em trânsito (HTTPS/TLS 1.3) e em repouso (AES-256), e autenticação stateless baseada em JWT (RFC 7519).

[ Cliente / Web ] 
       │ (HTTPS / TLS 1.3)
       ▼
[ Nuvem 1 - AWS (Core Application) ]
   ├─ Backend API (Python / Flask)
   └─ Banco de Dados (PostgreSQL + AES-256)
       │ (POST /audit + JWT no Header)
       ▼
[ Nuvem 2 - GCP (Audit & Logs) ]
   ├─ API de Logs (Python / Flask)
   └─ Cloud Storage (Bucket JSON + AES-256)


🛠️ Pré-requisitos

Antes de iniciar, certifique-se de ter instalado no seu ambiente:

Python 3.10+: Download Python

Git: Para controle de versão.

Bibliotecas Python necessárias:

pip install flask pyjwt requests cryptography


🚀 Como Executar o Código Passo a Passo

Para simular o ambiente completo, você precisará abrir 3 terminais distintos.

Passo 1: Iniciar o Servidor GCP (Serviço de Auditoria e Logs)

No Terminal 1, navegue até a pasta da GCP e inicie a API de logs:

cd gcp_service
python app.py


O servidor GCP ficará rodando na porta 5001 (http://localhost:5001).

Passo 2: Iniciar o Servidor AWS (Aplicação Principal)

No Terminal 2, navegue até a pasta da AWS e inicie a aplicação principal:

cd aws_service
python app.py


O servidor AWS ficará rodando na porta 5000 (http://localhost:5000).

Passo 3: Executar a Bateria Automatizada de Testes (Métricas e Estatística)

No Terminal 3, execute o script test_bateria.py na raiz do projeto para disparar 100 requisições cross-cloud e gerar o relatório estatístico:

python test_bateria.py


📊 Saída Esperada no Terminal:

O script imprimirá um resumo quantitativo:

========================================
 RESULTADOS ESTATÍSTICOS DO EXPERIMENTO 
========================================
Total de requisições: 100
Taxa de Sucesso:      100.0% (100/100)
Latência Média:       42.50 ms
Desvio Padrão:        4.20 ms
========================================
