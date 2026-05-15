import socket
import hashlib
import struct
import time

HOST = 'servidor'
PORT = 5000

matricula = "20249026761"
nome = "Luciano Sousa Barbosa"

auth = hashlib.sha256((matricula + nome).encode()).hexdigest()
arquivo_entrada = "output/arquivo_teste_r-udp_tcp.txt"


def enviar_framed(sock, seq, chunk):
    cabecalho = (
        f"X-Custom-Auth: {auth}\n"
        f"Content-Type: application/octet-stream\n"
        f"Chunk-Seq: {seq}\n"
    ).encode()
    sock.sendall(struct.pack("!I", len(cabecalho)))
    sock.sendall(cabecalho)
    sock.sendall(struct.pack("!I", len(chunk)))
    sock.sendall(chunk)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

inicio = time.perf_counter()
client.connect((HOST, PORT))

total_enviado = 0
with open(arquivo_entrada, "rb") as f:
    sequencia = 1
    while True:
        chunk = f.read(1024)
        if not chunk:
            break
        enviar_framed(client, sequencia, chunk)
        total_enviado += len(chunk)
        sequencia += 1

client.shutdown(socket.SHUT_WR)
fim = time.perf_counter()
duracao = fim - inicio
throughput_mbps = (total_enviado * 8) / duracao / 1_000_000 if duracao > 0 else 0

print(f"Arquivo enviado: {arquivo_entrada}")
print(f"Bytes enviados: {total_enviado}")
print(f"Tempo de envio: {duracao:.6f} s")
print(f"Throughput: {throughput_mbps:.6f} Mbps")

client.close()