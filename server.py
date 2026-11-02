from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
import json
import time
import sqlite3
import logging
import secrets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Uptime Monitor Server")

def init_db():
    conn = sqlite3.connect('uptime.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sites (
        site_id TEXT PRIMARY KEY, url TEXT, nome TEXT, token TEXT, criado_em REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, site_id TEXT, timestamp REAL, 
        status_code INTEGER, latency_ms REAL, is_alert INTEGER
    )''')
    conn.commit()
    conn.close()
init_db()

class SiteCadastro(BaseModel):
    site_id: str
    url: str
    nome: str

clients = {}
LIMITE_LATENCIA = 500.0

def gerar_token():
    return secrets.token_hex(16)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/site")
async def cadastrar_site(site: SiteCadastro):
    token = gerar_token()
    conn = sqlite3.connect('uptime.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO sites VALUES (?, ?, ?, ?, ?)", 
                  (site.site_id, site.url, site.nome, token, time.time()))
        conn.commit()
        logger.info(f"Site cadastrado: {site.site_id}")
        return {"site_id": site.site_id, "token": token, "status": "OK"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Site já cadastrado")
    finally:
        conn.close()

@app.get("/api/historico/{site_id}")
async def historico(site_id: str, limite: int = 50):
    conn = sqlite3.connect('uptime.db')
    c = conn.cursor()
    c.execute("""SELECT site_id, timestamp, status_code, latency_ms, is_alert 
                 FROM logs WHERE site_id=? ORDER BY timestamp DESC LIMIT ?""", 
              (site_id, limite))
    rows = c.fetchall()
    conn.close()
    return [{"site_id": r[0], "timestamp": r[1], "status_code": r[2], 
             "latency_ms": r[3], "is_alert": bool(r[4])} for r in rows]

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    client_id = None
    client_role = None

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "ERROR", "message": "JSON inválido"})
                continue

            msg_type = msg.get("type")

            if msg_type == "AUTH":
                client_id = msg.get("id")
                client_role = msg.get("role")
                token = msg.get("token")

                if client_role == "probe":
                    conn = sqlite3.connect('uptime.db')
                    c = conn.cursor()
                    c.execute("SELECT token FROM sites WHERE site_id=?", (client_id,))
                    row = c.fetchone()
                    conn.close()
                    if row and row[0] == token:
                        clients[client_id] = ws
                        await ws.send_json({"type": "AUTH_OK", "id": client_id})
                        logger.info(f"Probe autenticado: {client_id}")
                    else:
                        await ws.send_json({"type": "AUTH_ERROR", "message": "Token inválido"})
                elif client_role == "dashboard":
                    clients["dashboard"] = ws
                    await ws.send_json({"type": "AUTH_OK", "id": "dashboard"})
                    logger.info("Dashboard conectado")

            elif msg_type == "REPORT":
                if client_role != "probe":
                    continue
                
                site_id = msg.get("site_id")
                status_code = msg.get("status_code")
                latency_ms = msg.get("latency_ms")
                timestamp = msg.get("timestamp", time.time())

                is_alert = (latency_ms > LIMITE_LATENCIA) or (status_code >= 400)
                
                conn = sqlite3.connect('uptime.db')
                c = conn.cursor()
                c.execute("INSERT INTO logs (site_id, timestamp, status_code, latency_ms, is_alert) VALUES (?,?,?,?,?)",
                          (site_id, timestamp, status_code, latency_ms, int(is_alert)))
                conn.commit()
                conn.close()

                await ws.send_json({"type": "ACK", "status": "OK", "alert": is_alert})

                if "dashboard" in clients:
                    try:
                        await clients["dashboard"].send_json({
                            "type": "SITE_UPDATE",
                            "site_id": site_id,
                            "status_code": status_code,
                            "latency_ms": latency_ms,
                            "is_alert": is_alert,
                            "timestamp": timestamp
                        })
                    except:
                        pass
                
                if is_alert:
                    logger.warning(f"ALERTA: {site_id} status={status_code} lat={latency_ms}ms")

            elif msg_type == "PING":
                await ws.send_json({"type": "PONG", "timestamp": time.time(), "client_ts": msg.get("timestamp")})

    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado: {client_id}")
        if client_id in clients: del clients[client_id]
        if "dashboard" in clients and client_id == "dashboard": del clients["dashboard"]

if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("Servidor Uptime Monitor rodando em http://localhost:8080")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8080)