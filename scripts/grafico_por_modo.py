import pandas as pd
import matplotlib.pyplot as plt

def plotar_graficos(
    cenarioA_tcp,
    cenarioB_tcp,
    cenarioC_tcp,
    cenarioA_rudp,
    cenarioB_rudp,
    cenarioC_rudp
):

    # =========================
    # LEITURA DOS DADOS
    # =========================
    tcp_tempo = [
        pd.read_csv(cenarioA_tcp)["tempo_medio_s"].values[0],
        pd.read_csv(cenarioB_tcp)["tempo_medio_s"].values[0],
        pd.read_csv(cenarioC_tcp)["tempo_medio_s"].values[0],
    ]

    rudp_tempo = [
        pd.read_csv(cenarioA_rudp)["tempo_medio_s"].values[0],
        pd.read_csv(cenarioB_rudp)["tempo_medio_s"].values[0],
        pd.read_csv(cenarioC_rudp)["tempo_medio_s"].values[0],
    ]

    tcp_vazao = [
        pd.read_csv(cenarioA_tcp)["vazao_media_mbps"].values[0],
        pd.read_csv(cenarioB_tcp)["vazao_media_mbps"].values[0],
        pd.read_csv(cenarioC_tcp)["vazao_media_mbps"].values[0],
    ]

    rudp_vazao = [
        pd.read_csv(cenarioA_rudp)["vazao_media_mbps"].values[0],
        pd.read_csv(cenarioB_rudp)["vazao_media_mbps"].values[0],
        pd.read_csv(cenarioC_rudp)["vazao_media_mbps"].values[0],
    ]

    cenarios = ["A", "B", "C"]

    # =========================
    # FUNÇÃO PARA LABELS
    # =========================
    def adicionar_labels(x, y, offset=0.0):
      for i, v in enumerate(y):
          plt.text(
              i,
              v + offset,
              f"{v:.2f}",
              ha='center',
              va='bottom',
              fontsize=9
          )

    # =========================
    # GRÁFICO 1 - TEMPO
    # =========================
    plt.figure(figsize=(10, 6))

    plt.plot(cenarios, tcp_tempo, marker="o", label="TCP")
    plt.plot(cenarios, rudp_tempo, marker="s", label="R-UDP")

    adicionar_labels(cenarios, tcp_tempo, offset=1)
    adicionar_labels(cenarios, rudp_tempo, offset=1)

    plt.title("Tempo Médio de Transferência por Cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Tempo (s)")

    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()

    plt.savefig("tempo_por_cenario.png", dpi=300)
    plt.show()

    # =========================
    # GRÁFICO 2 - VAZÃO
    # =========================
    plt.figure(figsize=(10, 6))

    plt.plot(cenarios, tcp_vazao, marker="o", label="TCP")
    plt.plot(cenarios, rudp_vazao, marker="s", label="R-UDP")

    adicionar_labels(cenarios, tcp_vazao, offset=1.2)
    adicionar_labels(cenarios, rudp_vazao, offset=-4)

    plt.title("Vazão Média por Cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Vazão (Mbps)")

    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()

    plt.savefig("vazao_por_cenario.png", dpi=300)
    plt.show()


path_cenarioA_tcp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\tcp\logs\tcp_cenario_A\metricas_calculadas_tcp_cenario_A.csv"
path_cenarioB_tcp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\tcp\logs\tcp_cenario_B\metricas_calculadas_tcp_cenario_B.csv"
path_cenarioC_tcp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\tcp\logs\tcp_cenario_C\metricas_calculadas_tcp_cenario_C.csv"
path_cenarioA_rudp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_A\metricas_calculadas_rudp_cenario_A.csv"
path_cenarioB_rudp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_B\metricas_calculadas_rudp_cenario_B.csv"
path_cenarioC_rudp = r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_C\metricas_calculadas_rudp_cenario_C.csv"
plotar_graficos(
    path_cenarioA_tcp,
    path_cenarioB_tcp,
    path_cenarioC_tcp,
    path_cenarioA_rudp,
    path_cenarioB_rudp,
    path_cenarioC_rudp
)