import socket
import json
import hashlib
import os
import sys
import time

HOST = 'servidor'
PORTA = 12345
CHUNK_SIZE = 1400
TIMEOUT = 0.5
MAX_TENTATIVAS = 10
ARQUIVO = 'output/arquivo_envio_trabalhoRedes2.txt'

matricula = '20249026761'
nome = 'Luciano Sousa Barbosa'
X_CUSTOM_AUTH = hashlib.sha256((matricula + nome).encode()).hexdigest()


def calcular_checksum_md5(dados: bytes) -> str:
    """Calcula o checksum MD5 de um bloco de dados."""
    return hashlib.md5(dados).hexdigest()


def empacotar_mensagem(mensagem: dict) -> bytes:
    """Empacota uma mensagem para JSON bytes, incluindo o campo de autenticação."""
    mensagem['X-Custom-Auth'] = X_CUSTOM_AUTH
    return json.dumps(mensagem).encode('utf-8')


def desempacotar_mensagem(pacote_bytes: bytes) -> dict | None:
    """Desempacota bytes JSON para dict e valida o campo de autenticação."""
    try:
        mensagem = json.loads(pacote_bytes.decode('utf-8'))
        if mensagem.get('X-Custom-Auth') != X_CUSTOM_AUTH:
            print('[AVISO] Resposta com X-Custom-Auth inválido — descartada.')
            return None
        return mensagem
    except Exception as e:
        print(f'[ERRO] Falha ao desempacotar: {e}')
        return None


def dividir_em_chunks(dados: bytes) -> list[bytes]:
    """
    Divide os dados do arquivo em blocos menores (chunks)
    de tamanho CHUNK_SIZE.
    """

    chunks = []

    # percorre os dados pulando de CHUNK_SIZE em CHUNK_SIZE
    for inicio in range(0, len(dados), CHUNK_SIZE):

        # define o final do bloco atual
        fim = inicio + CHUNK_SIZE

        # extrai o pedaço correspondente
        chunk = dados[inicio:fim]

        # adiciona na lista de chunks
        chunks.append(chunk)

    return chunks


def realizar_handshake(socket_cliente: socket.socket, endereco_servidor: tuple,nome_arquivo: str,
                       quantidade_chunks: int,tamanho_arquivo: int, sha256_arquivo: str) -> bool:
    
    """Realiza o handshake inicial enviando um SYN com os metadados do arquivo.
    Aguarda um SYN-ACK do servidor, com timeout e retransmissão.
    Retorna True se o handshake for bem-sucedido, ou False após esgotarr as tentativas.
    """

    syn = empacotar_mensagem({
        'tipo': 'SYN',
        'nome_arquivo': nome_arquivo,
        'total_chunks': quantidade_chunks,
        'tamanho': tamanho_arquivo,
        'sha256_arquivo': sha256_arquivo,
        'ts': time.time(),
    })
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        print(f'[SYN] Tentativa {tentativa}/{MAX_TENTATIVAS}...')
        socket_cliente.sendto(syn, endereco_servidor)
        try:
            mensagem_bruta, _ = socket_cliente.recvfrom(65507)
            resposta = desempacotar_mensagem(mensagem_bruta)
            if resposta and resposta.get('tipo') == 'SYN-ACK':
                print(f'[SYN-ACK] Conexão estabelecida com {endereco_servidor[0]}:{endereco_servidor[1]}')
                return True
        except socket.timeout:
            print('[SYN] Timeout — retransmitindo...')

    print('[ERRO] Handshake falhou após todas as tentativas.')
    return False


