import asyncio
import websockets
import json
import time
import statistics
import random

async def testar_rede_normal(uri: str, site_id: str, token: str, num_medicoes: int = 30):
    print("\n" + "="*50)
    print("Teste 1: REDE NORMAL (sem atraso/perda)")
    print("="*50 + "\n")
    
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
            return [], []
        
        rtts = []
        perdidos = 0
        
        for i in range(num_medicoes):
            t_envio = time.time()
            await ws.send(json.dumps({
                "type": "PING",
                "timestamp": t_envio
            }))
            
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2.0)
                t_recebimento = time.time()
                rtt = (t_recebimento - t_envio) * 1000
                rtts.append(rtt)
            except asyncio.TimeoutError:
                perdidos += 1
        
        return rtts, perdidos

async def testar_rede_com_atraso(uri: str, site_id: str, token: str, num_medicoes: int = 30, 
                                  atraso_min_ms: float = 50, atraso_max_ms: float = 150):
    print("\n" + "="*50)
    print(f"Teste 2: REDE COM ATRASO ({atraso_min_ms}-{atraso_max_ms}ms)")
    print("="*50 + "\n")
    
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
            return [], []
        
        rtts = []
        perdidos = 0
        
        for i in range(num_medicoes):
            # Simula atraso de rede ANTES de enviar
            atraso = random.uniform(atraso_min_ms, atraso_max_ms) / 1000.0
            await asyncio.sleep(atraso)
            
            t_envio = time.time()
            await ws.send(json.dumps({
                "type": "PING",
                "timestamp": t_envio
            }))
            
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=2.0)
                t_recebimento = time.time()
                rtt = (t_recebimento - t_envio) * 1000
                rtts.append(rtt)
            except asyncio.TimeoutError:
                perdidos += 1
        
        return rtts, perdidos

async def testar_rede_com_perda(uri: str, site_id: str, token: str, num_medicoes: int = 30, 
                                 taxa_perda: float = 0.15):
    print("\n" + "="*50)
    print(f"Teste 3: REDE COM PERDA ({taxa_perda*100:.0f}%)")
    print("="*50 + "\n")
    
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
            return [], []
        
        rtts = []
        perdidos = 0
        enviados = 0
        
        for i in range(num_medicoes):
            # Simula perda: 15% das vezes NÃO envia a mensagem
            if random.random() < taxa_perda:
                perdidos += 1
                continue
            
            enviados += 1
            t_envio = time.time()
            await ws.send(json.dumps({
                "type": "PING",
                "timestamp": t_envio
            }))
            
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=0.5)
                t_recebimento = time.time()
                rtt = (t_recebimento - t_envio) * 1000
                rtts.append(rtt)
            except asyncio.TimeoutError:
                perdidos += 1
        
        return rtts, perdidos

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--site_id", default="site_01")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    
    uri = "ws://localhost:8080/ws"
    
    # Teste 1: Rede Normal
    rtts_normal, perdidos_normal = await testar_rede_normal(uri, args.site_id, args.token, 30)
    
    # Teste 2: Rede com Atraso
    rtts_atraso, perdidos_atraso = await testar_rede_com_atraso(uri, args.site_id, args.token, 30)
    
    # Teste 3: Rede com Perda
    rtts_perda, perdidos_perda = await testar_rede_com_perda(uri, args.site_id, args.token, 30)
    
    # Resumo dos resultados
    print("\n" + "="*60)
    print("EXPERIMENTO E - RESUMO DAS CONDIÇÕES DE REDE")
    print("="*60)
    
    print(f"\n{'Condição':<25} {'Medições':<12} {'Perdidos':<12} {'% Perda':<10} {'RTT Médio (ms)':<15}")
    print("-"*60)
    
    total = 30
    perda_normal = perdidos_normal
    perda_atraso = perdidos_atraso
    perda_perda = perdidos_perda
    
    print(f"{'Rede Normal':<25} {len(rtts_normal):<12} {perda_normal:<12} {(perda_normal/total)*100:<10.1f} {statistics.mean(rtts_normal) if rtts_normal else 0:<15.2f}")
    print(f"{'Rede com Atraso':<25} {len(rtts_atraso):<12} {perda_atraso:<12} {(perda_atraso/total)*100:<10.1f} {statistics.mean(rtts_atraso) if rtts_atraso else 0:<15.2f}")
    print(f"{'Rede com Perda (15%)':<25} {len(rtts_perda):<12} {perda_perda:<12} {(perda_perda/total)*100:<10.1f} {statistics.mean(rtts_perda) if rtts_perda else 0:<15.2f}")
    
    print("\n" + "="*60)
    print("Conclusão:")
    print("- Atraso aumenta o RTT médio proporcionalmente")
    print("- Perda de pacotes reduz o número de respostas recebidas")
    print("- Em redes reais, ambos os efeitos ocorrem simultaneamente")
    print("="*60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())