import os
import statistics
import requests

AWS_URL = "http://127.0.0.1:5000/processar"
GCS_BUCKET_DIR = "gcs_bucket_logs"
TOTAL_REQUISICOES = 100

def calcular_percentil_95(dados):
    dados_ordenados = sorted(dados)
    indice = int(0.95 * len(dados_ordenados)) - 1
    return dados_ordenados[max(0, indice)]

def executar_experimento():
    print(f"Iniciando bateria de testes ({TOTAL_REQUISICOES} requisições)...")
    
    latencias = []
    overheads_jwt = []
    uuids_enviados = []
    sessao = requests.Session()

    for i in range(TOTAL_REQUISICOES):
        resp = sessao.post(AWS_URL)
        if resp.status_code == 200:
            dados = resp.json()
            latencias.append(dados["latencia_inter_nuvens_ms"])
            overheads_jwt.append(dados["overhead_jwt_ms"])
            uuids_enviados.append(dados["uuid"])

    # Verifica quantos UUIDs realmente foram salvos no "Google Cloud Storage"
    logs_salvos = 0
    for uid in uuids_enviados:
        if os.path.exists(os.path.join(GCS_BUCKET_DIR, f"{uid}.json")):
            logs_salvos += 1

    taxa_sucesso = (logs_salvos / TOTAL_REQUISICOES) * 100.0

    # Cálculos estatísticos para o Quadro 3 do artigo
    lat_media = statistics.mean(latencias)
    lat_mediana = statistics.median(latencias)
    lat_p95 = calcular_percentil_95(latencias)
    lat_desvio = statistics.stdev(latencias)

    jwt_media = statistics.mean(overheads_jwt)
    jwt_mediana = statistics.median(overheads_jwt)
    jwt_p95 = calcular_percentil_95(overheads_jwt)
    jwt_desvio = statistics.stdev(overheads_jwt)

    print("\n" + "="*65)
    print(" RESULTADOS CONSOLIDADOS PARA O QUADRO 3 DO ARTIGO (100 REQS)")
    print("="*65)
    print(f"{'Métrica':<30} | {'Média':<8} | {'Mediana':<8} | {'P95':<8} | {'Desvio':<8}")
    print("-" * 65)
    print(f"{'Latência inter-nuvens (ms)':<30} | {lat_media:<8.2f} | {lat_mediana:<8.2f} | {lat_p95:<8.2f} | {lat_desvio:<8.2f}")
    print(f"{'Overhead do JWT (ms)':<30} | {jwt_media:<8.3f} | {jwt_mediana:<8.3f} | {jwt_p95:<8.3f} | {jwt_desvio:<8.3f}")
    print(f"{'Taxa de sucesso dos logs (%)':<30} | {taxa_sucesso:<8.1f} | {taxa_sucesso:<8.1f} | {taxa_sucesso:<8.1f} | {'0.0':<8}")
    print("="*65)

if __name__ == "__main__":
    executar_experimento()