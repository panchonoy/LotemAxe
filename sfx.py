import pygame
try:
    import numpy as np
    _numpy_ok = True
except ImportError:
    _numpy_ok = False

_sounds = {}
_enabled = False
_music_sound = None   # fallback: music loaded as Sound when mixer.music fails


def init():
    global _enabled
    if not _numpy_ok:
        return
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        _enabled = True
        _build_all()
    except Exception:
        _enabled = False


def _make(samples):
    mono = np.clip(samples, -32767, 32767).astype(np.int16)
    stereo = np.column_stack([mono, mono])
    return pygame.sndarray.make_sound(stereo)


def _sine(freq, dur, vol=0.5, sr=44100):
    t = np.linspace(0, dur, int(sr * dur), False)
    return (np.sin(2 * np.pi * freq * t) * 32767 * vol).astype(np.float32)


def _build_all():
    sr = 44100

    # Sword swing — short whoosh (white noise + pitch drop)
    dur = 0.12
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    env = np.exp(-t * 10).astype(np.float32)
    _sounds['swing'] = _make((noise * env * 32767 * 0.4).astype(np.float32))

    # Hit — short thud (low sine burst)
    dur = 0.10
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    freq = 120 - t * 80
    wave = np.sin(2 * np.pi * np.cumsum(freq) / sr).astype(np.float32)
    env  = np.exp(-t * 12).astype(np.float32)
    _sounds['hit'] = _make((wave * env * 32767 * 0.7).astype(np.float32))

    # Magic — ascending arpeggio
    notes = [330, 440, 550, 660]
    chunks = []
    for freq in notes:
        dur = 0.07
        t2 = np.linspace(0, 1, int(sr * dur))
        chunk = _sine(freq, dur, 0.35) * np.exp(-t2 * 6).astype(np.float32)
        chunks.append(chunk)
    arr = np.concatenate(chunks)
    _sounds['magic'] = _make(arr)

    # Death — descending tone
    dur = 0.25
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    freq = 300 - t * 200
    wave = np.sin(2 * np.pi * np.cumsum(freq) / sr).astype(np.float32)
    env  = np.exp(-t * 5).astype(np.float32)
    _sounds['death'] = _make((wave * env * 32767 * 0.5).astype(np.float32))

    # Boss roar — low rumble
    dur = 0.55
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    low   = _sine(60, dur, 0.5)[:n]
    env   = (np.exp(-t * 3) * 0.7 + 0.3 * np.exp(-t * 8)).astype(np.float32)
    _sounds['boss_roar'] = _make(((noise * 0.3 + low) * env * 32767 * 0.6).astype(np.float32))

    # Respawn chime — rising soft ding
    notes2 = [523, 659, 784]
    chunks2 = []
    for freq in notes2:
        dur2 = 0.09
        t3 = np.linspace(0, 1, int(sr * dur2))
        c = _sine(freq, dur2, 0.25) * np.exp(-t3 * 8).astype(np.float32)
        chunks2.append(c)
    _sounds['respawn'] = _make(np.concatenate(chunks2))


def play(name, volume=1.0):
    if not _enabled:
        return
    s = _sounds.get(name)
    if s:
        s.set_volume(min(1.0, volume))
        s.play()


def play_music(path, volume=0.65, loops=-1):
    """Start looping background music. Falls back to Sound if mixer.music fails."""
    global _music_sound
    if not _enabled:
        return
    # Stop any previous music/sound track
    stop_music()
    # Primary: pygame.mixer.music (works on desktop; may fail in WASM with MP3)
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
        return
    except Exception:
        pass
    # Fallback: load as Sound object — works in pygbag/WASM
    try:
        _music_sound = pygame.mixer.Sound(path)
        _music_sound.set_volume(volume)
        _music_sound.play(loops=loops)
    except Exception:
        _music_sound = None


def stop_music():
    """Stop any currently-playing background music."""
    global _music_sound
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    if _music_sound is not None:
        try:
            _music_sound.stop()
        except Exception:
            pass
        _music_sound = None
