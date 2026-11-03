# Uptime Monitor - Projeto de Redes de Computadores

## Integrantes
- Matheus Hassan Ribeiro Khalil - 232005100
- Gabriela Seguins de Paula - 242004180
- Vitor Gomes Santos - 252013923

## Descrição
Sistema distribuído de monitoramento de status de serviços (Uptime Monitor). 
O sistema utiliza HTTP para cadastro e WebSocket para monitoramento em tempo real, 
com geração de alertas automáticos baseada em latência e códigos de erro HTTP.

## Tecnologias
- Python 3.13 (FastAPI, Uvicorn, WebSockets)
- HTML5/CSS3/JavaScript (Dashboard)
- SQLite (Persistência)

## Instalação e Execução
1. Instale as dependências: `pip install -r requirements.txt`
2. Inicie o servidor: `python server.py`
3. Cadastre um site via HTTP (ex: curl ou Postman para POST /api/site)
4. Abra o dashboard em `http://localhost:8080`
5. Inicie o agente de monitoramento: `python probe_simulator.py --site_id site_01 --token SEU_TOKEN`

## Experimentos Realizados
- **A (RTT):** Medição de 30 pings via WebSocket.
- **B (Throughput):** Transferência de payloads de 100B a 1MB.
- **C (Concorrência):** Teste com 1, 2 e 5 clientes simultâneos.
- **D (TCP vs UDP):** Microteste de sockets comparando confiabilidade e RTT.
- **E (Condições de Rede):** Simulação de atraso e perda de pacotes via código.

## Estrutura do Projeto
- `server.py`: Servidor central (API + WS).
- `probe_simulator.py`: Agente que simula o monitoramento.
- `index.html`: Dashboard web.
- `experiments/`: Scripts para os 5 experimentos de rede.
