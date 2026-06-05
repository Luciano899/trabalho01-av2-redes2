import socket
import json
import hashlib
import os
import time

HOST        = '0.0.0.0'
PORTA       = 12345
TAM_BUFFER  = 65507          # tamanho máximo de datagrama UDP
PASTA_SAIDA = './recebidos'

MATRICULA = '20249026761'
NOME      = 'Luciano Sousa Barbosa'
X_CUSTOM_AUTH  = hashlib.sha256((MATRICULA + NOME).encode()).hexdigest()

def calcular_checksum_md5(dado: bytes) -> str:
    """MD5 do bloco — detecta corrupção bit-a-bit."""
    return hashlib.md5(dado).hexdigest()


def empacotar_mensagem(msg: dict) -> bytes:
    """Injeta X-Custom-Auth e empacota para JSON bytes."""
    msg['X-Custom-Auth'] = X_CUSTOM_AUTH
    return json.dumps(msg).encode('utf-8')


def desempacotar_mensagem(pacote_bytes: bytes) -> dict | None:
    """Valida autenticação e desempacota bytes JSON para dict."""
    try:
        msg = json.loads(pacote_bytes.decode('utf-8'))
        if msg.get('X-Custom-Auth') != X_CUSTOM_AUTH:
            print('[AVISO] Pacote com X-Custom-Auth inválido — descartado.')
            return None
        return msg
    except Exception as e:
        print(f'[ERRO] Falha ao desempacotar pacote: {e}')
        return None


def enviar_ack(sock: socket.socket, endereco: tuple, seq: int, ok: bool):
    """Envia ACK (ok=True) ou NAK (ok=False)."""
    print(f'[{"ACK" if ok else "NAK"}] enviando seq={seq}')
    pacote_ack = empacotar_mensagem({
        'tipo': 'ACK' if ok else 'NAK',
        'seq' : seq,
        'ts'  : time.time(),
    })
    sock.sendto(pacote_ack, endereco)


def separar_cabecalho_do_payload(pacote_recebido: bytes) -> tuple[dict | None, bytes]:
    """Separa o cabeçalho JSON do payload bruto usando o delimitador \\n\\n."""
    partes = pacote_recebido.split(b'\n\n', 1)
    if len(partes) != 2:
        print('[ERRO] Pacote híbrido sem delimitador válido.')
        return None, b''

    cabecalho_bytes, payload_bruto = partes
    mensagem = desempacotar_mensagem(cabecalho_bytes)
    return mensagem, payload_bruto



def receber_saw(sock: socket.socket, cliente: tuple, meta: dict) -> bytes | None:
    """
    Protocolo Stop-and-Wait:
      1. Aguarda chunk com seq == esperado
      2. Valida checksum MD5
      3. Envia ACK → avança; envia NAK → cliente retransmite
      4. Repete até receber todos os chunks
    """
    total_chunks    = meta['total_chunks']
    chunks_recebidos = {}
    esperado_seq    = 0

    while esperado_seq < total_chunks:
        # ── aguarda próximo pacote ──────────────────────────────
        try:
            pacote_recebido, _ = sock.recvfrom(TAM_BUFFER)
        except socket.timeout:
            # sem pacote no timeout → cliente vai retransmitir por conta própria
            continue

        mensagem, dado = separar_cabecalho_do_payload(pacote_recebido)
        if mensagem is None:
            continue
        if mensagem.get('tipo') != 'DATA':
            continue                          # ignora pacotes inválidos/desconhecidos

        seq = mensagem['seq']
        checksum_recebido = mensagem['checksum_md5']

        print(f'[DATA] recebido seq={seq} esperado={esperado_seq}')

        # ── valida integridade ──────────────────────────────────
        if calcular_checksum_md5(dado) != checksum_recebido:
            print(f'[ERRO] checksum inválido em seq={seq}')
            enviar_ack(sock, cliente, seq, ok=False)
            continue
        # ── verifica sequência ──────────────────────────────────
        if seq != esperado_seq:
            print(f'[ERRO] seq fora de ordem: recebido={seq} esperado={esperado_seq}')
            enviar_ack(sock, cliente, seq, ok=False)
            continue

        # ── chunk válido ────────────────────────────────────────
        chunks_recebidos[esperado_seq] = dado
        print(f'[OK] seq={seq} confirmado')
        enviar_ack(sock, cliente, seq, ok=True)
        esperado_seq += 1

    # monta arquivo na ordem correta
    if len(chunks_recebidos) != total_chunks:
        print(f'[ERRO] Chunks incompletos: {len(chunks_recebidos)}/{total_chunks}')
        return None
    return b''.join(chunks_recebidos[i] for i in range(total_chunks))



