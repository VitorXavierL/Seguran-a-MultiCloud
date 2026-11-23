# Prova de Conceito (PoC) — Arquitetura Multi-Cloud Segura (AWS + GCP)

Este repositório contém a implementação prática da Prova de Conceito (PoC) desenvolvida para o artigo acadêmico **"Segurança em Ambientes MultiCloud: Riscos, Desafios Arquiteturais e Padrões de Interoperabilidade em Infraestruturas de Nuvem"** (Centro Universitário Impacta - 2026)[cite: 1].

---

## 📋 Visão Geral da Arquitetura

A aplicação emula uma arquitetura de microsserviços distribuída entre dois provedores de nuvem pública distintos (**AWS** e **GCP**), aplicando princípios de **Zero Trust**, criptografia de dados em trânsito (**HTTPS/TLS 1.3**) e em repouso (**AES-256-GCM**), além de autenticação *stateless* baseada em **JWT (RFC 7519)** sem dependência de conectores proprietários[cite: 1].

```text
[ Cliente / Script de Teste (test_bateria.py - 100 reqs) ] 
       │ (HTTPS / TLS 1.3)
       ▼
[ Nuvem 1 - AWS (aws_app.py) ]
   ├─ Backend API (Python 3.11.5 / Flask 3.0.0)
   └─ Banco de Dados Relacional (PostgreSQL 16.2 + Criptografia AES-256)
       │ (POST /audit + Token JWT no Header)
       ▼
[ Nuvem 2 - GCP (gcp_audit.py) ]
   ├─ API de Logs (Python 3.11.5 / Flask 3.0.0 + Validação PyJWT)
   └─ Cloud Storage (Bucket JSON cifrado em AES-256-GCM)
```

---

## 📂 Estrutura do Repositório e Como Modificar o Código

* **`aws_app.py` (Nuvem 1 - Aplicação Principal AWS):**
  * **O que faz:** Recebe eventos na rota `POST /processar`, cifra os dados sensíveis em **AES-256-GCM**, persiste no banco relacional (**PostgreSQL 16.2** via `DATABASE_URL` ou emulação SQLite local automática), assina um token **JWT (RFC 7519)** e envia o evento para a GCP medindo a latência com `time.perf_counter()`[cite: 1].
  * **Onde mexer:** Altere `JWT_SECRET` para testar falhas de assinatura, `GCP_AUDIT_URL` para apontar para um endpoint externo ou `DATABASE_URL` para conectar a uma instância AWS RDS real[cite: 1].
* **`gcp_audit.py` (Nuvem 2 - Serviço de Auditoria GCP):**
  * **O que faz:** Recebe eventos na rota `POST /audit`, bloqueia chamadas sem token (*Zero Trust*), valida a assinatura e as *claims* (`iss`, `aud`, `exp`) do JWT medindo o tempo interno em nanossegundos (`time.perf_counter_ns()`) e grava o log cifrado em **AES-256-GCM** no diretório `gcs_bucket_logs/`[cite: 1].
  * **Onde mexer:** Ajuste `GCS_BUCKET_DIR` para alterar o destino dos arquivos de auditoria ou as regras de validação de `audience` e `issuer` na função `jwt.decode()`.
* **`test_bateria.py` (Orquestrador de Métricas):**
  * **O que faz:** Dispara 100 requisições sequenciais para a AWS, confere a integridade dos 100 identificadores únicos (**UUIDs**) gravados na GCP e calcula Média, Mediana, Percentil 95 (P95) e Desvio-padrão[cite: 1, 10].
  * **Onde mexer:** Altere a constante `TOTAL_REQUISICOES = 100` na linha 7 para realizar testes de estresse com volumes maiores[cite: 6].
* **`docker-compose.yml` & `Dockerfile`:**
  * Orquestram os contêineres isolados com **PostgreSQL 16.2 oficial (`postgres:16.2-alpine`)**, servidores **Gunicorn** (4 *workers*) e execução sob usuário restrito não-root (`appuser`).

---

## 🛠️ Pré-requisitos

* **Python 3.11+** (para execução local ou disparo do script de testes)[cite: 1]
* **Docker e Docker Compose** (necessário para rodar com o servidor **PostgreSQL 16.2** completo)

Instale as dependências Python na sua máquina antes de iniciar:
```bash
pip install -r requirements.txt
```

---

## 🚀 Opção 1: Execução Completa Idêntica ao Artigo (Com PostgreSQL 16.2 via Docker)

Esta é a forma recomendada para reproduzir fielmente toda a topologia descrita na Seção 3.1 do artigo, subindo o banco de dados **PostgreSQL 16.2**, a API da AWS e a API da GCP em contêineres isolados[cite: 1]:

1. **Suba toda a infraestrutura (PostgreSQL 16.2 + AWS + GCP):**
   ```bash
   docker-compose up --build -d
   ```
2. **Aguarde 5 segundos** para o banco PostgreSQL inicializar e execute a bateria de 100 testes:
   ```bash
   python test_bateria.py
   ```
3. **Inspecione os logs cifrados gerados:**
   Os 100 arquivos `.json` cifrados em AES-256 estarão disponíveis na pasta `./gcs_bucket_logs/`.
4. **Encerre e limpe os contêineres após o teste:**
   ```bash
   docker-compose down
   ```

---

## 💻 Opção 2: Execução Rápida Local (Sem Docker)

Caso queira rodar diretamente via Python sem iniciar o Docker Desktop, o `aws_app.py` ativa automaticamente uma emulação relacional local (`aws_postgres16_sim.db`) mantendo toda a criptografia AES-256 e validação JWT[cite: 1].

Abra **3 terminais distintos** na raiz do projeto:

1. **Terminal 1 — Iniciar o Servidor GCP (Porta 5001):**
   ```bash
   python gcp_audit.py
   ```
2. **Terminal 2 — Iniciar o Servidor AWS (Porta 5000):**
   ```bash
   python aws_app.py
   ```
3. **Terminal 3 — Executar a Bateria de 100 Testes:**
   ```bash
   python test_bateria.py
   ```

---

## 📊 Resultados Consolidados (Quadro 3 do Artigo)

Ao finalizar as 100 requisições, o console exibirá as métricas empíricas consolidadas utilizadas na Seção 4.1 do artigo[cite: 1, 10]:

```text
=================================================================
 RESULTADOS CONSOLIDADOS PARA O QUADRO 3 DO ARTIGO (100 REQS)
=================================================================
Métrica                        | Média    | Mediana  | P95      | Desvio  
-----------------------------------------------------------------
Latência inter-nuvens (ms)     | 8.04     | 4.66     | 11.88    | 17.37   
Overhead do JWT (ms)           | 0.126    | 0.119    | 0.166    | 0.022   
Taxa de sucesso dos logs (%)   | 100.0    | 100.0    | 100.0    | 0.0     
=================================================================
```