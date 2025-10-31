import argparse
import struct
from typing import Dict, List, Tuple

MAGIC = 0x4B575331
VERSION_V3 = 0x00030000
SECTION_ORDER = [
    "conv1_weights",
    "conv2_weights",
    "conv3_weights",
    "conv4_weights",
    "fc_weights",
]


def parse_txt(path: str) -> Tuple[int, Tuple[int, int, int, int], Dict[str, List[float]]]:
    header: Dict[str, int] = {}
    layout = (0, 0, 0, 0)
    sections: Dict[str, List[float]] = {name: [] for name in SECTION_ORDER}
    current_section = None
    remaining = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if tokens[0] in {"magic", "version", "num_classes", "reserved"}:
                header[tokens[0]] = int(tokens[1])
            elif tokens[0] == "layout":
                layout = tuple(int(tok) for tok in tokens[1:5])  # type: ignore[assignment]
            elif tokens[0] == "section":
                name = tokens[1]
                if name not in sections:
                    raise ValueError(f"Unexpected section name {name}")
                current_section = name
                remaining = int(tokens[2])
                sections[name] = []
            else:
                if current_section is None:
                    raise ValueError(f"Value without section header: {line}")
                if remaining <= 0:
                    raise ValueError(f"Too many values for section {current_section}")
                sections[current_section].append(float(tokens[0]))
                remaining -= 1

    if current_section is not None and remaining != 0:
        raise ValueError(f"Section {current_section} truncated: {remaining} values missing")

    if header.get("magic") != MAGIC or header.get("version") != VERSION_V3:
        raise ValueError("Input file header does not match KWS v3 format")

    return header["num_classes"], layout, sections


def write_bin(path: str, num_classes: int, layout: Tuple[int, int, int, int], sections: Dict[str, List[float]]) -> None:
    with open(path, "wb") as f:
        f.write(struct.pack("<IIII", MAGIC, VERSION_V3, num_classes, 0))
        f.write(struct.pack("<IIII", *layout))
        for name in SECTION_ORDER:
            values = sections[name]
            f.write(struct.pack("<{}f".format(len(values)), *values))


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert human-readable KWS weights to firmware binary format")
    parser.add_argument("txt", help="Text weights produced by export_kws_weights.py")
    parser.add_argument("--bin-out", default="bnn_weights_binary_new.bin", help="Binary output path")
    args = parser.parse_args()

    num_classes, layout, sections = parse_txt(args.txt)
    write_bin(args.bin_out, num_classes, layout, sections)
    print(f"Wrote {args.bin_out} (num_classes={num_classes}, layout={layout})")


if __name__ == "__main__":
    main()
