import requests
import time
import statistics

# URL da nossa aplicação principal (AWS) rodando localmente
AWS_URL = "http://localhost:5000/api/submit"
TOTAL_REQUESTS = 100

latencias = []
sucessos = 0

print(f"Iniciando bateria automatizada de {TOTAL_REQUESTS} testes Cross-Cloud...")
print("Enviando requisições (isso pode levar alguns segundos)...\n")

for i in range(TOTAL_REQUESTS):
    # Criamos um usuário diferente para cada teste para simular tráfego real
    payload = {
        "usuario": f"vitoria_teste_automatizado_{i+1}", 
        "acao": "login_teste", 
        "status": "sucesso"
    }
    
    # Marca o tempo inicial antes de disparar
    start_time = time.time()
    
    try:
        # Dispara para a AWS (que fará todo o fluxo até a GCP)
        response = requests.post(AWS_URL, json=payload, timeout=5)
        
        # Calcula o tempo total que demorou (em milissegundos)
        latencia_ms = (time.time() - start_time) * 1000 
        
        # Se a AWS e a GCP retornarem sucesso (201 Created)
        if response.status_code == 201:
            sucessos += 1
            latencias.append(latencia_ms)
            
    except requests.exceptions.RequestException as e:
        print(f"Falha na requisição {i+1}: {e}")

# Processamento Estatístico
if latencias:
    media = statistics.mean(latencias)
    desvio_padrao = statistics.stdev(latencias) if len(latencias) > 1 else 0
    taxa = (sucessos / TOTAL_REQUESTS) * 100

    print("=" * 40)
    print(" RESULTADOS ESTATÍSTICOS DO EXPERIMENTO ")
    print("=" * 40)
    print(f"Total de requisições: {TOTAL_REQUESTS}")
    print(f"Taxa de Sucesso:      {taxa:.1f}% ({sucessos}/{TOTAL_REQUESTS})")
    print(f"Latência Média:       {media:.2f} ms")
    print(f"Desvio Padrão:        {desvio_padrao:.2f} ms")
    print("=" * 40)
else:
    print("Nenhuma requisição teve sucesso. Verifique se os servidores AWS e GCP estão rodando.")