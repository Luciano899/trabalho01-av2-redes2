from pathlib import Path

BLOCK_SIZE = 1024  # bytes aproximados por bloco


def create_file(filename, size_mb):

    total_bytes = size_mb * 1024 * 1024

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    filename = f"{Path(filename).stem}.txt"
    filepath = output_dir / filename

    written = 0
    block_number = 1

    with open(filepath, "w", encoding="utf-8") as f:

        while written < total_bytes:

            header = f"\nBLOCO {block_number:06d}\n"

            payload_size = BLOCK_SIZE - len(header)

            payload = ("X" * payload_size)

            data = header + payload

            f.write(data)

            written += len(data.encode("utf-8"))

            percent = (written / total_bytes) * 100

            print(f"\rGerando: {percent:.1f}%", end="")

            block_number += 1

    print("\n✔ Arquivo criado:")
    print(filepath)


# =====================
# MAIN
# =====================

name = input("Nome do arquivo: ")
size = int(input("Tamanho MB: "))

create_file(name, size)