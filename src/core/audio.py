"""All game sound in ONE place.   from src.core import audio ;  audio.play("tick")

* Every sound is made in code, so no audio files are needed.
* To use a real recording instead, drop assets/sounds/<name>.ogg (or .wav). It wins over
  the code-made version with the same name.
* The Options "sfx" switch (prefs) turns everything off.
* If a sound cannot be made, a warning is printed once (it does not stay silent).
"""
import array
import math
import random

import pygame

from src.core import prefs
from src.utils.data_loader import BASE_DIR

SOUND_DIR = BASE_DIR / "assets" / "sounds"

_cache = {}
_state = None      # None = untried, False = unavailable, (freq, channels) = ready


# ------------------------------------------------------------------
# MIXER + BUILDING BLOCKS
# ------------------------------------------------------------------
def _setup():
    global _state
    if _state is None:
        _state = False
        try:
            init = pygame.mixer.get_init()
            if not init or init[1] != -16 or init[2] not in (1, 2):
                # No mixer yet, or the sound card gave us something odd (for example an
                # 8-channel surround output). Restart it as plain 16-bit stereo.
                if init:
                    pygame.mixer.quit()
                pygame.mixer.init(44100, -16, 2, 512, allowedchanges=0)
            freq, fmt, channels = pygame.mixer.get_init()
            if fmt == -16:
                _state = (freq, channels)           # any channel count works: we copy the sample
                print("[audio] ready:", pygame.mixer.get_init())
            else:
                print("[audio] unsupported mixer format:", pygame.mixer.get_init())
        except pygame.error as err:
            print("[audio] disabled:", err)
    return _state


def _build(duration, fn):
    """Renders fn(t) -> -1..1 into a Sound. Needs t to be called in increasing order."""
    state = _setup()
    if not state:
        return None
    freq, channels = state
    data = array.array("h")
    for i in range(int(freq * duration)):
        v = max(-1.0, min(1.0, fn(i / freq)))
        sample = int(v * 32767)
        for _ in range(channels):
            data.append(sample)
    return pygame.mixer.Sound(buffer=data.tobytes())


def _tone(segments):
    """Little beep melodies. segments = [(start_hz, end_hz, seconds, volume, noise, square)]."""
    total = sum(seg[2] for seg in segments)

    def make():
        rng = random.Random(8)
        phase, last = [0.0], [0.0]

        def fn(t):
            start = 0.0
            for f0, f1, dur, vol, noise, square in segments:
                if t < start + dur:
                    break
                start += dur
            else:
                return 0.0
            u = (t - start) / dur
            phase[0] += 2 * math.pi * (f0 + (f1 - f0) * u) * (t - last[0])
            last[0] = t
            wave = math.sin(phase[0])
            if square:
                wave = 1.0 if wave > 0 else -1.0
            return vol * (wave * (1 - noise) + rng.uniform(-1, 1) * noise) * (1 - u) ** 2
        return _build(total, fn)
    return make


# ------------------------------------------------------------------
# THE SOUNDS
# ------------------------------------------------------------------
def _tock():
    rng = random.Random(1)

    def fn(t):
        env = math.exp(-t * 60)
        return env * (0.5 * math.sin(2 * math.pi * (640 - 900 * t) * t) + 0.15 * rng.uniform(-1, 1))
    return _build(0.08, fn)


def _thud():
    rng = random.Random(2)

    def fn(t):
        env = math.exp(-t * 22)
        return env * (0.85 * math.sin(2 * math.pi * (110 - 300 * t) * t) + 0.12 * rng.uniform(-1, 1))
    return _build(0.16, fn)


def _thunder():
    rng = random.Random(3)
    low = [0.0]

    def fn(t):
        low[0] += (rng.uniform(-1, 1) - low[0]) * 0.04
        return low[0] * min(1.0, t * 8) * math.exp(-t * 2.2) * 4.0
    return _build(1.8, fn)


