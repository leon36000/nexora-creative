#!/usr/bin/env python3
"""Prepare and run one isolated, non-destructive MuseTalk 1.5 lab take.

Nothing runs by default. ``execute`` requires two explicit confirmation flags,
an exclusive per-run lock, an exclusive global GPU lock, and a fresh local GPU
preflight. Every attempt keeps its inputs, extracted frames, generated PNGs,
intermediate MP4s, coordinate pickle, logs, and partial outputs.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import difflib
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import uuid
import wave
from pathlib import Path
from typing import Any


# Les chemins, empreintes des binaires, échantillons et identités GPU proviennent
# exclusivement d'un JSON explicite ; aucun fichier n'est lu à l'import.
CONFIG_SHA = ''
CONFIG_BYTES = b''
ROOT = SOURCE = WEIGHTS = RUNS = TORCH_HOME = HF_HOME = TMPDIR = VENV_PYTHON = FFMPEG = FFPROBE = FFMPEG_DIR = None
EXPECTED_GPU_NAME = ''
MIN_FREE_GPU_MIB = 12288
AUTHORIZED_EXISTING_GPU_PROCESS = None
EXPECTED_INPUTS = {}
EXPECTED_MEDIA_HASHES = {}
CUDA_ALLOCATOR_FRACTION = 0.60
PADDING_CODEC = 0.08
FPS_CIBLE = 24
TEAM_SOURCE_SCOPE = 'Shared technical bench; source attribution not inferred; no human approval'


def _objet_json_sans_doublon(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Clé JSON dupliquée : {key}")
        result[key] = value
    return result


def configurer(path: Path) -> None:
    """Charge uniquement la configuration JSON du banc, sans accès à .env ou secrets."""
    global CONFIG_SHA, CONFIG_BYTES, ROOT, SOURCE, WEIGHTS, RUNS, TORCH_HOME, HF_HOME, TMPDIR, VENV_PYTHON
    global FFMPEG, FFPROBE, FFMPEG_DIR, EXPECTED_GPU_NAME, MIN_FREE_GPU_MIB
    global AUTHORIZED_EXISTING_GPU_PROCESS, EXPECTED_INPUTS, EXPECTED_MEDIA_HASHES, PADDING_CODEC, FPS_CIBLE
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError('Configuration trop volumineuse')
    cfg = json.loads(raw, object_pairs_hook=_objet_json_sans_doublon)
    keys = {'root', 'source', 'weights', 'python', 'ffmpeg', 'ffprobe', 'ffmpeg_sha256',
            'ffprobe_sha256', 'gpu_name', 'gpu_min_free_mib', 'gpu_process', 'inputs', 'padding_codec_seconds'}
    if not isinstance(cfg, dict) or not keys <= set(cfg) or set(cfg) - keys - {'fps'}:
        raise ValueError('Champs de configuration invalides')
    def chemin(value):
        if not isinstance(value, str) or not Path(value).is_absolute() or '\x00' in value:
            raise ValueError('Chemin absolu requis')
        return Path(value)
    def empreinte(value):
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Empreinte SHA-256 invalide')
        return value
    fps = cfg.get('fps', 24)
    if type(fps) is not int or fps not in (24, 25):
        raise ValueError('Cadence attendue : 24 ou 25 images/s')
    root, source, weights = map(chemin, (cfg['root'], cfg['source'], cfg['weights']))
    python, ffmpeg, ffprobe = map(chemin, (cfg['python'], cfg['ffmpeg'], cfg['ffprobe']))
    hashes = {'ffmpeg': empreinte(cfg['ffmpeg_sha256']), 'ffprobe': empreinte(cfg['ffprobe_sha256'])}
    name, minimum, process = cfg['gpu_name'], cfg['gpu_min_free_mib'], cfg['gpu_process']
    if not isinstance(name, str) or not name or type(minimum) is not int or minimum < 12288:
        raise ValueError('GPU ou minimum mémoire invalide')
    if process is not None:
        if not isinstance(process, dict) or set(process) != {'pid', 'start_ticks', 'uid', 'exe', 'max_used_mib'}:
            raise ValueError('Identité GPU invalide')
        if type(process['pid']) is not int or process['pid'] <= 0 or type(process['max_used_mib']) is not int or not 0 <= process['max_used_mib'] <= 512:
            raise ValueError('Identité GPU invalide')
        if not all(isinstance(process[k], str) and process[k].isdigit() for k in ('start_ticks', 'uid')):
            raise ValueError('Identité GPU invalide')
        chemin(process['exe'])
    inputs = cfg['inputs']
    if not isinstance(inputs, dict) or 'video' not in inputs or not set(inputs) <= {'video', 'fr', 'en'} or not set(inputs) & {'fr', 'en'}:
        raise ValueError('Entrées de banc invalides')
    checked = {}
    for kind, item in inputs.items():
        expected = {'path', 'sha256', 'bytes'} if kind == 'video' else {'path', 'sha256', 'bytes', 'language'}
        if not isinstance(item, dict) or set(item) != expected or type(item.get('bytes')) is not int or item['bytes'] <= 0:
            raise ValueError('Entrée de banc invalide')
        if kind != 'video' and (not isinstance(item['language'], str) or not item['language'] or len(item['language']) > 32):
            raise ValueError('Langue invalide')
        checked[kind] = {**item, 'path': chemin(item['path']), 'sha256': empreinte(item['sha256'])}
    padding = cfg['padding_codec_seconds']
    if type(padding) not in (int, float) or not 0 <= padding <= 1:
        raise ValueError('Padding codec invalide')
    CONFIG_SHA = hashlib.sha256(raw).hexdigest()
    CONFIG_BYTES = raw
    ROOT, SOURCE, WEIGHTS = root, source, weights
    RUNS, TORCH_HOME, HF_HOME, TMPDIR = root / 'runs', root / 'cache/torch', root / 'cache/huggingface', root / 'tmp'
    VENV_PYTHON, FFMPEG, FFPROBE, FFMPEG_DIR = python, ffmpeg, ffprobe, ffmpeg.parent
    EXPECTED_MEDIA_HASHES = hashes
    EXPECTED_GPU_NAME, MIN_FREE_GPU_MIB, AUTHORIZED_EXISTING_GPU_PROCESS = name, minimum, process
    EXPECTED_INPUTS, PADDING_CODEC, FPS_CIBLE = checked, float(padding), fps


EXPECTED_SOURCE = {
    "scripts/inference.py": "aaf9c8289c8f07eaf00b87fb11442ac0e1005ac4e2f469966ae3dab2dc4a03aa",
    "musetalk/utils/preprocessing.py": "14a4202869bc8dfa761a3c4c3fb13afe2be4aeb9b853e2389c4e7860b439799c",
    "musetalk/utils/face_parsing/resnet.py": "7bd02989cd50904713ede4fb9ca468e0d45f0cb0c7ed55e12fc8e2b05e591184",
    "musetalk/utils/face_parsing/model.py": "4fd6c5f15979686367b261749dd13f28fc9e551b4e60f5844656ce2cdeac98db",
    "musetalk/utils/face_parsing/__init__.py": "5b4bc38796072153014181f00214ccceff8fd1a58193684795dad60715fb652b",
}

EXPECTED_MODELS = {
    "models/musetalkV15/unet.pth": "7ebf6c98c181e20838e4c0054e96e944ac60d5d692cc01db42839fe11b787007",
    "models/musetalkV15/musetalk.json": "5b6923aee04d71692e0e9846c471e0a4ea07a4f686d39545e472bd4ba17e1b47",
    "models/sd-vae/diffusion_pytorch_model.bin": "1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc",
    "models/sd-vae/config.json": "92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e",
    "models/whisper/pytorch_model.bin": "9607f98a2b22d9e229ae43c52ecea79dcede9e0c5cfae67e8da6eda86d8aac1d",
    "models/whisper/config.json": "ffdccec4f3211f4c63310f2b7098f309fe70f3952cedc5e4d11e43f5b2379b98",
    "models/whisper/preprocessor_config.json": "9b5cd03a36fbb8a627c64d98a5b5b126ead95a77720723944487311f0110b666",
    "models/dwpose/dw-ll_ucoco_384.pth": "0d9408b13cd863c4e95a149dd31232f88f2a12aa6cf8964ed74d7d97748c7a07",
    "models/face-parse-bisent/79999_iter.pth": "468e13ca13a9b43cc0881a9f99083a430e9c0a38abd935431d1c28ee94b26567",
    "models/face-parse-bisent/resnet18-5c106cde.pth": "5c106cde386e87d4033832f2996f5493238eda96ccf559d1d62760c4de0613f8",
    "models/syncnet/auxiliary/s3fd-619a316812.pth": "619a31681264d3f7f7fc7a16a42cbbe8b23f31a256f75a366e5a1bcd59b33543",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def create_exclusive(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def create_json_exclusive(path: Path, obj: dict[str, Any]) -> None:
    create_exclusive(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode())


def append_event(path: Path, event: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def verifier_entree(source: Path, expected_sha: str, expected_bytes: int) -> None:
    if source.is_symlink() or not source.is_file():
        raise RuntimeError(f"input is not a regular file: {source}")
    if source.stat().st_size != expected_bytes or sha256_file(source) != expected_sha:
        raise RuntimeError(f"input integrity check failed: {source}")


def copy_exclusive(source: Path, target: Path, expected_sha: str, expected_bytes: int) -> dict[str, Any]:
    verifier_entree(source, expected_sha, expected_bytes)
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    h = hashlib.sha256()
    count = 0
    with os.fdopen(fd, "wb") as out, source.open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            out.write(block)
            h.update(block)
            count += len(block)
        out.flush()
        os.fsync(out.fileno())
    if count != expected_bytes or h.hexdigest() != expected_sha:
        raise RuntimeError(f"copied input verification failed: {target}")
    return {"path": str(target), "bytes": count, "sha256": h.hexdigest()}


def make_model_audio(source_mp3: Path, target_wav: Path) -> dict[str, Any]:
    if target_wav.exists() or target_wav.is_symlink():
        raise RuntimeError("model audio output already exists; refusing to overwrite")
    subprocess.run(
        [
            str(FFMPEG), "-nostdin", "-n", "-v", "error", "-i", str(source_mp3),
            "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(target_wav),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if target_wav.is_symlink() or not target_wav.is_file():
        raise RuntimeError("FFmpeg did not create a regular model audio WAV")
    with wave.open(str(target_wav), "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        sample_rate = audio.getframerate()
        sample_count = audio.getnframes()
    if channels != 1 or sample_width != 2 or sample_rate != 16000 or sample_count <= 0:
        raise RuntimeError("model audio WAV must be nonempty mono PCM16 at 16000 Hz")
    return {
        "path": str(target_wav),
        "bytes": target_wav.stat().st_size,
        "sha256": sha256_file(target_wav),
        "codec": "pcm_s16le",
        "channels": channels,
        "sample_width_bytes": sample_width,
        "sample_rate": sample_rate,
        "sample_count": sample_count,
        "duration_s": sample_count / sample_rate,
        "decoded_from_sha256": sha256_file(source_mp3),
    }


def expected_final_output_path(run_dir: Path, staged_video: Path, staged_audio: Path) -> Path:
    output_name = f"{staged_video.stem}_{staged_audio.stem}.mp4"
    return run_dir / "results" / "v15" / output_name


def verify_static_assets() -> dict[str, Any]:
    if SOURCE.resolve(strict=True) != SOURCE:
        raise RuntimeError("source path unexpectedly resolves through a symlink")
    if not (SOURCE / "models").is_symlink() or (SOURCE / "models").resolve(strict=True) != WEIGHTS.resolve(strict=True):
        raise RuntimeError("source models mapping differs from the private weights directory")
    result: dict[str, Any] = {"source": {}, "models": {}}
    for relative, expected in EXPECTED_SOURCE.items():
        path = SOURCE / relative
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"source hash mismatch: {relative}")
        result["source"][relative] = {"sha256": actual, "bytes": path.stat().st_size}
    for relative, expected in EXPECTED_MODELS.items():
        path = SOURCE / relative
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"model/config hash mismatch: {relative}")
        result["models"][relative] = {"sha256": actual, "bytes": path.stat().st_size}
    sfd_link = TORCH_HOME / "hub/checkpoints/s3fd-619a316812.pth"
    if sfd_link.resolve(strict=True) != (SOURCE / "models/syncnet/auxiliary/s3fd-619a316812.pth").resolve(strict=True):
        raise RuntimeError("SFD cache path is not the verified local model")
    for tool, expected in (
        (FFMPEG, EXPECTED_MEDIA_HASHES["ffmpeg"]),
        (FFPROBE, EXPECTED_MEDIA_HASHES["ffprobe"]),
    ):
        actual = sha256_file(tool)
        if actual != expected or not os.access(tool, os.X_OK):
            raise RuntimeError(f"media-tool hash/execute check failed: {tool}")
    result["ffmpeg"] = {"path": str(FFMPEG), "sha256": sha256_file(FFMPEG)}
    result["ffprobe"] = {"path": str(FFPROBE), "sha256": sha256_file(FFPROBE)}
    return result


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"inference source anchor {label} occurs {count} times; refusing patch")
    return text.replace(old, new, 1)


def make_preserving_runner(source: Path) -> bytes:
    actual = sha256_file(source)
    expected = EXPECTED_SOURCE["scripts/inference.py"]
    if actual != expected:
        raise RuntimeError(f"upstream inference source changed: {actual}")
    text = source.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import torch\n",
        "import torch\n\n"
        "# Limit only this MuseTalk process's PyTorch CUDA allocator.\n"
        "if torch.cuda.is_available():\n"
        "    torch.cuda.set_per_process_memory_fraction(0.60, device=0)\n",
        "per-process allocator cap",
    )
    text = replace_once(
        text,
        "            whisper_input_features, librosa_length = audio_processor.get_audio_feature(audio_path)\n",
        "            feature_audio_path = os.environ.get(\"NEXORA_FEATURE_AUDIO_PATH\", audio_path)\n"
        "            whisper_input_features, librosa_length = audio_processor.get_audio_feature(feature_audio_path)\n",
        "Whisper feature audio source",
    )
    text = replace_once(
        text,
        '                cmd = f"ffmpeg -v fatal -i {video_path} -start_number 0 {save_dir_full}/%08d.png"\n'
        "                os.system(cmd)",
        '                cmd = [\n'
        '                    os.environ["NEXORA_FFMPEG_BIN"], "-nostdin", "-n", "-v", "fatal",\n'
        '                    "-i", video_path, "-start_number", "0",\n'
        '                    os.path.join(save_dir_full, "%08d.png"),\n'
        "                ]\n"
        "                subprocess.run(cmd, check=True)",
        "frame extraction",
    )
    text = replace_once(
        text,
        "                fps = get_video_fps(video_path)\n",
        "                fps = get_video_fps(video_path)\n"
        "                if abs(fps - args.fps) > 0.001:\n"
        "                    raise ValueError('source FPS differs from requested FPS')\n",
        "source video cadence",
    )
    text = replace_once(
        text,
        '            cmd_img2video = f"ffmpeg -y -v warning -r {fps} -f image2 -i {result_img_save_path}/%08d.png -vcodec libx264 -vf format=yuv420p -crf 18 {temp_vid_path}"\n'
        '            print("Video generation command:", cmd_img2video)\n'
        "            os.system(cmd_img2video)",
        '            cmd_img2video = [\n'
        '                os.environ["NEXORA_FFMPEG_BIN"], "-nostdin", "-n", "-v", "warning",\n'
        '                "-r", str(fps), "-f", "image2", "-i",\n'
        '                os.path.join(result_img_save_path, "%08d.png"),\n'
        '                "-vcodec", "libx264", "-vf", "format=yuv420p", "-crf", "18", temp_vid_path,\n'
        "            ]\n"
        '            print("Video generation command:", cmd_img2video)\n'
        "            subprocess.run(cmd_img2video, check=True)",
        "image encoding",
    )
    text = replace_once(
        text,
        '            cmd_combine_audio = f"ffmpeg -y -v warning -i {audio_path} -i {temp_vid_path} {output_vid_name}"\n'
        '            print("Audio combination command:", cmd_combine_audio) \n'
        "            os.system(cmd_combine_audio)",
        '            cmd_combine_audio = [\n'
        '                os.environ["NEXORA_FFMPEG_BIN"], "-nostdin", "-n", "-v", "warning",\n'
        '                "-i", audio_path, "-i", temp_vid_path, output_vid_name,\n'
        "            ]\n"
        '            print("Audio combination command:", cmd_combine_audio)\n'
        "            subprocess.run(cmd_combine_audio, check=True)",
        "audio mux",
    )
    text = replace_once(
        text,
        "            # Clean up temporary files\n"
        "            shutil.rmtree(result_img_save_path)\n"
        "            os.remove(temp_vid_path)\n"
        "            \n"
        "            shutil.rmtree(save_dir_full)\n"
        "            if not args.saved_coord:\n"
        "                os.remove(crop_coord_save_path)",
        "            # Deliberately retain generated PNGs, extracted source frames,\n"
        "            # coordinate pickle, and silent intermediate MP4 for review.",
        "destructive cleanup",
    )
    text = replace_once(
        text,
        '        except Exception as e:\n'
        '            print("Error occurred during processing:", e)',
        '        except Exception as e:\n'
        '            print("Error occurred during processing:", e)\n'
        "            raise",
        "error propagation",
    )
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in {"system", "remove", "rmtree"}:
                raise RuntimeError(f"unsafe file/process operation remains in safe runner: {name}")
            if name == "run" and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                if not any(
                    keyword.arg == "check"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in node.keywords
                ):
                    raise RuntimeError("subprocess.run without check=True remains")
    if '"-y"' in text or "ffmpeg -y" in text:
        raise RuntimeError("overwrite flag remains in safe runner")
    subprocess_runs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    if len(subprocess_runs) != 4:
        raise RuntimeError(f"expected one ffmpeg probe and three checked ffmpeg calls; found {len(subprocess_runs)}")
    return text.encode("utf-8")


def probe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            str(FFPROBE), "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def verifier_cadence_video(video_probe: dict[str, Any]) -> None:
    """Refuse une cadence déclarée différente ; ne certifie pas seule un flux CFR."""
    from fractions import Fraction
    streams = [s for s in video_probe.get('streams', []) if s.get('codec_type') == 'video']
    if len(streams) != 1:
        raise ValueError('Un seul flux vidéo attendu')
    try:
        cadences = (Fraction(streams[0]['r_frame_rate']), Fraction(streams[0]['avg_frame_rate']))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError('Cadence vidéo illisible') from exc
    if any(rate != FPS_CIBLE for rate in cadences):
        raise ValueError('Cadence vidéo incompatible avec la cadence déclarée')


def construire_commande(run_dir: Path) -> list[str]:
    safe_runner = run_dir / "runner/inference_preserve.py"
    return [
        str(VENV_PYTHON), str(safe_runner),
        "--inference_config", str(run_dir / "config/task.yaml"),
        "--result_dir", str(run_dir / "results"),
        "--unet_model_path", str(SOURCE / "models/musetalkV15/unet.pth"),
        "--unet_config", str(SOURCE / "models/musetalkV15/musetalk.json"),
        "--whisper_dir", str(SOURCE / "models/whisper"),
        "--vae_type", "sd-vae", "--version", "v15", "--gpu_id", "0",
        "--fps", str(FPS_CIBLE), "--batch_size", "2", "--extra_margin", "10",
        "--parsing_mode", "jaw", "--left_cheek_width", "90",
        "--right_cheek_width", "90", "--saved_coord", "--use_float16",
    ]


def prepare(language: str) -> Path:
    if language not in {"fr", "en"} or language not in EXPECTED_INPUTS:
        raise ValueError("language must be fr or en")
    assets = verify_static_assets()
    video_info = EXPECTED_INPUTS["video"]
    voice_info = EXPECTED_INPUTS[language]
    for item in (video_info, voice_info):
        verifier_entree(item["path"], item["sha256"], item["bytes"])
    video_probe = probe(video_info["path"])
    verifier_cadence_video(video_probe)
    audio_probe = probe(voice_info["path"])
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{language}-{uuid.uuid4().hex[:12]}"
    RUNS.mkdir(mode=0o700, parents=True, exist_ok=True)
    run_dir = RUNS / run_id
    run_dir.mkdir(mode=0o700, exist_ok=False)
    (run_dir / "inputs").mkdir(mode=0o700, exist_ok=False)
    (run_dir / "runner").mkdir(mode=0o700, exist_ok=False)
    (run_dir / "config").mkdir(mode=0o700, exist_ok=False)
    create_exclusive(run_dir / "config/launcher.json", CONFIG_BYTES)

    staged_video = run_dir / "inputs" / f"video-{language}.mp4"
    voice_suffix = voice_info["path"].suffix.lower()
    if voice_suffix not in {".mp3", ".wav", ".m4a", ".flac", ".ogg"}:
        raise ValueError("unsupported audio input extension")
    staged_voice_source = run_dir / "inputs" / f"voice-{language}-source{voice_suffix}"
    staged_voice_model = run_dir / "inputs" / f"voice-{language}-model.wav"
    copied_video = copy_exclusive(video_info["path"], staged_video, video_info["sha256"], video_info["bytes"])
    copied_voice_source = copy_exclusive(voice_info["path"], staged_voice_source, voice_info["sha256"], voice_info["bytes"])
    model_audio = make_model_audio(staged_voice_source, staged_voice_model)
    safe_runner = run_dir / "runner" / "inference_preserve.py"
    source_inference = SOURCE / "scripts/inference.py"
    safe_runner_bytes = make_preserving_runner(source_inference)
    create_exclusive(safe_runner, safe_runner_bytes)
    safe_diff = "".join(
        difflib.unified_diff(
            source_inference.read_text(encoding="utf-8").splitlines(keepends=True),
            safe_runner_bytes.decode("utf-8").splitlines(keepends=True),
            fromfile="pinned/scripts/inference.py",
            tofile="private-runner/inference_preserve.py",
        )
    )
    diff_path = run_dir / "runner" / "inference_preserve.diff"
    create_exclusive(diff_path, safe_diff.encode("utf-8"))
    config_text = (
        "task_0:\n"
        f'  video_path: {json.dumps(str(staged_video))}\n'
        f'  audio_path: {json.dumps(str(staged_voice_source))}\n'
    )
    config_path = run_dir / "config" / "task.yaml"
    create_exclusive(config_path, config_text.encode("utf-8"))
    expected_final_path = expected_final_output_path(run_dir, staged_video, staged_voice_source)
    command = construire_commande(run_dir)
    manifest = {
        "schema_version": 1,
        "launcher_config_sha256": CONFIG_SHA,
        "run_id": run_id,
        "created_utc": utc_now(),
        "status": "prepared_no_inference",
        "classification": "ESSAI TECHNIQUE NON APPROUVÉ",
        "product_or_quality_approval": "none; human review pending",
        "voice_selection": "not approved; these archived samples are lab inputs only",
        "team_source": TEAM_SOURCE_SCOPE,
        "launcher": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "language": voice_info["language"],
        "language_key": language,
        "model_version": "MuseTalk 1.5",
        "source_video": {
            "original_path": str(video_info["path"]),
            "staged": copied_video,
            "probe": video_probe,
        },
        "voice_sample": {
            **{key: value for key, value in voice_info.items() if key != "path"},
            "original_staged": copied_voice_source,
            "model_input": model_audio,
            "source_probe": audio_probe,
            "model_input_probe": probe(staged_voice_model),
        },
        "source_snapshot": str(SOURCE),
        "source_hashes": assets["source"],
        "model_hashes": assets["models"],
        "ffmpeg": assets["ffmpeg"],
        "ffprobe": assets["ffprobe"],
        "safe_runner_sha256": hashlib.sha256(safe_runner_bytes).hexdigest(),
        "safe_runner_diff_sha256": sha256_file(diff_path),
        "config_sha256": sha256_file(config_path),
        "render_parameters": {
            "fps": FPS_CIBLE,
            "batch_size": 2,
            "precision": "upstream --use_float16 enabled for the technical baseline; no quality claim",
            "pytorch_cuda_allocator_fraction": CUDA_ALLOCATOR_FRACTION,
            "allocator_limit_note": "PyTorch allocator only; not a hard cap on driver/non-PyTorch allocations",
            "bbox_shift": 0,
            "extra_margin": 10,
            "parsing_mode": "jaw",
            "save_coordinates": True,
            "preserve_all_intermediates": True,
            "no_overwrite": True,
            "network": "Hugging Face and Diffusers offline; local-only model files",
        },
        "planned_command": command,
        "planned_environment": {
            "PYTHONPATH": str(SOURCE),
            "NEXORA_FEATURE_AUDIO_PATH": str(staged_voice_model),
            "CUDA_VISIBLE_DEVICES": "0 (only if explicitly executed after review)",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "DIFFUSERS_OFFLINE": "1",
            "OMP_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "1",
        },
        "output_layout": {
            "root": str(run_dir / "results"),
            "expected_final": str(expected_final_path),
            "retained": ["all extracted source PNGs", "all generated PNGs", "silent intermediate MP4", "coordinate pickle", "logs", "partial files on failure"],
        },
        "execution": "not launched; requires separate explicit root review and fresh GPU preflight",
    }
    create_json_exclusive(run_dir / "manifest.json", manifest)
    create_exclusive(run_dir / "events.jsonl", (json.dumps({"event": "prepared", "utc": utc_now(), "run_id": run_id}) + "\n").encode())
    create_json_exclusive(run_dir / "launch-plan.json", {"run_id": run_id, "command": command, "run_directory": str(run_dir), "launcher_sha256": manifest["launcher"]["sha256"], "status": "not_started"})
    return run_dir


def gpu_snapshot() -> dict[str, Any]:
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,uuid,memory.total,memory.free,utilization.gpu,power.draw", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=15,
    ).stdout.strip().splitlines()
    processes_result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=15,
    )
    processes = [line.strip() for line in processes_result.stdout.splitlines() if line.strip() and "No running processes" not in line]
    identities: dict[str, Any] = {}
    for row in processes:
        try:
            pid = int(row.split(",", 1)[0].strip())
            proc = Path(f"/proc/{pid}")
            stat_text = (proc / "stat").read_text(encoding="utf-8")
            stat_fields = stat_text[stat_text.rfind(")") + 2 :].split()
            uid = next(line.split()[1] for line in (proc / "status").read_text(encoding="utf-8").splitlines() if line.startswith("Uid:"))
            identities[str(pid)] = {
                "pid": pid,
                "start_ticks": stat_fields[19],
                "uid": uid,
                "exe": os.readlink(proc / "exe"),
            }
        except Exception as exc:
            identities[row.split(",", 1)[0].strip()] = {"metadata_error": type(exc).__name__}
    return {
        "utc": utc_now(),
        "gpu_rows": gpu,
        "compute_process_rows": processes,
        "compute_process_identities": identities,
        "queue_scope": "standalone MuseTalk process; no external service queue endpoint is configured",
    }


def evaluate_gpu_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    rows = snapshot.get("gpu_rows", [])
    if len(rows) != 1:
        return {"ready": False, "reason": f"expected one local GPU row; got {len(rows)}"}
    fields = [field.strip() for field in rows[0].split(",")]
    if len(fields) < 6 or fields[0] != EXPECTED_GPU_NAME:
        return {"ready": False, "reason": "GPU snapshot is malformed or names an unexpected device"}
    try:
        free_mib = int(float(fields[3]))
        utilization = int(fields[4])
    except ValueError:
        return {"ready": False, "reason": "GPU memory/utilization fields are not numeric"}
    if free_mib < MIN_FREE_GPU_MIB:
        return {"ready": False, "reason": f"free VRAM {free_mib} MiB is below {MIN_FREE_GPU_MIB} MiB"}
    if utilization != 0:
        return {"ready": False, "reason": f"GPU utilization is {utilization}%, expected idle 0%"}
    allowed: list[dict[str, Any]] = []
    process_rows = snapshot.get("compute_process_rows", [])
    identities = snapshot.get("compute_process_identities", {})
    for row in process_rows:
        columns = [column.strip() for column in row.split(",")]
        if len(columns) < 3 or not columns[0].isdigit():
            return {"ready": False, "reason": f"unparseable GPU compute process row: {row}"}
        pid = int(columns[0])
        try:
            used_mib = int(float(columns[2]))
        except ValueError:
            return {"ready": False, "reason": f"unparseable GPU memory for PID {pid}"}
        identity = identities.get(str(pid))
        expected = AUTHORIZED_EXISTING_GPU_PROCESS
        matches = (
            expected is not None
            and pid == expected["pid"]
            and isinstance(identity, dict)
            and identity.get("start_ticks") == expected["start_ticks"]
            and identity.get("uid") == expected["uid"]
            and identity.get("exe") == expected["exe"]
            and used_mib <= expected["max_used_mib"]
        )
        if not matches:
            return {"ready": False, "reason": f"unrecognized or changed GPU process PID {pid}"}
        allowed.append({"pid": pid, "used_mib": used_mib, "identity": identity})
    return {
        "ready": True,
        "reason": "VRAM threshold met, GPU utilization 0%, and only the known stable low-memory process is present",
        "free_mib": free_mib,
        "allowed_existing_processes": allowed,
    }


def self_test_gpu_policy() -> None:
    expected = AUTHORIZED_EXISTING_GPU_PROCESS
    identities = {} if expected is None else {str(expected["pid"]): dict(expected)}
    rows = [] if expected is None else [f"{expected['pid']}, python, {min(expected['max_used_mib'], 1)}"]
    def snapshot(free, util):
        return {"gpu_rows": [f"{EXPECTED_GPU_NAME}, GPU-test, {MIN_FREE_GPU_MIB + 1000}, {free}, {util}, 1"],
                "compute_process_rows": rows, "compute_process_identities": identities}
    if not evaluate_gpu_snapshot(snapshot(MIN_FREE_GPU_MIB, 0))["ready"]:
        raise RuntimeError("GPU policy refused an allowed idle snapshot")
    if evaluate_gpu_snapshot(snapshot(MIN_FREE_GPU_MIB - 1, 0))["ready"]:
        raise RuntimeError("GPU policy allowed insufficient memory")
    if evaluate_gpu_snapshot(snapshot(MIN_FREE_GPU_MIB, 1))["ready"]:
        raise RuntimeError("GPU policy allowed a busy GPU")
    unknown = snapshot(MIN_FREE_GPU_MIB, 0)
    unknown["compute_process_rows"] = ["999999, unknown, 1"]
    unknown["compute_process_identities"] = {}
    if evaluate_gpu_snapshot(unknown)["ready"]:
        raise RuntimeError("GPU policy allowed an unknown process")
    if expected is not None:
        changed = snapshot(MIN_FREE_GPU_MIB, 0)
        changed["compute_process_identities"] = {str(expected["pid"]): {**expected, "start_ticks": "different"}}
        if evaluate_gpu_snapshot(changed)["ready"]:
            raise RuntimeError("GPU policy allowed a restarted process")


def run_preflight(run_dir: Path, persist: bool) -> dict[str, Any]:
    assets = verify_static_assets()
    snapshot = gpu_snapshot()
    video_probe = probe(EXPECTED_INPUTS["video"]["path"])
    verifier_cadence_video(video_probe)
    result = {
        "checked_utc": utc_now(),
        "static_assets_ok": True,
        "fresh_gpu_snapshot": snapshot,
        "gpu_policy": evaluate_gpu_snapshot(snapshot),
        "input_video_probe": video_probe,
        "local_models_offline": True,
    }
    if persist:
        path = run_dir / f"preflight-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.json"
        create_json_exclusive(path, result)
    return result


def verifier_rendu_av(reference: Path, rendu: Path) -> dict[str, Any]:
    import importlib.util
    validator = Path(__file__).resolve().parent.parent / "valider_duree_av.py"
    spec = importlib.util.spec_from_file_location("nexora_valider_duree_av", validator)
    if spec is None or spec.loader is None:
        raise RuntimeError("AV validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.valider(reference, rendu, FFMPEG, FFPROBE, PADDING_CODEC, cadence_cible=str(FPS_CIBLE))


def safe_run(run_id: str, root_reviewed: bool, technical_unapproved: bool) -> int:
    if not root_reviewed or not technical_unapproved:
        raise RuntimeError("execution requires --root-reviewed and --technical-unapproved")
    run_dir = RUNS / run_id
    if run_dir.resolve(strict=True).parent != RUNS.resolve(strict=True):
        raise RuntimeError("run directory is outside the isolated runs root")
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "prepared_no_inference" or manifest.get("classification") != "ESSAI TECHNIQUE NON APPROUVÉ":
        raise RuntimeError("unexpected run manifest state")
    if manifest.get("launcher_config_sha256") != CONFIG_SHA:
        raise RuntimeError("configuration changed since preparation")
    if manifest.get("launcher", {}).get("sha256") != sha256_file(Path(__file__).resolve()):
        raise RuntimeError("launcher hash differs from the version that prepared this run")
    if (run_dir / "inputs").is_symlink():
        raise RuntimeError("prepared inputs directory is a symlink")
    staged_inputs = (
        manifest["source_video"]["staged"],
        manifest["voice_sample"]["original_staged"],
        manifest["voice_sample"]["model_input"],
    )
    for staged in staged_inputs:
        staged_path = Path(staged["path"])
        if staged_path.is_symlink() or not staged_path.is_file():
            raise RuntimeError(f"staged input is not a regular file: {staged_path}")
        if staged_path.resolve(strict=True).parent != (run_dir / "inputs").resolve(strict=True):
            raise RuntimeError(f"staged input escaped run directory: {staged_path}")
        if staged_path.stat().st_size != staged["bytes"] or sha256_file(staged_path) != staged["sha256"]:
            raise RuntimeError(f"staged input hash mismatch: {staged_path}")
    safe_runner_path = run_dir / "runner/inference_preserve.py"
    config_path = run_dir / "config/task.yaml"
    for path in (run_dir / "runner", run_dir / "config", safe_runner_path, config_path, run_dir / "config/launcher.json"):
        if path.is_symlink():
            raise RuntimeError("prepared runner or configuration path is a symlink")
    key = manifest.get("language_key")
    if key not in ("fr", "en") or key not in EXPECTED_INPUTS:
        raise RuntimeError("unknown prepared language")
    for staged, configured in ((staged_inputs[0], EXPECTED_INPUTS["video"]), (staged_inputs[1], EXPECTED_INPUTS[key])):
        if staged["sha256"] != configured["sha256"] or staged["bytes"] != configured["bytes"]:
            raise RuntimeError("prepared input differs from launcher configuration")
    if sha256_file(safe_runner_path) != manifest["safe_runner_sha256"]:
        raise RuntimeError("prepared runner hash mismatch")
    if safe_runner_path.read_bytes() != make_preserving_runner(SOURCE / "scripts/inference.py"):
        raise RuntimeError("prepared runner differs from pinned transformation")
    if sha256_file(config_path) != manifest["config_sha256"]:
        raise RuntimeError("prepared config hash mismatch")
    expected_task = ("task_0:\n" + f'  video_path: {json.dumps(staged_inputs[0]["path"])}\n'
                     + f'  audio_path: {json.dumps(staged_inputs[1]["path"])}\n').encode()
    if config_path.read_bytes() != expected_task:
        raise RuntimeError("prepared task differs from staged inputs")
    if sha256_file(run_dir / "config/launcher.json") != CONFIG_SHA:
        raise RuntimeError("stored launcher configuration mismatch")
    expected_output = expected_final_output_path(run_dir, Path(staged_inputs[0]["path"]), Path(staged_inputs[1]["path"]))
    if manifest.get("planned_command") != construire_commande(run_dir):
        raise RuntimeError("prepared command differs from the verified plan")
    if manifest.get("output_layout", {}).get("expected_final") != str(expected_output):
        raise RuntimeError("prepared output differs from confined path")
    if (run_dir / "results").exists():
        raise RuntimeError("results path already exists; preserve this attempt and prepare a new run")
    if (run_dir / "launch.lock").exists():
        raise RuntimeError("this run already has a launch record; never retry it")
    create_exclusive(run_dir / "launch.lock", (utc_now() + "\n").encode())
    active_fd: int | None = None
    child_started = False
    try:
        append_event(run_dir / "events.jsonl", {"event": "launch_requested", "utc": utc_now(), "run_id": run_id})

        active_path = RUNS / "active-gpu.lock"
        active_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if active_path.is_symlink():
            raise RuntimeError("global GPU lock path is a symlink")
        active_fd = os.open(active_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(active_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another MuseTalk launcher process holds the exclusive GPU lock") from exc
        preflight = run_preflight(run_dir, persist=True)
        if not preflight["gpu_policy"]["ready"]:
            raise RuntimeError(preflight["gpu_policy"]["reason"])
        (run_dir / "results").mkdir(mode=0o700, exist_ok=False)
        env = {
            "PATH": f"{FFMPEG_DIR}:{VENV_PYTHON.parent}:/usr/bin:/bin",
            "PYTHONPATH": str(SOURCE),
            "TMPDIR": str(TMPDIR),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "CUDA_VISIBLE_DEVICES": "0",
            "TORCH_HOME": str(TORCH_HOME),
            "HF_HOME": str(HF_HOME),
            "XDG_CACHE_HOME": str(ROOT / "cache"),
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "DIFFUSERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "OMP_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
            "OPENBLAS_NUM_THREADS": "1",
            "NEXORA_FFMPEG_BIN": str(FFMPEG),
            "NEXORA_FEATURE_AUDIO_PATH": manifest["voice_sample"]["model_input"]["path"],
        }
        command = manifest["planned_command"]
        log_path = run_dir / "run.log"
        fd = os.open(log_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        child_exception = None
        completed = None
        with os.fdopen(fd, "wb") as log:
            append_event(run_dir / "events.jsonl", {"event": "model_process_launch_requested", "utc": utc_now(), "run_id": run_id})
            try:
                child_started = True
                completed = subprocess.run(
                    command,
                    cwd=SOURCE,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1200,
                    check=False,
                )
            except Exception as exc:
                child_exception = f"{type(exc).__name__}: {exc}"
                log.write(("\nLAUNCHER_CHILD_EXCEPTION=" + child_exception + "\n").encode())
            log.flush()
            os.fsync(log.fileno())
        output_path = Path(manifest["output_layout"]["expected_final"])
        decode = None
        probe_result = None
        postflight_exception = None
        av_validation = None
        if output_path.is_file() and output_path.stat().st_size > 0:
            try:
                probe_result = probe(output_path)
                decode_run = subprocess.run(
                    [str(FFMPEG), "-nostdin", "-v", "error", "-xerror", "-i", str(output_path), "-f", "null", "-"],
                    capture_output=True, text=True, timeout=120,
                )
                decode = {"exit_code": decode_run.returncode, "stderr": decode_run.stderr[-1000:]}
                if decode_run.returncode == 0:
                    av_validation = verifier_rendu_av(Path(manifest["voice_sample"]["original_staged"]["path"]), output_path)
            except Exception as exc:
                postflight_exception = f"{type(exc).__name__}: {exc}"
        artifact_rows = []
        for path in sorted(run_dir.rglob("*")):
            if path.is_file() and path.name not in {"result.json"}:
                artifact_rows.append({"relative_path": str(path.relative_to(run_dir)), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
        success = (
            child_exception is None
            and postflight_exception is None
            and completed is not None
            and completed.returncode == 0
            and output_path.is_file()
            and bool(decode and decode["exit_code"] == 0)
            and bool(av_validation and av_validation.get("valide") is True)
        )
        result = {
            "run_id": run_id,
            "finished_utc": utc_now(),
            "status": "completed_av_validated" if success else "failed_or_invalid_output",
            "av_validation": av_validation,
            "child_exit_code": None if completed is None else completed.returncode,
            "child_exception": child_exception,
            "postflight_exception": postflight_exception,
            "final_output": None if not output_path.is_file() else {"path": str(output_path), "bytes": output_path.stat().st_size, "sha256": sha256_file(output_path), "probe": probe_result, "full_decode": decode},
            "retained_artifacts": artifact_rows,
            "human_status": "unapproved technical lab output; no voice or marketing approval",
        }
        create_json_exclusive(run_dir / "result.json", result)
        append_event(run_dir / "events.jsonl", {"event": result["status"], "utc": result["finished_utc"], "run_id": run_id})
        return 0 if success else 1
    except Exception as exc:
        if not (run_dir / "result.json").exists():
            status = "refused_preflight" if not (run_dir / "results").exists() else "launcher_error"
            terminal = {
                "run_id": run_id,
                "finished_utc": utc_now(),
                "status": status,
                "reason_type": type(exc).__name__,
                "reason": str(exc),
                "execution_stage": "model_start_attempted" if child_started else "before_model_start",
                "human_status": "unapproved technical lab attempt; model execution may have started" if child_started else "unapproved technical lab attempt; model execution not started",
            }
            create_json_exclusive(run_dir / "result.json", terminal)
            append_event(run_dir / "events.jsonl", {"event": status, "utc": terminal["finished_utc"], "run_id": run_id})
            return 2
        raise
    finally:
        if active_fd is not None:
            os.close(active_fd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("self-test", help="verify isolated source transformation only; no model execution")
    prep = sub.add_parser("prepare", help="stage one language in a new exclusive run directory")
    prep.add_argument("--language", choices=("fr", "en"), required=True)
    preflight = sub.add_parser("preflight", help="read-only GPU/asset snapshot")
    preflight.add_argument("run_id")
    run = sub.add_parser("execute", help="launch exactly one run after separate root review")
    run.add_argument("run_id")
    run.add_argument("--root-reviewed", action="store_true")
    run.add_argument("--technical-unapproved", action="store_true")
    args = parser.parse_args()
    configurer(args.config)

    if args.command == "self-test":
        verify_static_assets()
        safe = make_preserving_runner(SOURCE / "scripts/inference.py").decode("utf-8")
        self_test_gpu_policy()
        print(f"safe_runner_sha256={hashlib.sha256(safe.encode()).hexdigest()}")
        print("cleanup_calls=0 overwrite_y=0 checked_ffmpeg_calls=3 ast=parse_ok gpu_policy_mocks=5_pass")
        return 0
    if args.command == "prepare":
        print(str(prepare(args.language)))
        return 0
    if args.command == "preflight":
        run_dir = RUNS / args.run_id
        if run_dir.resolve(strict=True).parent != RUNS.resolve(strict=True):
            raise RuntimeError("run directory is outside the isolated runs root")
        snapshot = run_preflight(run_dir, persist=True)
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return 0
    if args.command == "execute":
        return safe_run(args.run_id, args.root_reviewed, args.technical_unapproved)
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
