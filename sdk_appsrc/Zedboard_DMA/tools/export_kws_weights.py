import argparse
import struct
from typing import Dict, Iterable, Tuple

import torch

MAGIC = 0x4B575331  # 'KWS1'
VERSION_V3 = 0x00030000

SECTION_ORDER = [
    "conv1_weights",
    "conv2_weights",
    "conv3_weights",
    "conv4_weights",
    "fc_weights",
]


def _get_tensor(state: Dict[str, torch.Tensor], candidates: Iterable[str]) -> torch.Tensor:
    for key in candidates:
        if key in state:
            return state[key].float().contiguous()
    raise KeyError(f"None of the keys {list(candidates)} found in checkpoint")


def _infer_conv_weight(state: Dict[str, torch.Tensor], prefix: str) -> torch.Tensor:
    candidates = (
        f"{prefix}.weight",
        f"{prefix}.real_weight",
        f"{prefix}.0.weight",
    )
    return _get_tensor(state, candidates)


def extract_sections(state: Dict[str, torch.Tensor]) -> Tuple[Dict[str, torch.Tensor], Tuple[int, int, int, int], int]:
    sections: Dict[str, torch.Tensor] = {}

    conv1_w = _infer_conv_weight(state, "conv1")
    conv2_w = _infer_conv_weight(state, "conv2")
    conv3_w = _infer_conv_weight(state, "conv3")
    conv4_w = _infer_conv_weight(state, "conv4")
    fc_w = _get_tensor(state, ("fc_out.weight", "classifier.weight", "fc.weight"))

    sections["conv1_weights"] = conv1_w.view(-1)
    sections["conv2_weights"] = conv2_w.view(-1)
    sections["conv3_weights"] = conv3_w.view(-1)
    sections["conv4_weights"] = conv4_w.view(-1)
    sections["fc_weights"] = fc_w.view(-1)

    layout = (
        conv1_w.shape[0],
        conv2_w.shape[0],
        conv3_w.shape[0],
        conv4_w.shape[0],
    )
    num_classes = fc_w.shape[0]

    return sections, layout, num_classes


def write_txt(path: str, num_classes: int, layout: Tuple[int, int, int, int], sections: Dict[str, torch.Tensor]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# KWS weight export (version v3)\n")
        f.write(f"magic {MAGIC}\n")
        f.write(f"version {VERSION_V3}\n")
        f.write(f"num_classes {num_classes}\n")
        f.write("reserved 0\n")
        f.write("layout {} {} {} {}\n".format(*layout))
        for name in SECTION_ORDER:
            tensor = sections[name]
            flat = tensor.cpu().numpy()
            f.write(f"section {name} {flat.size}\n")
            for val in flat:
                f.write(f"{float(val):.8e}\n")


def write_bin(path: str, num_classes: int, layout: Tuple[int, int, int, int], sections: Dict[str, torch.Tensor]) -> None:
    with open(path, "wb") as f:
        f.write(struct.pack("<IIII", MAGIC, VERSION_V3, num_classes, 0))
        f.write(struct.pack("<IIII", *layout))
        for name in SECTION_ORDER:
            data = sections[name].cpu().numpy().astype("<f4", copy=False)
            f.write(data.tobytes(order="C"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export KWS weights to text + bin files compatible with the firmware")
    parser.add_argument("checkpoint", help="Path to PyTorch checkpoint (.pt)")
    parser.add_argument("--txt-out", default="kws_weights.txt", help="Text output file")
    parser.add_argument("--bin-out", default="bnn_weights_binary_new.bin", help="Binary output file")
    args = parser.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    if isinstance(ckpt, dict) and "model" in ckpt:
        state = ckpt["model"]
        num_classes = int(ckpt.get("num_classes", 0) or ckpt.get("args", {}).get("num_classes", 0))
    else:
        state = ckpt
        num_classes = 0

    sections, layout, inferred_classes = extract_sections(state)
    if num_classes == 0:
        num_classes = inferred_classes
    elif num_classes != inferred_classes:
        raise ValueError(f"Checkpoint num_classes ({num_classes}) does not match fc weight rows ({inferred_classes})")

    write_txt(args.txt_out, num_classes, layout, sections)
    write_bin(args.bin_out, num_classes, layout, sections)

    print(
        "Exported weights to {} and {} (num_classes={}, layout={})".format(
            args.txt_out, args.bin_out, num_classes, layout
        )
    )


if __name__ == "__main__":
    main()
