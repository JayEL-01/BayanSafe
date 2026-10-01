"""Menu sound effects generated in code, so no audio files are needed.

If you later add real files, drop them in assets/audio/ and replace _make() for that name.
Everything fails silently if the mixer is missing or in an unexpected format.
"""
import array
import math
import random

import pygame

from src.core import prefs

_cache = {}
_state = None      # None = untried, False = unavailable, (freq, channels) = ready


def _setup():
    global _state
    if _state is None:
        _state = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            freq, fmt, channels = pygame.mixer.get_init()
            if fmt == -16 and channels in (1, 2):
                _state = (freq, channels)
        except pygame.error:
            pass
    return _state


def _build(duration, fn):
    state = _setup()
    if not state:
        return None
    freq, channels = state
    count = int(freq * duration)
    data = array.array("h")
    for i in range(count):
        v = max(-1.0, min(1.0, fn(i / freq)))
        sample = int(v * 32767)
        for _ in range(channels):
            data.append(sample)
    return pygame.mixer.Sound(buffer=data.tobytes())


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


_MAKERS = {"tock": _tock, "thud": _thud, "thunder": _thunder,
           "rumble": _rumble, "boom": _boom, "crackle": _crackle, "swish": _swish}


def _get(name):
    if name not in _cache:
        try:
            _cache[name] = _MAKERS[name]()
        except Exception:
            _cache[name] = None
    return _cache[name]


def warm():
    """Build all sounds now so the first play has no hitch."""
    for name in _MAKERS:
        _get(name)


def play(name, volume=0.5):
    if not prefs.get("sfx"):
        return
    sound = _get(name)
    if sound:
        sound.set_volume(volume)
        sound.play()