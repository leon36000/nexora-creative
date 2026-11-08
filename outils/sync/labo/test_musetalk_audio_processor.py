"""Tests CPU causaux du calcul de fenêtres AudioProcessor MuseTalk."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import types
import unittest

from outils.sync.labo.musetalk_patch import (
    PATCHED_SHA256,
    adapter_audio_processor,
)

FIXTURE = Path(__file__).with_name('musetalk_audio_fixture') / 'audio_processor.py.txt'
ENCODER_LENGTH = 2000
VOICE_SAMPLES = (
    ('FR1', 144640), ('FR2', 144640), ('FR3', 156160), ('FR4', 153600),
    ('EN1', 153600), ('EN2', 148480), ('EN3', 170240), ('EN4', 162560),
)
BOUNDARY_SAMPLES = (144639, 144641, 148479, 148481)


class FakeTensor:
    """Double de tenseur limité aux formes, découpes et conversions .to()."""

    trim_lengths = []

    def __init__(self, shape):
        self.shape = tuple(int(d) for d in shape)

    def to(self, *args, **kwargs):
        return self

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            key = (key,)
        if (len(key) >= 3 and key[0] == slice(None)
                and isinstance(key[1], slice) and key[1].start is None
                and any(k is Ellipsis for k in key)):
            start, stop, step = key[1].indices(self.shape[1])
            FakeTensor.trim_lengths.append(len(range(start, stop, step)))
        new_shape = list(self.shape)
        dim = 0
        for selector in key:
            if selector is Ellipsis:
                continue
            if dim >= len(new_shape):
                break
            if isinstance(selector, slice):
                start, stop, step = selector.indices(new_shape[dim])
                new_shape[dim] = len(range(start, stop, step))
                dim += 1
            elif isinstance(selector, int):
                new_shape.pop(dim)
            else:
                dim += 1
        return FakeTensor(new_shape)


class FakeWhisper:
    N_LAYERS = 5
    FEAT_DIM = 384

    def encoder(self, input_feature, output_hidden_states=False):
        seq = input_feature.shape[1]
        return types.SimpleNamespace(hidden_states=[
            FakeTensor((1, seq, self.FEAT_DIM)) for _ in range(self.N_LAYERS)
        ])


def _fake_stack(tensors, dim=0):
    tensors = list(tensors)
    shape = list(tensors[0].shape)
    shape.insert(dim, len(tensors))
    return FakeTensor(shape)


def _fake_cat(tensors, dim=0):
    tensors = list(tensors)
    shape = list(tensors[0].shape)
    shape[dim] = sum(t.shape[dim] for t in tensors)
    return FakeTensor(shape)


def _fake_rearrange(tensor, pattern):
    if pattern != 'b c h w -> b (c h) w' or len(tensor.shape) != 4:
        raise AssertionError(f'pattern inattendu: {pattern!r}, {tensor.shape!r}')
    b, c, h, w = tensor.shape
    return FakeTensor((b, c * h, w))


def _load_module(name: str, source: bytes, source_name: str):
    module = types.ModuleType(name)
    module.__file__ = source_name
    sys.modules[name] = module
    exec(compile(source, source_name, 'exec'), module.__dict__)
    return module


def _install_import_stubs():
    torch_stub = types.ModuleType('torch')
    torch_stub.stack = _fake_stack
    torch_stub.cat = _fake_cat
    torch_stub.zeros_like = lambda tensor: FakeTensor(tensor.shape)
    torch_stub.__causal_shape_stub__ = True
    einops_stub = types.ModuleType('einops')
    einops_stub.rearrange = _fake_rearrange
    transformers_stub = types.ModuleType('transformers')

    class AutoFeatureExtractor:
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            raise AssertionError('un modèle ne doit jamais être chargé')

    transformers_stub.AutoFeatureExtractor = AutoFeatureExtractor
    stubs = {
        'torch': torch_stub,
        'librosa': types.ModuleType('librosa'),
        'numpy': types.ModuleType('numpy'),
        'einops': einops_stub,
        'transformers': transformers_stub,
    }
    prior = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    return prior, stubs


def _restore_imports(prior):
    for name, module in prior.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


class AudioProcessorFrameCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_bytes = FIXTURE.read_bytes()
        # La provenance primaire et l'ancre de version sont gardées dans
        # musetalk_audio_fixture/source_manifest.json; le patch refuse toute
        # entrée dont le SHA ne correspond pas à cette source épinglée.
        cls.patched_bytes = adapter_audio_processor(cls.original_bytes)
        cls.prior_modules, cls.stubs = _install_import_stubs()
        try:
            cls.original = _load_module(
                'musetalk_audio_processor_original_test', cls.original_bytes, str(FIXTURE))
            cls.patched = _load_module(
                'musetalk_audio_processor_patched_test', cls.patched_bytes,
                '<AudioProcessor généré par musetalk_patch>')
        except Exception:
            _restore_imports(cls.prior_modules)
            raise
        _restore_imports(cls.prior_modules)

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop('musetalk_audio_processor_original_test', None)
        sys.modules.pop('musetalk_audio_processor_patched_test', None)

    def run_method(self, module, samples, fps):
        FakeTensor.trim_lengths.clear()
        processor = module.AudioProcessor.__new__(module.AudioProcessor)
        encoder_input = [FakeTensor((1, ENCODER_LENGTH, 384))]
        output = processor.get_whisper_chunk(
            encoder_input, 'cpu', None, FakeWhisper(), samples, fps=fps)
        self.assertEqual(len(FakeTensor.trim_lengths), 1,
                         'la tranche réelle whisper_feature[:, :actual_length, ...] doit être mesurée')
        self.assertIs(module.torch, self.stubs['torch'],
                      'AudioProcessor doit utiliser le stub installé, pas importer Torch réel')
        return output.shape[0], FakeTensor.trim_lengths[0], output.shape

    def test_patch_output_is_reproducible_and_matches_pinned_sha(self):
        first = adapter_audio_processor(self.original_bytes)
        second = adapter_audio_processor(self.original_bytes)
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), PATCHED_SHA256)

    def test_patch_refuses_mutated_source_bytes(self):
        for position in (0, len(self.original_bytes) // 2, len(self.original_bytes) - 1):
            with self.subTest(position=position):
                changed = bytearray(self.original_bytes)
                changed[position] ^= 1
                with self.assertRaises(ValueError):
                    adapter_audio_processor(bytes(changed))

    def test_original_reproduces_fr_and_en2_float_floor_loss(self):
        prompts, features, _ = self.run_method(self.original, 144640, 25)
        self.assertEqual((prompts, features), (225, 451))
        prompts, features, _ = self.run_method(self.original, 148480, 25)
        self.assertEqual((prompts, features), (231, 463))

    def test_corrected_real_method_for_all_eight_inputs_at_24_and_25_fps(self):
        for voice, samples in VOICE_SAMPLES:
            for fps in (24, 25):
                with self.subTest(voice=voice, samples=samples, fps=fps):
                    prompts, features, shape = self.run_method(self.patched, samples, fps)
                    self.assertEqual(prompts, samples * fps // 16000)
                    self.assertEqual(features, samples * 50 // 16000)
                    self.assertEqual(shape, (prompts, 50, FakeWhisper.FEAT_DIM))

    def test_boundary_lengths_floor_at_24_and_25_fps_without_clipping(self):
        for samples in BOUNDARY_SAMPLES:
            self.assertNotEqual(samples % 640, 0)
            self.assertNotEqual(samples % 320, 0)
            for fps in (24, 25):
                with self.subTest(samples=samples, fps=fps):
                    corrected = self.run_method(self.patched, samples, fps)
                    self.assertEqual(corrected[0], samples * fps // 16000)
                    self.assertEqual(corrected[1], samples * 50 // 16000)
                    original = self.run_method(self.original, samples, fps)
                    self.assertEqual(original[:2], corrected[:2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
