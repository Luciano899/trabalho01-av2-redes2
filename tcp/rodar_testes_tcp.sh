#!/bin/bash

# TESTE AUTOMATIZADO TCP + TC + TCPDUMP

CLIENT_CONTAINER="cliente_redes"
SERVER_CONTAINER="servidor_redes"

CLIENT_SCRIPT="/app/tcp/cliente_tcp.py"
SERVER_SCRIPT="/app/tcp/servidor_tcp.py"

LOG_DIR="./logs"
PCAP_DIR="./pcaps"

mkdir -p $LOG_DIR
mkdir -p $PCAP_DIR

# =========================================================
# ESCOLHA DO CENÁRIO
# =========================================================

echo ""
echo "========================================"
echo "Escolha o cenário:"
echo ""
echo "A -> 0% perda / 10ms delay"
echo "B -> 5% perda / 50ms delay"
echo "C -> 10% perda / 100ms delay"
echo "========================================"
echo ""

read -p "Digite A, B ou C: " CENARIO

case $CENARIO in

    A|a)
        DELAY=10
        LOSS=0
        NOME="cenario_A"
        ;;

    B|b)
        DELAY=50
        LOSS=5
        NOME="cenario_B"
        ;;

    C|c)
        DELAY=100
        LOSS=10
        NOME="cenario_C"
        ;;

    *)
        echo "Cenário inválido."
        exit 1
        ;;

esac

# =========================================================
# CSV
# =========================================================

CSV_FILE="$LOG_DIR/${NOME}.csv"

echo "execucao,bytes,tempo_s,throughput_mbps" \
> $CSV_FILE

# =========================================================
# FUNÇÕES
# =========================================================

reset_tc() {

    docker exec $CLIENT_CONTAINER \
        tc qdisc del dev eth0 root 2>/dev/null
}

apply_tc() {

    reset_tc

    docker exec $CLIENT_CONTAINER \
        tc qdisc add dev eth0 root netem \
        delay ${DELAY}ms \
        loss ${LOSS}%
}

# =========================================================
# LIMPEZA INICIAL
# =========================================================

echo ""
echo "Limpando configurações anteriores..."
echo ""

reset_tc

docker exec $SERVER_CONTAINER \
    pkill -f servidor_tcp.py 2>/dev/null

docker exec $CLIENT_CONTAINER \
    pkill tcpdump 2>/dev/null

rm -f $PCAP_DIR/${NOME}.pcap

# =========================================================
# APLICA CENÁRIO
# =========================================================

echo ""
echo "========================================"
echo "Executando cenário:"
echo ""
echo "Nome  : $NOME"
echo "Delay : ${DELAY}ms"
echo "Loss  : ${LOSS}%"
echo "========================================"
echo ""

apply_tc

echo ""
echo "TC aplicado:"
docker exec $CLIENT_CONTAINER tc qdisc show dev eth0
echo ""

# =========================================================
# INICIA TCPDUMP
# =========================================================

echo "Iniciando captura tcpdump..."

docker exec -d $CLIENT_CONTAINER \
    tcpdump -n -i eth0 -s 0 -U tcp port 12345 \
    -w /app/${NOME}.pcap

sleep 2

# =========================================================
# EXECUÇÕES
# =========================================================

for i in $(seq 1 30)
do

    echo ""
    echo "========================================"
    echo "Execução $i/30"
    echo "========================================"

    # -----------------------------------------------------
    # Reinicia servidor
    # -----------------------------------------------------

    docker exec $SERVER_CONTAINER \
        pkill -f servidor_tcp.py 2>/dev/null

    sleep 1

    docker exec -d $SERVER_CONTAINER \
        python3 $SERVER_SCRIPT

    sleep 2

    # -----------------------------------------------------
    # Executa cliente
    # -----------------------------------------------------

    OUTPUT=$(docker exec $CLIENT_CONTAINER \
        python3 $CLIENT_SCRIPT)

    echo "$OUTPUT"

    # -----------------------------------------------------
    # Salva log bruto
    # -----------------------------------------------------

    echo "$OUTPUT" \
        > $LOG_DIR/${NOME}_${i}.log

    # -----------------------------------------------------
    # Extrai métricas
    # -----------------------------------------------------

    BYTES=$(echo "$OUTPUT" \
        | grep "Bytes enviados" \
        | awk '{print $3}')

    TEMPO=$(echo "$OUTPUT" \
        | grep "Tempo de envio" \
        | awk '{print $4}')

    THROUGHPUT=$(echo "$OUTPUT" \
        | grep "Throughput" \
        | awk '{print $2}')

    # -----------------------------------------------------
    # Salva CSV
    # -----------------------------------------------------

    echo "$i,$BYTES,$TEMPO,$THROUGHPUT" \
        >> $CSV_FILE

    sleep 2

done

# =========================================================
# FINALIZA TCPDUMP
# =========================================================

echo ""
echo "Encerrando tcpdump..."

docker exec $CLIENT_CONTAINER \
    pkill tcpdump

sleep 2

# =========================================================
# COPIA PCAP
# =========================================================

echo ""
echo "Copiando PCAP..."

docker cp \
$CLIENT_CONTAINER:/app/${NOME}.pcap \
$PCAP_DIR/${NOME}.pcap

# =========================================================
# LIMPEZA FINAL
# =========================================================

reset_tc

docker exec $SERVER_CONTAINER \
    pkill -f servidor_tcp.py 2>/dev/null

# =========================================================
# FINAL
# =========================================================

echo ""
echo "========================================"
echo "TESTES FINALIZADOS"
echo "========================================"
echo ""
echo "CSV  : $CSV_FILE"
echo "PCAP : $PCAP_DIR/${NOME}.pcap"
echo ""
echo "Logs individuais:"
echo "$LOG_DIR/"
echo ""