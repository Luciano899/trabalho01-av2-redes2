"""Calcula metricas de vazao e tempo a partir de um CSV de execucoes.

O script recebe um CSV de entrada e grava um novo CSV de saida com:
- vazao media
- vazao minima e maxima
- desvio padrao da vazao
- tempo minimo, maximo, medio e desvio padrao de transferencia
- tempo total acumulado das execucoes
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev


ARQUIVO_ENTRADA_PADRAO = Path(
	r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_C\rudp_cenario_C.csv"
)
ARQUIVO_SAIDA_PADRAO = Path(
	r"C:\Users\lucia\Desktop\UFPI\5-Periodo\Redes-2\trabalho01-av2\rudp\logs\rudp_cenario_C\metricas_calculadas_rudp_cenario_C.csv"
)


@dataclass(frozen=True)
class Metrics:
	total_execucoes: int
	vazao_media_mbps: float
	vazao_minima_mbps: float
	vazao_maxima_mbps: float
	desvio_padrao_mbps: float
	tempo_minimo_s: float
	tempo_maximo_s: float
	tempo_medio_s: float
	desvio_padrao_tempo_s: float
	tempo_total_s: float


def carregar_metricas(csv_path: Path) -> Metrics:
	throughput: list[float] = []
	tempos: list[float] = []

	with csv_path.open("r", encoding="utf-8-sig", newline="") as arquivo_csv:
		leitor = csv.DictReader(arquivo_csv)

		for linha in leitor:
			try:
				throughput.append(float(linha["throughput_mbps"]))
				tempos.append(float(linha["tempo_s"]))
			except KeyError as exc:
				raise ValueError(
					f"O arquivo {csv_path} nao possui a coluna obrigatoria {exc.args[0]!r}."
				) from exc
			except ValueError as exc:
				raise ValueError(f"Valor numerico invalido em {csv_path}: {linha}") from exc

	if not throughput:
		raise ValueError(f"O arquivo {csv_path} nao contem dados.")

	return Metrics(
		total_execucoes=len(throughput),
		vazao_media_mbps=mean(throughput),
		vazao_minima_mbps=min(throughput),
		vazao_maxima_mbps=max(throughput),
		desvio_padrao_mbps=stdev(throughput) if len(throughput) > 1 else 0.0,
		tempo_minimo_s=min(tempos),
		tempo_maximo_s=max(tempos),
		tempo_medio_s=mean(tempos),
		desvio_padrao_tempo_s=stdev(tempos) if len(tempos) > 1 else 0.0,
		tempo_total_s=sum(tempos),
	)


def salvar_metricas(csv_saida: Path, csv_entrada: Path, metricas: Metrics) -> None:
	csv_saida.parent.mkdir(parents=True, exist_ok=True)

	with csv_saida.open("w", encoding="utf-8", newline="") as arquivo_csv:
		escritor = csv.DictWriter(
			arquivo_csv,
			fieldnames=[
				"arquivo_origem",
				"total_execucoes",
				"vazao_media_mbps",
				"vazao_minima_mbps",
				"vazao_maxima_mbps",
				"desvio_padrao_mbps",
				"tempo_minimo_s",
				"tempo_maximo_s",
				"tempo_medio_s",
				"desvio_padrao_tempo_s",
				"tempo_total_s",
			],
		)
		escritor.writeheader()
		escritor.writerow(
			{
				"arquivo_origem": csv_entrada.name,
				"total_execucoes": metricas.total_execucoes,
				"vazao_media_mbps": f"{metricas.vazao_media_mbps:.6f}",
				"vazao_minima_mbps": f"{metricas.vazao_minima_mbps:.6f}",
				"vazao_maxima_mbps": f"{metricas.vazao_maxima_mbps:.6f}",
				"desvio_padrao_mbps": f"{metricas.desvio_padrao_mbps:.6f}",
				"tempo_minimo_s": f"{metricas.tempo_minimo_s:.6f}",
				"tempo_maximo_s": f"{metricas.tempo_maximo_s:.6f}",
				"tempo_medio_s": f"{metricas.tempo_medio_s:.6f}",
				"desvio_padrao_tempo_s": f"{metricas.desvio_padrao_tempo_s:.6f}",
				"tempo_total_s": f"{metricas.tempo_total_s:.6f}",
			}
		)


def main() -> int:
	csv_entrada = ARQUIVO_ENTRADA_PADRAO
	csv_saida = ARQUIVO_SAIDA_PADRAO

	metricas = carregar_metricas(csv_entrada)
	salvar_metricas(csv_saida, csv_entrada, metricas)

	print(
		f"Metricas calculadas para {csv_entrada.name} e gravadas em {csv_saida.name}."
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
