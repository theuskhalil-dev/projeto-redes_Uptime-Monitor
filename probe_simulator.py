import asyncio
import websockets
import json
import time
import random
import argparse

async def rodar_probe(site_id: str, token: str, intervalo: float = 2.0):
    uri = "ws://localhost:8080/ws"
    print(f"[{site_id}] Conectando ao servidor...")
    
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "type": "AUTH",
            "role": "probe",
            "id": site_id,
            "token": token
        }))
        
        resp = await ws.recv()
        msg = json.loads(resp)
        if msg.get("type") != "AUTH_OK":
            print(f"Erro de autenticação: {msg}")
            return
        print(f"[{site_id}] Autenticado! Monitorando a cada {intervalo}s...")
        
        contador = 0
        while True:
            if random.random() < 0.9:
                status_code = 200
                latency_ms = random.gauss(150, 40)
            else:
                status_code = random.choice([500, 502, 503])
                latency_ms = random.uniform(600, 1200)
            
            report = {
                "type": "REPORT",
                "site_id": site_id,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "timestamp": time.time()
            }
            
            await ws.send(json.dumps(report))
            contador += 1
            
            try:
                ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
                status_alert = "⚠️ ALERTA" if ack.get("alert") else "OK"
                print(f"[{site_id}] #{contador} HTTP {status_code} | {latency_ms:.1f}ms -> {status_alert}")
            except asyncio.TimeoutError:
                print(f"[{site_id}] #{contador} TIMEOUT (Sem resposta do servidor)")
            
            await asyncio.sleep(intervalo)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site_id", default="site_01", help="ID do site cadastrado")
    parser.add_argument("--token", required=True, help="Token obtido no cadastro HTTP")
    parser.add_argument("--intervalo", type=float, default=2.0, help="Intervalo em segundos")
    args = parser.parse_args()
    
    asyncio.run(rodar_probe(args.site_id, args.token, args.intervalo))