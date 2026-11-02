import asyncio
import websockets
import json
import time
import statistics

async def cliente_concorrente(cliente_id: int, uri: str, site_id: str, token: str, duracao: float = 10.0):
    rtts = []
    try:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({
                "type": "AUTH",
                "role": "probe",
                "id": site_id,
                "token": token
            }))
            
            resp = await ws.recv()
            if json.loads(resp).get("type") != "AUTH_OK":
                print(f"Cliente {cliente_id}: Falha na autenticação")
                return []
            
            print(f"Cliente {cliente_id} conectado!")
            t_fim = time.time() + duracao
            
            while time.time() < t_fim:
                t_envio = time.time()
                await ws.send(json.dumps({
                    "type": "REPORT",
                    "site_id": site_id,
                    "status_code": 200,
                    "latency_ms": 150.0,
                    "timestamp": time.time()
                }))
                
                await ws.recv()
                t_recebimento = time.time()
                
                rtt = (t_recebimento - t_envio) * 1000
                rtts.append(rtt)
                
                await asyncio.sleep(0.5)
    except Exception as e:
        print(f"Cliente {cliente_id} erro: {e}")
    
    return rtts

async def testar_concorrencia(uri: str, site_id: str, token: str, num_clientes: int):
    print(f"\n{'='*50}")
    print(f"Experimento C - Concorrência ({num_clientes} clientes)")
    print(f"{'='*50}\n")
    
    tarefas = [
        cliente_concorrente(i, uri, site_id, token, duracao=10.0)
        for i in range(num_clientes)
    ]
    
    resultados = await asyncio.gather(*tarefas)
    
    todos_rtts = []
    for idx, cliente_rtts in enumerate(resultados):
        print(f"Cliente {idx}: {len(cliente_rtts)} medições")
        todos_rtts.extend(cliente_rtts)
    
    if todos_rtts:
        print(f"\n{'='*50}")
        print(f"Resultados Consolidados ({num_clientes} clientes)")
        print(f"{'='*50}")
        print(f"Total de medições: {len(todos_rtts)}")
        print(f"Média RTT: {statistics.mean(todos_rtts):.2f} ms")
        print(f"Mediana RTT: {statistics.median(todos_rtts):.2f} ms")
        print(f"Desvio padrão: {statistics.stdev(todos_rtts):.2f} ms")
        print(f"Mínimo: {min(todos_rtts):.2f} ms")
        print(f"Máximo: {max(todos_rtts):.2f} ms")
    else:
        print("Nenhuma medição realizada")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--site_id", default="site_01")
    parser.add_argument("--token", required=True)
    parser.add_argument("--clientes", type=int, default=5)
    args = parser.parse_args()
    
    asyncio.run(testar_concorrencia("ws://localhost:8080/ws", args.site_id, args.token, args.clientes))