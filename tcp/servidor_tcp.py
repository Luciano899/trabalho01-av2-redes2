import socket
import time
import struct
import hashlib

HOST = "0.0.0.0"  # importante no Docker
PORT = 12345
MATRICULA = "20249026761"
NOME = "Luciano Sousa Barbosa"
AUTH_ESPERADO = hashlib.sha256((MATRICULA + NOME).encode()).hexdigest()


def ler_bytes_exatos(conn, tamanho):
    dados = b""
    while len(dados) < tamanho:
        bloco = conn.recv(tamanho - len(dados))
        if not bloco:
            return None
        dados += bloco
    return dados


def extrair_cabecalhos(cabecalho_bytes):
    cabecalho_texto = cabecalho_bytes.decode()
    headers = {}
    for linha in cabecalho_texto.splitlines():
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            headers[chave.strip()] = valor.strip()
    return headers


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Servidor aguardando conexão...")

conn, addr = server.accept()
print(f"Cliente conectado: {addr}")

inicio = time.perf_counter()
total_recebido = 0
total_geral = 0
pacotes_recebidos = 0

with open("arquivo_recebido.txt", "wb") as f:
    while True:
        tamanho_cabecalho_bytes = ler_bytes_exatos(conn, 4)
        if tamanho_cabecalho_bytes is None:
            break

        tamanho_cabecalho = struct.unpack("!I", tamanho_cabecalho_bytes)[0]
        cabecalho_bytes = ler_bytes_exatos(conn, tamanho_cabecalho)
        if cabecalho_bytes is None:
            break

        headers = extrair_cabecalhos(cabecalho_bytes)

        tamanho_chunk_bytes = ler_bytes_exatos(conn, 4)
        if tamanho_chunk_bytes is None:
            break

        tamanho_chunk = struct.unpack("!I", tamanho_chunk_bytes)[0]
        chunk = ler_bytes_exatos(conn, tamanho_chunk)
        if chunk is None:
            break

        if headers.get("X-Custom-Auth") != AUTH_ESPERADO:
            print("Pacote ignorado: X-Custom-Auth invalido")
            continue

        f.write(chunk)
        total_recebido += len(chunk)
        total_geral += len(chunk)
        pacotes_recebidos += 1

fim = time.perf_counter()
duracao = fim - inicio
throughput_mbps = (total_geral * 8) / duracao / 1_000_000 if duracao > 0 else 0

print(f"Pacotes recebidos: {pacotes_recebidos}")
print(f"Bytes recebidos: {total_geral}")
print(f"Tempo de recepção: {duracao:.6f} s")
print(f"Throughput estimado: {throughput_mbps:.6f} Mbps")

conn.close()
server.close()