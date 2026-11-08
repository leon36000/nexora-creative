"""Adaptation reproductible de la cadence MuseTalk, sans charger le modèle."""
import ast
import hashlib

SOURCE_SHA256 = 'b7b62f3daa99678576138bf581a6394a10d346571a2530a760d1299ffd622b81'
PATCHED_SHA256 = '21d6e791d5fa66283f839e478a813275c304c23ff6c81144a093486f5ca14247'


def adapter_audio_processor(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('source AudioProcessor différente de la version épinglée')
    text = source.decode('utf-8')
    for old, new in (
        ('num_frames = math.floor((librosa_length / sr) * fps)',
         'num_frames = (librosa_length * fps) // sr'),
        ('actual_length = math.floor((librosa_length / sr) * audio_fps)',
         'actual_length = (librosa_length * audio_fps) // sr'),
    ):
        if text.count(old) != 1:
            raise ValueError('ancre AudioProcessor non unique')
        text = text.replace(old, new, 1)
    ast.parse(text)
    result = text.encode('utf-8')
    if hashlib.sha256(result).hexdigest() != PATCHED_SHA256:
        raise ValueError('adaptation AudioProcessor inattendue')
    return result
