import pandas as pd
import matplotlib.pyplot as plt

def plot_throughput_curve(tcp_csv, rudp_csv, output_name="throughput_curve_cenario_A.png"):
    # Leitura dos dados
    tcp = pd.read_csv(tcp_csv)
    rudp = pd.read_csv(rudp_csv)

    # Ordena por execução (segurança)
    tcp = tcp.sort_values("execucao")
    rudp = rudp.sort_values("execucao")

    # Configuração do estilo científico
    plt.figure(figsize=(10, 6))

    # TCP
    plt.plot(
        tcp["execucao"],
        tcp["throughput_mbps"],
        marker="o",
        linestyle="-",
        label="TCP"
    )

    # R-UDP
    plt.plot(
        rudp["execucao"],
        rudp["throughput_mbps"],
        marker="s",
        linestyle="-",
        label="R-UDP"
    )

    # Títulos e labels
    plt.xlabel("Execução", fontsize=12)
    plt.ylabel("Throughput (Mbps)", fontsize=12)

    # Grade leve (estilo paper)
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)

    # Legenda
    plt.legend()

    # Layout compacto
    plt.tight_layout()

    # Salvar em alta resolução (padrão artigo)
    plt.savefig(output_name, dpi=300)

    # Mostrar
    plt.show()


# Exemplo de uso:
plot_throughput_curve(r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\tcp\logs\tcp_cenario_A\cenario_A.csv", r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_A\rudp_cenario_A.csv", output_name="throughput_curve_cenario_A.png")