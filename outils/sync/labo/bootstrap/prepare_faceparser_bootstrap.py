#!/usr/bin/env python3
"""Build a private FaceParser overlay from the pinned MuseTalk 0a89dec text sources.

This tool never edits the upstream source tree. It validates all four pinned input
files and all generated Python before reserving a fresh output directory. Published
files are created exclusively; an interrupted publication is retained for inspection.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

UPSTREAM_COMMIT = "0a89dec45a0192b824e3cf4daf96c239440c5ed8"
EXPECTED = {
    "musetalk/utils/face_parsing/resnet.py": "a3419dabeff41c535e24f4d056b054c1bfc70d56f9ee430808b440005cc3189f",
    "musetalk/utils/face_parsing/model.py": "05d69d1bd77fbca7b537602fe3f7851e8b2e1a3ea0279f383b4223598157e2d2",
    "musetalk/utils/face_parsing/__init__.py": "c2824281e80458b81b7ecdde6cfd2b5f0224b022f41aaf1c61144a52163b2494",
    "musetalk/utils/preprocessing.py": "ca22548666af9bb0b059306e3955bffb97a4a97592b4a050fdce42c5361359f8",
}

FACE_PARSING_INIT_PATH = "musetalk/utils/face_parsing/__init__.py"
PREPROCESSING_PATH = "musetalk/utils/preprocessing.py"

REPLACEMENTS = {
    "musetalk/utils/face_parsing/resnet.py": [
        (
            "class Resnet18(nn.Module):\n"
            "    def __init__(self, model_path):\n"
            "        super(Resnet18, self).__init__()\n"
            "        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,\n"
            "                               bias=False)\n"
            "        self.bn1 = nn.BatchNorm2d(64)\n"
            "        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)\n"
            "        self.layer1 = create_layer_basic(64, 64, bnum=2, stride=1)\n"
            "        self.layer2 = create_layer_basic(64, 128, bnum=2, stride=2)\n"
            "        self.layer3 = create_layer_basic(128, 256, bnum=2, stride=2)\n"
            "        self.layer4 = create_layer_basic(256, 512, bnum=2, stride=2)\n"
            "        self.init_weight(model_path)\n",
            "class Resnet18(nn.Module):\n"
            "    def __init__(self, model_path=None, *, pretrained=True):\n"
            "        super(Resnet18, self).__init__()\n"
            "        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,\n"
            "                               bias=False)\n"
            "        self.bn1 = nn.BatchNorm2d(64)\n"
            "        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)\n"
            "        self.layer1 = create_layer_basic(64, 64, bnum=2, stride=1)\n"
            "        self.layer2 = create_layer_basic(64, 128, bnum=2, stride=2)\n"
            "        self.layer3 = create_layer_basic(128, 256, bnum=2, stride=2)\n"
            "        self.layer4 = create_layer_basic(256, 512, bnum=2, stride=2)\n"
            "        if pretrained:\n"
            "            if model_path is None:\n"
            "                raise ValueError('model_path is required when pretrained=True')\n"
            "            self.init_weight(model_path)\n",
        )
    ],
    "musetalk/utils/face_parsing/model.py": [
        (
            "class ContextPath(nn.Module):\n"
            "    def __init__(self, resnet_path, *args, **kwargs):\n"
            "        super(ContextPath, self).__init__()\n"
            "        self.resnet = Resnet18(resnet_path)\n",
            "class ContextPath(nn.Module):\n"
            "    def __init__(self, resnet_path, *args, pretrained=True, **kwargs):\n"
            "        super(ContextPath, self).__init__()\n"
            "        self.resnet = Resnet18(resnet_path, pretrained=pretrained)\n",
        ),
        (
            "class BiSeNet(nn.Module):\n"
            "    def __init__(self, resnet_path='models/resnet18-5c106cde.pth', n_classes=19, *args, **kwargs):\n"
            "        super(BiSeNet, self).__init__()\n"
            "        self.cp = ContextPath(resnet_path)\n",
            "class BiSeNet(nn.Module):\n"
            "    def __init__(self, resnet_path='models/resnet18-5c106cde.pth', n_classes=19, *args, pretrained=True, **kwargs):\n"
            "        super(BiSeNet, self).__init__()\n"
            "        self.cp = ContextPath(resnet_path, pretrained=pretrained)\n",
        ),
    ],
    FACE_PARSING_INIT_PATH: [
        (
            "        net = BiSeNet(resnet_path)\n"
            "        if torch.cuda.is_available():\n"
            "            net.cuda()\n"
            "            net.load_state_dict(torch.load(model_pth)) \n"
            "        else:\n"
            "            net.load_state_dict(torch.load(model_pth, map_location=torch.device('cpu')))\n",
            "        # The full pinned BiSeNet checkpoint contains the ResNet backbone too.\n"
            "        # Skip only the legacy pretrained bootstrap; strict full-state loading\n"
            "        # below must cover every parameter and buffer.\n"
            "        net = BiSeNet(resnet_path, pretrained=False)\n"
            "        state_dict = torch.load(\n"
            "            model_pth, map_location=torch.device('cpu'), weights_only=True\n"
            "        )\n"
            "        net.load_state_dict(state_dict, strict=True)\n"
            "        if torch.cuda.is_available():\n"
            "            net.cuda()\n",
        )
    ],
    PREPROCESSING_PATH: [
        (
            "model = init_model(config_file, checkpoint_file, device=device)\n",
            "# Nexora compatibility: allow only NumPy containers in the official DWPose checkpoint under Torch 2.7.\n"
            "from mmengine.logging.history_buffer import HistoryBuffer\n"
            "with torch.serialization.safe_globals([HistoryBuffer, np.core.multiarray.scalar, np.core.multiarray._reconstruct, np.ndarray, np.dtype] + [type(np.dtype(t)) for t in ('float32', 'float64', 'int32', 'int64', 'uint8', 'bool')]):\n"
            "    model = init_model(config_file, checkpoint_file, device=device)\n",
        )
    ],
}



class BootstrapError(ValueError):
    pass


def _read_regular(root: Path, relative: str) -> bytes:
    path = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise BootstrapError(f"symlink in source path refused: {relative}")
    try:
        info = path.lstat()
    except OSError as exc:
        raise BootstrapError(f"cannot stat pinned source {relative}: {type(exc).__name__}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise BootstrapError(f"pinned source is not a regular file: {relative}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise BootstrapError(f"cannot read pinned source {relative}: {type(exc).__name__}") from exc


def _apply_one(text: str, old: str, new: str, relative: str) -> str:
    count = text.count(old)
    if count != 1:
        raise BootstrapError(f"non-unique patch anchor in {relative}: {count}")
    return text.replace(old, new, 1)


def build_outputs(source_root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    root = Path(source_root).absolute()
    if not root.is_dir() or root.is_symlink() or root.resolve(strict=True) != root:
        raise BootstrapError("source root must be an existing real directory without symlink traversal")

    # Read and validate every original before applying any patch.
    originals: dict[str, bytes] = {}
    source_hashes: dict[str, str] = {}
    for relative, expected_sha in EXPECTED.items():
        data = _read_regular(root, relative)
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != expected_sha:
            raise BootstrapError(f"unexpected pinned source hash for {relative}: {actual_sha}")
        originals[relative] = data
        source_hashes[relative] = actual_sha

    outputs: dict[str, bytes] = {}
    for relative, data in originals.items():
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BootstrapError(f"pinned source is not UTF-8: {relative}") from exc
        for old, new in REPLACEMENTS[relative]:
            text = _apply_one(text, old, new, relative)
        try:
            ast.parse(text, filename=relative)
        except SyntaxError as exc:
            raise BootstrapError(f"patched Python is invalid: {relative}") from exc
        outputs[relative] = text.encode("utf-8")

    init_text = outputs[FACE_PARSING_INIT_PATH].decode("utf-8")
    if "weights_only=True" not in init_text or "strict=True" not in init_text or "pretrained=False" not in init_text:
        raise BootstrapError("safe strict FaceParser bootstrap postconditions failed")
    pose_text = outputs[PREPROCESSING_PATH].decode("utf-8")
    if "torch.serialization.safe_globals(" not in pose_text or "weights_only=False" in pose_text:
        raise BootstrapError("scoped DWPose safe-globals postconditions failed")

    output_hashes = {relative: hashlib.sha256(data).hexdigest() for relative, data in outputs.items()}
    manifest = {
        "schema_version": 1,
        "status": "validated_overlay_ready",
        "upstream": "TMElyralab/MuseTalk",
        "upstream_commit": UPSTREAM_COMMIT,
        "source_sha256": source_hashes,
        "overlay_sha256": output_hashes,
        "files": sorted(outputs),
        "checkpoint_loading": "FaceParser uses CPU map_location, weights_only=True and strict=True; DWPose safe_globals is scoped to init_model; no model execution",
        "source_tree_modified": False,
    }
    return outputs, manifest


def _write_exclusive(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def publish_overlay(source_root: Path, destination: Path) -> dict[str, Any]:
    outputs, manifest = build_outputs(source_root)
    source = Path(source_root).resolve(strict=True)
    target = Path(destination).absolute()
    target_resolved = target.resolve(strict=False)
    if target_resolved == source or source in target_resolved.parents:
        raise BootstrapError("destination must be outside the pinned source tree")
    if not target.name or target.exists() or target.is_symlink() or os.path.lexists(target):
        raise BootstrapError("destination already exists; refusing overwrite")
    parent = target.parent
    if not parent.is_dir() or any(p.is_symlink() for p in (parent, *parent.parents)):
        raise BootstrapError("destination parent must exist and have no symlink components")

    # mkdir is the exclusive reservation. No existing output tree is ever reused.
    try:
        target.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise BootstrapError("destination appeared concurrently; refusing overwrite") from exc

    try:
        for relative, data in outputs.items():
            output_path = target / relative
            output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            _write_exclusive(output_path, data)
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
        _write_exclusive(target / "bootstrap-manifest.json", manifest_bytes)
        directory_fd = os.open(target, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception as exc:
        # Keep any partial overlay visible; never delete or silently retry it.
        raise BootstrapError(f"overlay publication incomplete and retained at {target}: {type(exc).__name__}") from exc
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = publish_overlay(args.source_root, args.destination)
    except (BootstrapError, OSError) as exc:
        print(f"bootstrap refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"destination": str(args.destination.absolute()), "manifest": manifest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
