from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import re


# Paleta em tons científicos/neutros
# TCP  -> cinza escuro
# R-UDP -> cinza claro
PROTOCOL_COLORS = [
    "#4D4D4D",
    "#B0B0B0",
    "#D9D9D9"
]

# Cor exclusiva para desvio padrão
ERROR_BAR_COLOR = "#163A5F"


def load_data(csv_path: Path) -> dict[str, pd.DataFrame]:
    """
    Retorna:
        {
            nome_cenario: DataFrame
        }

    Cada DataFrame possui:
        - Protocolo
        - Vazão média (Mbps)
        - Desvio padrão da vazão
        - Tempo médio (s)
        - Desvio padrão do tempo
    """

    raw = csv_path.read_text(
        encoding="utf-8-sig"
    )

    lines = raw.splitlines()

    scenario_idx = [
        i for i, line in enumerate(lines)
        if (
            re.search(r"Cenário", line, re.IGNORECASE)
            and "Métrica" not in line
            and line.strip()
        )
    ]

    scenarios = {}

    for start in scenario_idx:

        scenario_name = re.split(
            r"\t|;",
            lines[start]
        )[0].strip()

        # encontra cabeçalho
        header_line = start + 1

        while (
            header_line < len(lines)
            and not lines[header_line].strip()
        ):
            header_line += 1

        if header_line >= len(lines):
            continue

        cols = [
            c.strip()
            for c in re.split(
                r"\t|;",
                lines[header_line]
            )
        ]

        protocols = [
            c for c in cols
            if c and c.lower() != "métrica"
        ]

        metrics = {
            p: {}
            for p in protocols
        }

        next_block = (
            scenario_idx[
                scenario_idx.index(start) + 1
            ]
            if start != scenario_idx[-1]
            else len(lines)
        )

        for row_idx in range(
            header_line + 1,
            next_block
        ):

            line = lines[row_idx].strip()

            if not line:
                continue

            parts = [
                c.strip()
                for c in re.split(r"\t|;", line)
            ]

            if not parts[0]:
                continue

            metric_name = parts[0]

            for p_i, protocol in enumerate(protocols):

                val_str = (
                    parts[p_i + 1]
                    if p_i + 1 < len(parts)
                    else ""
                )

                val_str = val_str.replace(",", ".")

                try:
                    metrics[protocol][metric_name] = float(val_str)

                except ValueError:
                    metrics[protocol][metric_name] = np.nan

        records = []

        for protocol, metric in metrics.items():

            records.append({
                "Protocolo":
                    protocol,

                "Vazão média (Mbps)":
                    metric.get(
                        "Vazão média (Mbps)",
                        np.nan
                    ),

                "Desvio padrão da vazão":
                    metric.get(
                        "Desvio padrão da vazão",
                        np.nan
                    ),

                "Tempo médio (s)":
                    metric.get(
                        "Tempo médio (s)",
                        np.nan
                    ),

                "Desvio padrão do tempo":
                    metric.get(
                        "Desvio padrão do tempo",
                        np.nan
                    ),
            })

        scenarios[scenario_name] = pd.DataFrame(records)

    return scenarios


def set_rcparams() -> None:

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 300,
    })


def plot_bar_chart(
    df: pd.DataFrame,
    scenario_name: str,
    value_col: str,
    error_col: str,
    ylabel: str,
    output_path: Path,
) -> None:

    protocols = df["Protocolo"].tolist()

    values = df[value_col].tolist()

    errors = df[error_col].tolist()

    set_rcparams()

    fig, ax = plt.subplots(
        figsize=(6.5, 5)
    )

    colors = PROTOCOL_COLORS[:len(protocols)]

    bars = ax.bar(
        protocols,

        values,

        color=colors,

        edgecolor="black",

        linewidth=1.0,

        yerr=errors,

        capsize=5,

        error_kw=dict(
            elinewidth=0.9,
            ecolor=ERROR_BAR_COLOR,
            capthick=0.9
        ),
    )

    upper_limit = max(
        value + error
        for value, error in zip(values, errors)
        if not np.isnan(value)
    )

    for i, (bar, value) in enumerate(
        zip(bars, values)
    ):

        if np.isnan(value):
            continue

        # barras pequenas
        if value < (upper_limit * 0.12):

            ax.text(
                bar.get_x() + bar.get_width() / 2,

                bar.get_height() + upper_limit * 0.02,

                f"{value:.3f}",

                ha="center",

                va="bottom",

                fontsize=9,

                color="black"
            )

        # barras normais
        else:

            text_color = (
                "white"
                if i == 0
                else "black"
            )

            ax.text(
                bar.get_x() + bar.get_width() / 2,

                bar.get_height() / 2,

                f"{value:.3f}",

                ha="center",

                va="center",

                fontsize=9,

                color=text_color
            )

    ax.set_ylabel(ylabel)

    ax.set_xlabel("Protocolo")

    ax.set_ylim(
        0,
        upper_limit * 1.30
    )

    ax.grid(
        axis="y",
        linestyle="--",
        linewidth=0.6,
        alpha=0.6
    )

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    plt.tight_layout(
        pad=1.2
    )

    fig.savefig(
        output_path.with_suffix(".pdf"),
        bbox_inches="tight"
    )

    fig.savefig(
        output_path.with_suffix(".png"),
        dpi=600,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(
        f"  {output_path.with_suffix('.pdf')}"
    )

    print(
        f"  {output_path.with_suffix('.png')}"
    )


def sanitize(name: str) -> str:
    """
    Remove caracteres inválidos
    para nome de arquivo
    """

    return re.sub(
        r"[^\w\-]",
        "_",
        name
    ).strip("_")


def main() -> None:

    base_dir = Path(__file__).resolve().parent

    csv_path = (
        base_dir /
        "cenario_A_TCP_RUDP.csv"
    )

    scenarios = load_data(csv_path)

    print(
        f"Cenários encontrados: "
        f"{list(scenarios.keys())}\n"
    )

    for scenario_name, df in scenarios.items():

        slug = sanitize(scenario_name)

        print(
            f"[{scenario_name}] "
            f"— Vazão Média:"
        )

        plot_bar_chart(
            df=df,

            scenario_name=scenario_name,

            value_col="Vazão média (Mbps)",

            error_col="Desvio padrão da vazão",

            ylabel="Vazão Média (Mbps)",

            output_path=(
                base_dir /
                f"figura_vazao_{slug}"
            ),
        )

        print(
            f"[{scenario_name}] "
            f"— Tempo de Transferência:"
        )

        plot_bar_chart(
            df=df,

            scenario_name=scenario_name,

            value_col="Tempo médio (s)",

            error_col="Desvio padrão do tempo",

            ylabel="Tempo de Transferência (s)",

            output_path=(
                base_dir /
                f"figura_tempo_{slug}"
            ),
        )

    print("\nFinalizado.")


if __name__ == "__main__":
    main()