def _rumble():
    """Earthquake: deep shaking drone with filtered noise."""
    rng = random.Random(4)
    low = [0.0]

    def fn(t):
        low[0] += (rng.uniform(-1, 1) - low[0]) * 0.02
        env = min(1.0, t * 6) * max(0.0, 1 - t / 1.6)
        return env * (low[0] * 5.0 + 0.45 * math.sin(2 * math.pi * (38 + 6 * math.sin(t * 9)) * t))
    return _build(1.6, fn)


def _boom():
    """Volcanic blast: a falling low tone plus a rolling noise tail."""
    rng = random.Random(5)
    low = [0.0]

    def fn(t):
        low[0] += (rng.uniform(-1, 1) - low[0]) * 0.06
        env = math.exp(-t * 3.5)
        return env * (0.8 * math.sin(2 * math.pi * (90 - 60 * min(t, 1.0)) * t) + low[0] * 3.0)
    return _build(1.2, fn)


def _crackle():
    """Wildfire: random sharp pops."""
    rng = random.Random(6)
    pops = sorted((rng.uniform(0, 0.95), rng.uniform(0.4, 1.0)) for _ in range(30))
    start = [0]

    def fn(t):
        while start[0] < len(pops) and t - pops[start[0]][0] >= 0.03:
            start[0] += 1
        v, i = 0.0, start[0]
        while i < len(pops) and pops[i][0] <= t:
            d = t - pops[i][0]
            v += pops[i][1] * math.exp(-d * 220) * rng.uniform(-1, 1)
            i += 1
        return v * 0.7 + 0.04 * rng.uniform(-1, 1)
    return _build(1.0, fn)


def _swish():
    """Flood: a soft wave of filtered noise."""
    rng = random.Random(7)
    low = [0.0]

    def fn(t):
        low[0] += (rng.uniform(-1, 1) - low[0]) * 0.15
        env = math.sin(math.pi * min(t, 0.9) / 0.9) ** 2
        return env * low[0] * 2.2
    return _build(0.9, fn)


def _ding():
    """A small two-tone chime when a go-bag item drops in."""
    def fn(t):
        env = math.exp(-t * 14)
        return env * (0.45 * math.sin(2 * math.pi * 880 * t)
                      + 0.3 * math.sin(2 * math.pi * 1320 * (t - 0.05)) * (t > 0.05))
    return _build(0.3, fn)


def _tink():
    """A bright metallic tap for clicking the title casing."""
    def fn(t):
        env = math.exp(-t * 38)
        return env * (0.45 * math.sin(2 * math.pi * 1900 * t) + 0.3 * math.sin(2 * math.pi * 2850 * t)
                      + 0.2 * math.sin(2 * math.pi * 640 * t) * math.exp(-t * 20))
    return _build(0.14, fn)


def _siren():
    """Hazard warning: a wailing two-tone siren."""
    ph, last = [0.0], [0.0]

    def fn(t):
        f = 520 + 380 * (0.5 - 0.5 * math.cos(2 * math.pi * t * 1.5))
        ph[0] += 2 * math.pi * f * (t - last[0])
        last[0] = t
        env = min(1.0, t * 12) * min(1.0, (1.2 - t) * 8)
        return env * 0.35 * (math.sin(ph[0]) + 0.3 * math.sin(2 * ph[0]))
    return _build(1.2, fn)


def _rain():
    """A seamless rain loop: bright hiss plus tiny random drops."""
    rng = random.Random(9)
    low = [0.0]
    drops = sorted((rng.uniform(0, 2.0), rng.uniform(0.2, 0.7)) for _ in range(160))
    start = [0]

    def fn(t):
        white = rng.uniform(-1, 1)
        low[0] += (white - low[0]) * 0.3
        hiss = (white - low[0]) * 0.35                      # high-pass: the "shhh" of rain
        while start[0] < len(drops) and t - drops[start[0]][0] >= 0.02:
            start[0] += 1
        pop, i = 0.0, start[0]
        while i < len(drops) and drops[i][0] <= t:
            pop += drops[i][1] * math.exp(-(t - drops[i][0]) * 400) * rng.uniform(-1, 1)
            i += 1
        swell = 0.85 + 0.15 * math.sin(t * 2 * math.pi / 2.0)   # one slow breath per loop
        return (hiss + pop * 0.5) * swell
    return _build(2.0, fn)


