import asyncio
import websockets
import json
import time

async def medir_throughput(uri: str, site_id: str, token: str):
    print("Conectando ao servidor...")
    
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "AUTH",
            "role": "probe",
            "id": site_id,
            "token": token
        }))
        
        resp = await ws.recv()
        if json.loads(resp).get("type") != "AUTH_OK":
            print("Erro de autenticação")
            return
        
        print("Autenticado! Testando throughput com diferentes tamanhos...\n")
        
        tamanhos = [100, 1000, 10000, 100000, 1000000]
        
        for tamanho in tamanhos:
            dados_teste = "x" * tamanho
            
            t_inicio = time.time()
            
            for _ in range(10):
                await ws.send(json.dumps({
                    "type": "REPORT",
                    "site_id": site_id,
                    "status_code": 200,
                    "latency_ms": 150.0,
                    "timestamp": time.time(),
                    "dados_extra": dados_teste
                }))
                await ws.recv()
            
            t_fim = time.time()
            tempo_total = t_fim - t_inicio
            
            bytes_total = tamanho * 10
            throughput = bytes_total / tempo_total
            
            print(f"Tamanho: {tamanho:>8} bytes | Tempo: {tempo_total:.3f}s | Throughput: {throughput/1024:.2f} KB/s")
        
        print(f"\n{'='*50}")
        print("Experimento B - Throughput concluído")
        print("{'='*50}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--site_id", default="site_01")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    
    asyncio.run(medir_throughput("ws://localhost:8080/ws", args.site_id, args.token))