def main():
    print('=' * 60)
    print('  R-UDP Servidor  |  Protocolo: Stop-and-Wait')
    print(f'  Porta           : {PORTA}')
    print(f'  X-Custom-Auth   : {X_CUSTOM_AUTH[:24]}…')
    print('=' * 60)

    os.makedirs(PASTA_SAIDA, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_servidor:
        socket_servidor.bind((HOST, PORTA))
        socket_servidor.settimeout(60)
        print(f'Aguardando clientes em {HOST}:{PORTA}...\n')

        while True:

            # ── 1) Handshake: espera SYN ───────────────────────
            try:
                pacote_recebido, cliente = socket_servidor.recvfrom(TAM_BUFFER)
            except socket.timeout:
                continue

            meta = desempacotar_mensagem(pacote_recebido)
            if meta is None or meta.get('tipo') != 'SYN':
                continue

            print(f'[SYN] Cliente {cliente[0]}:{cliente[1]}')
            print(f'      Arquivo : {meta["nome_arquivo"]}')
            print(f'      Chunks  : {meta["total_chunks"]}')
            print(f'      Tamanho : {meta["tamanho"]} bytes')

            # 2) Marca o início da transferência.
            inicio = time.perf_counter()

            # 3) Responde SYN-ACK ────────────────────────────
            syn_ack = empacotar_mensagem({
                'tipo' : 'SYN-ACK',
                'modo' : 'SAW',
                'ts'   : time.time(),
            })
            socket_servidor.sendto(syn_ack, cliente)

            # 4) Recebe dados (Stop-and-Wait) ────────────────
            socket_servidor.settimeout(10)
            dados = receber_saw(socket_servidor, cliente, meta)
            socket_servidor.settimeout(60)
            fim = time.perf_counter()
            duracao = fim - inicio

            if dados is None:
                print('[ERRO] Transferência falhou.\n')
                continue

            # 5) Valida SHA-256 global do arquivo ────────────
            sha_calculado = hashlib.sha256(dados).hexdigest()
            if sha_calculado != meta.get('sha256_arquivo'):
                print('[ERRO] SHA-256 global não confere — arquivo descartado.')
                socket_servidor.sendto(empacotar_mensagem({
                    'tipo'   : 'FIN',
                    'status' : 'ERRO',
                    'motivo' : 'hash_global_invalido',
                }), cliente)
                continue

            # 6) Salva arquivo ───────────────────────────────
            destino = os.path.join(PASTA_SAIDA, meta['nome_arquivo'])
            with open(destino, 'wb') as f:
                f.write(dados)
            total_recebido = len(dados)
            throughput_mbps = (total_recebido * 8) / duracao / 1_000_000 if duracao > 0 else 0

            print(f'[OK] Salvo em: {destino}')
            print(f'Pacotes recebidos: {meta["total_chunks"]}')

            print(f'Bytes recebidos: {total_recebido}')
            print(f'Tempo de recepção: {duracao:.6f} s')
            print(f'Throughput estimado: {throughput_mbps:.6f} Mbps')

            fin = empacotar_mensagem({
                'tipo'   : 'FIN',
                'status' : 'OK',
                'sha256' : sha_calculado,
            })
            print('[FIN] enviando confirmação final')
            socket_servidor.sendto(fin, cliente)
            print()


if __name__ == '__main__':
    main()
