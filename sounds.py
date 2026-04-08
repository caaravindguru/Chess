import struct
import math
import os

# Try to use PyQt5 for audio, fallback to silent
try:
    from PyQt5.QtMultimedia import QSound
    HAS_QT_AUDIO = True
except ImportError:
    HAS_QT_AUDIO = False

def generate_wav(filename, freq, duration_ms=100, volume=0.5):
    """Generates a simple beep WAV file."""
    sample_rate = 44100
    num_samples = int(sample_rate * (duration_ms / 1000.0))

    # WAV Header
    data = bytearray()
    data.extend(b'RIFF')
    data.extend(struct.pack('<I', 36 + num_samples * 2))
    data.extend(b'WAVEfmt ')
    data.extend(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    data.extend(b'data')
    data.extend(struct.pack('<I', num_samples * 2))

    for i in range(num_samples):
        sample = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        data.extend(struct.pack('<h', sample))

    with open(filename, 'wb') as f:
        f.write(data)

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._init_sounds()

    def _init_sounds(self):
        sound_dir = "sounds"
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir)

        configs = {
            "move": (440, 50),
            "capture": (880, 50),
            "check": (1320, 100),
            "castle": (330, 80),
            "promote": (660, 150),
            "game_end": (220, 300),
            "illegal": (110, 100),
            "start": (550, 150)
        }

        for name, (freq, dur) in configs.items():
            path = os.path.join(sound_dir, f"{name}.wav")
            if not os.path.exists(path):
                generate_wav(path, freq, dur)
            self.sounds[name] = path

    def play(self, name):
        if not self.enabled or name not in self.sounds:
            return

        if HAS_QT_AUDIO:
            try:
                QSound.play(self.sounds[name])
            except Exception:
                pass
        # If no Qt audio, we fail silently as requested.
