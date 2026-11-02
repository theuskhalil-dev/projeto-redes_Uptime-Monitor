import socket
import time
import statistics
import threading

PORT_TCP = 19001
PORT_UDP = 19002
NUM_MSG = 20

def tcp_server_thread(ready_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', PORT_TCP))
    sock.listen(1)
    sock.settimeout(10.0)
    ready_event.set()
    
    try:
        conn, addr = sock.accept()
        conn.settimeout(5.0)
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)
            except socket.timeout:
                break
    except socket.timeout:
        pass
    finally:
        try:
            conn.close()
        except:
            pass
        sock.close()

def udp_server_thread(received_msgs, ready_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', PORT_UDP))
    sock.settimeout(5.0)
    ready_event.set()
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                received_msgs.append(data.decode())
                sock.sendto(b"ACK", addr)
            except socket.timeout:
                break
    finally:
        sock.close()

def test_tcp():
    print("\n[Teste TCP] Iniciando...")
    rtts = []
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    
    try:
        sock.connect(('127.0.0.1', PORT_TCP))
    except ConnectionRefusedError:
        print("[TCP] ERRO: Servidor TCP não está rodando!")
        return []
    
    start_time = time.time()
    for i in range(NUM_MSG):
        msg = f"MSG_TCP_{i}".encode()
        t_send = time.time()
        sock.sendall(msg)
        
        try:
            resp = sock.recv(1024)
            t_recv = time.time()
            rtts.append((t_recv - t_send) * 1000)
        except socket.timeout:
            print(f"[TCP] Timeout na mensagem {i}")
    
    sock.close()
    tempo_total = time.time() - start_time
    
    print(f"[TCP] Concluído em {tempo_total:.3f}s")
    print(f"[TCP] Mensagens enviadas: {NUM_MSG} | Recebidas: {len(rtts)} (Perda: {((NUM_MSG - len(rtts))/NUM_MSG)*100:.0f}%)")
    if rtts:
        print(f"[TCP] RTT Médio: {statistics.mean(rtts):.2f} ms")
        print(f"[TCP] RTT Mediana: {statistics.median(rtts):.2f} ms")
    return rtts

def test_udp():
    print("\n[Teste UDP] Iniciando...")
    received_msgs = []
    ready_event = threading.Event()
    
    server = threading.Thread(target=udp_server_thread, args=(received_msgs, ready_event), daemon=True)
    server.start()
    ready_event.wait()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    rtts = []
    start_time = time.time()
    
    for i in range(NUM_MSG):
        msg = f"MSG_UDP_{i}".encode()
        t_send = time.time()
        sock.sendto(msg, ('127.0.0.1', PORT_UDP))
        try:
            sock.recvfrom(1024)
            t_recv = time.time()
            rtts.append((t_recv - t_send) * 1000)
        except socket.timeout:
            pass
    
    sock.close()
    tempo_total = time.time() - start_time
    
    print(f"[UDP] Concluído em {tempo_total:.3f}s")
    print(f"[UDP] Mensagens enviadas: {NUM_MSG} | Recebidas: {len(received_msgs)}")
    if rtts:
        print(f"[UDP] RTT Médio: {statistics.mean(rtts):.2f} ms")
        print(f"[UDP] RTT Mediana: {statistics.median(rtts):.2f} ms")
    else:
        print("[UDP] RTT Médio: N/A")

def main():
    print("="*50)
    print("Experimento D - Comparativo TCP vs UDP")
    print("="*50)
    
    tcp_ready = threading.Event()
    tcp_server = threading.Thread(target=tcp_server_thread, args=(tcp_ready,), daemon=True)
    tcp_server.start()
    tcp_ready.wait()
    
    print("Servidores iniciados. Rodando testes...\n")
    
    tcp_rtts = test_tcp()
    test_udp()
    
    print("\n" + "="*50)
    print("Conclusão:")
    print("- TCP: garante entrega e ordem, mas é mais lento")
    print("- UDP: mais rápido no RTT, mas não garante entrega nem ordem")
    print("="*50)

if __name__ == "__main__":
    main()