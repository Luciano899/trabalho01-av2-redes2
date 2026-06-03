#!/bin/bash


# TESTE AUTOMATIZADO RUDP + TC + TCPDUMP

# Executa 30 transferências RUDP em UM cenário escolhido


CLIENT_CONTAINER="cliente_redes"
SERVER_CONTAINER="servidor_redes"

CLIENT_SCRIPT="/app/rudp/cliente_rudp.py"
SERVER_SCRIPT="/app/rudp/servidor_rudp.py"
NET_IFACE="eth0"

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
        NOME="rudp_cenario_A"
        ;;

    B|b)
        DELAY=50
        LOSS=5
        NOME="rudp_cenario_B"
        ;;

    C|c)
        DELAY=100
        LOSS=10
        NOME="rudp_cenario_C"
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
PCAP_EXEC_DIR="${PCAP_DIR}/${NOME}_execucoes"

echo "execucao,bytes,tempo_s,throughput_mbps" \
> $CSV_FILE

# =========================================================
# FUNÇÕES
# =========================================================

reset_tc() {

    docker exec $CLIENT_CONTAINER \
    tc qdisc del dev $NET_IFACE root 2>/dev/null
}

apply_tc() {

    reset_tc

    docker exec $CLIENT_CONTAINER \
        tc qdisc add dev $NET_IFACE root netem \
        delay ${DELAY}ms \
        loss ${LOSS}%
}

iniciar_tcpdump() {
    ARQ_PCAP="$1"
    docker exec $CLIENT_CONTAINER sh -c \
    "tcpdump -n -i ${NET_IFACE} -s 0 -U udp port 12345 -w /app/${ARQ_PCAP} >/dev/null 2>&1 & echo \$!"
}

encerrar_tcpdump() {
    PID_TCPDUMP="$1"
    docker exec $CLIENT_CONTAINER sh -c "kill -INT ${PID_TCPDUMP} 2>/dev/null"
}

# =========================================================
# LIMPEZA INICIAL
# =========================================================

echo ""
echo "Limpando configurações anteriores..."
echo ""

reset_tc

docker exec $SERVER_CONTAINER \
    pkill -f servidor_rudp.py 2>/dev/null

docker exec $CLIENT_CONTAINER \
    pkill tcpdump 2>/dev/null

rm -f $PCAP_DIR/${NOME}.pcap
rm -rf $PCAP_EXEC_DIR
mkdir -p $PCAP_EXEC_DIR

docker exec $CLIENT_CONTAINER sh -c \
    "rm -f /app/${NOME}.pcap /app/${NOME}_exec_*.pcap"

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
docker exec $CLIENT_CONTAINER tc qdisc show dev $NET_IFACE
echo ""

# =========================================================
# INICIA TCPDUMP
# =========================================================

echo "Iniciando captura tcpdump..."

PID_TCPDUMP_COMPLETO=$(iniciar_tcpdump "${NOME}.pcap")

sleep 2

# =========================================================
# EXECUÇÕES
# =========================================================

TOTAL_EXECUCOES=30

for i in $(seq 1 $TOTAL_EXECUCOES)
do

    echo ""
    echo "========================================"
    echo "Execução $i/$TOTAL_EXECUCOES"
    echo "========================================"

    # -----------------------------------------------------
    # Reinicia servidor
    # -----------------------------------------------------

    docker exec $SERVER_CONTAINER \
        pkill -f servidor_rudp.py 2>/dev/null

    sleep 1

    docker exec -d $SERVER_CONTAINER \
        python3 $SERVER_SCRIPT

    sleep 2

    # -----------------------------------------------------
    # Executa cliente
    # -----------------------------------------------------

    PCAP_EXEC="${NOME}_exec_${i}.pcap"
    PID_TCPDUMP_EXEC=$(iniciar_tcpdump "${PCAP_EXEC}")

    sleep 1

    OUTPUT=$(docker exec $CLIENT_CONTAINER \
        python3 $CLIENT_SCRIPT)

    sleep 2

    encerrar_tcpdump "$PID_TCPDUMP_EXEC"

    sleep 1

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

    docker cp \
        $CLIENT_CONTAINER:/app/${PCAP_EXEC} \
        $PCAP_EXEC_DIR/${PCAP_EXEC}

    sleep 2

done

# =========================================================
# FINALIZA TCPDUMP
# =========================================================

echo ""
echo "Encerrando tcpdump..."

encerrar_tcpdump "$PID_TCPDUMP_COMPLETO"

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
    pkill -f servidor_rudp.py 2>/dev/null

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
echo "PCAPs individuais: $PCAP_EXEC_DIR"
echo ""
echo "Logs individuais:"
echo "$LOG_DIR/"
echo ""