def enviar_stop_and_wait(socket_cliente: socket.socket, endereco_servidor: tuple, chunks: list[bytes]):
    total = len(chunks)
    seq_num = 0  # alinhado ao servidor atual, que espera seq iniciando em 0

    for chunk in chunks:
        pacote = empacotar_mensagem({
            'tipo': 'DATA',
            'seq': seq_num,
            'dado': chunk.hex(),
            'checksum': calcular_checksum_md5(chunk),
            'ts': time.time(),
        })

        tentativas = 0
        confirmado = False

        while not confirmado:
            if tentativas >= MAX_TENTATIVAS:
                raise RuntimeError(
                    f'[SAW] Chunk {seq_num} não confirmado após '
                    f'{MAX_TENTATIVAS} tentativas — abortando.'
                )

            if tentativas == 0:
                print(f'[SAW] Enviando chunk {seq_num}/{total-1} ({len(chunk)} B)...')
            else:
                print(f'[SAW] Retransmitindo chunk {seq_num} '
                      f'(tentativa {tentativas + 1}/{MAX_TENTATIVAS})...')

            socket_cliente.sendto(pacote, endereco_servidor)

            try:
                mensagem_bruta, _ = socket_cliente.recvfrom(65507)
                resposta = desempacotar_mensagem(mensagem_bruta)

                if resposta is None:
                    tentativas += 1
                    continue

                tipo_resposta = resposta.get('tipo')
                seq_resposta = resposta.get('seq')

                if tipo_resposta == 'ACK' and seq_resposta == seq_num:
                    print(f'[SAW] ACK {seq_num} recebido.')
                    confirmado = True
                elif tipo_resposta == 'NAK' and seq_resposta == seq_num:
                    print(f'[SAW] NAK {seq_num} — retransmitindo...')
                    tentativas += 1
                else:
                    print(f'[SAW] ACK/NAK inesperado (tipo={tipo_resposta}, seq={seq_resposta}) — ignora.')
                    tentativas += 1

            except socket.timeout:
                print(f'[SAW] Timeout aguardando ACK {seq_num}.')
                tentativas += 1

        seq_num += 1


def aguardar_confirmacao_final(socket_cliente: socket.socket) -> dict | None:
    for _ in range(MAX_TENTATIVAS):
        try:
            mensagem_bruta, _ = socket_cliente.recvfrom(65507)
            mensagem = desempacotar_mensagem(mensagem_bruta)
            if mensagem and mensagem.get('tipo') == 'FIN':
                return mensagem
        except socket.timeout:
            pass
    return None


def enviar_arquivo(caminho_arquivo: str, host: str = HOST, porta: int = PORTA):
    if not os.path.isfile(caminho_arquivo):
        print(f'Arquivo não encontrado: {caminho_arquivo}')
        return

    with open(caminho_arquivo, 'rb') as arquivo:
        dados = arquivo.read()

    nome_arquivo = os.path.basename(caminho_arquivo)
    sha256_arquivo = hashlib.sha256(dados).hexdigest()
    chunks = dividir_em_chunks(dados)
    total_chunks = len(chunks)
    ip_servidor = socket.gethostbyname(HOST)
    endereco_servidor = (ip_servidor, PORTA)

    print('=' * 60)
    print('  R-UDP Cliente  |  Protocolo: Stop-and-Wait')
    print(f'  Arquivo        : {nome_arquivo}  ({len(dados):,} bytes)')
    print(f'  Chunks         : {total_chunks} × {CHUNK_SIZE} B')
    print(f'  SHA-256 global : {sha256_arquivo[:24]}...')
    print(f'  X-Custom-Auth  : {X_CUSTOM_AUTH[:24]}...')
    print(f'  Destino        : {host}:{porta}')
    print('=' * 60)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_cliente:
        socket_cliente.settimeout(TIMEOUT)
        inicio = time.perf_counter()

        ok = realizar_handshake(
            socket_cliente,
            endereco_servidor,
            nome_arquivo,
            total_chunks,
            len(dados),
            sha256_arquivo,
        )
        if not ok:
            return

        try:
            enviar_stop_and_wait(socket_cliente, endereco_servidor, chunks)
        except RuntimeError as e:
            print(e)
            return

        fin = aguardar_confirmacao_final(socket_cliente)
        if fin is None:
            print('[AVISO] FIN não recebido — verifique o servidor.')
            return

        fim = time.perf_counter()
        duracao = fim - inicio

        if fin.get('status') == 'OK':
            total_enviado = len(dados)
            throughput_mbps = (total_enviado * 8) / duracao / 1_000_000 if duracao > 0 else 0

            print(f'Arquivo enviado: {caminho_arquivo}')
            print(f'Bytes enviados: {total_enviado}')
            print(f'Tempo de envio: {duracao:.6f} s')
            print(f'Throughput: {throughput_mbps:.6f} Mbps')
            print(f'  SHA-256 confirmado: {fin["sha256"][:24]}...')
        else:
            print(f'\nServidor relatou erro: {fin.get("motivo")}')


if __name__ == '__main__':
  enviar_arquivo(ARQUIVO, HOST, PORTA)