def _wind():
    """A seamless wind loop: low whooshing noise that swells and fades."""
    rng = random.Random(10)
    low, low2 = [0.0], [0.0]

    def fn(t):
        low[0] += (rng.uniform(-1, 1) - low[0]) * 0.03
        low2[0] += (low[0] - low2[0]) * 0.2
        swell = 0.55 + 0.45 * math.sin(t * 2 * math.pi / 3.0)    # whole number of swells per loop
        return low2[0] * 6.0 * swell
    return _build(3.0, fn)


_MAKERS = {
    # menu + hazards
    "tock": _tock, "thud": _thud, "tink": _tink, "ding": _ding, "siren": _siren,
    "thunder": _thunder, "rumble": _rumble, "boom": _boom, "crackle": _crackle, "swish": _swish,
    # interface (character select and other screens)
    "tick":    _tone([(1400, 1000, 0.04, 0.35, 0.0, True)]),
    "hop":     _tone([(500, 900, 0.07, 0.30, 0.0, True)]),
    "back":    _tone([(800, 500, 0.06, 0.30, 0.0, True)]),
    "confirm": _tone([(660, 660, 0.07, 0.35, 0.0, True), (990, 990, 0.14, 0.35, 0.0, True)]),
    "whoosh":  _tone([(300, 1400, 0.16, 0.18, 0.85, False)]),
    # loops (use audio.loop / audio.stop, not audio.play)
    "rain": _rain, "wind": _wind,
}


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------
def _get(name):
    if name not in _cache:
        sound = None
        for ext in (".ogg", ".wav"):                        # a real recording wins
            path = SOUND_DIR / f"{name}{ext}"
            if path.exists():
                try:
                    sound = pygame.mixer.Sound(str(path)) if _setup() else None
                except pygame.error as err:
                    print(f"[audio] could not load {path.name}: {err}")
                break
        if sound is None:
            try:
                sound = _MAKERS[name]()
            except KeyError:
                print(f"[audio] unknown sound '{name}'")
            except Exception as err:
                print(f"[audio] could not make '{name}': {err}")
        _cache[name] = sound
    return _cache[name]


def warm():
    """Build all sounds now so the first play has no hitch."""
    for name in _MAKERS:
        _get(name)


def play(name, volume=0.5):
    try:
        if not prefs.get("sfx"):                            # Options screen switch
            return
    except Exception:
        pass
    sound = _get(name)
    if sound:
        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()


# ------------------------------------------------------------------
# LOOPING SOUNDS (rain, wind, ambience)
# ------------------------------------------------------------------
_loops = {}      # name -> Channel


def loop(name, volume=0.4, fade_ms=600):
    """Start a looping sound (does nothing if it is already running)."""
    try:
        if not prefs.get("sfx"):
            return
    except Exception:
        pass
    channel = _loops.get(name)
    if channel is not None and channel.get_busy():
        channel.set_volume(max(0.0, min(1.0, volume)))
        return
    sound = _get(name)
    if not sound:
        return
    channel = pygame.mixer.find_channel(True)         # True = take a channel even if all are busy
    if channel is None:
        return
    channel.set_volume(max(0.0, min(1.0, volume)))
    channel.play(sound, loops=-1, fade_ms=fade_ms)
    _loops[name] = channel


def set_loop_volume(name, volume):
    """Change a running loop's volume (for example, heavier rain as danger rises)."""
    channel = _loops.get(name)
    if channel is not None:
        channel.set_volume(max(0.0, min(1.0, volume)))


def stop(name, fade_ms=500):
    channel = _loops.pop(name, None)
    if channel is not None:
        channel.fadeout(fade_ms)


def stop_all(fade_ms=300):
    for name in list(_loops):
        stop(name, fade_ms)