import asyncio
import websockets
import json
import time
import statistics

async def medir_rtt(uri: str, site_id: str, token: str, num_medicoes: int = 30):
    print(f"Conectando ao servidor...")
    
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
        
        print(f"Autenticado! Medindo RTT {num_medicoes} vezes...\n")
        
        rtts = []
        for i in range(num_medicoes):
            t_envio = time.time()
            await ws.send(json.dumps({
                "type": "PING",
                "timestamp": t_envio
            }))
            
            resp = await ws.recv()
            t_recebimento = time.time()
            
            rtt = (t_recebimento - t_envio) * 1000
            rtts.append(rtt)
            
            print(f"Medição {i+1:2d}: RTT = {rtt:.2f} ms")
            await asyncio.sleep(0.1)
        
        print(f"\n{'='*50}")
        print(f"Resultados do Experimento A - RTT")
        print(f"{'='*50}")
        print(f"Número de medições: {len(rtts)}")
        print(f"Média: {statistics.mean(rtts):.2f} ms")
        print(f"Mediana: {statistics.median(rtts):.2f} ms")
        print(f"Desvio padrão: {statistics.stdev(rtts):.2f} ms")
        print(f"Mínimo: {min(rtts):.2f} ms")
        print(f"Máximo: {max(rtts):.2f} ms")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--site_id", default="site_01")
    parser.add_argument("--token", required=True)
    parser.add_argument("--medicoes", type=int, default=30)
    args = parser.parse_args()
    
    asyncio.run(medir_rtt("ws://localhost:8080/ws", args.site_id, args.token, args.medicoes))