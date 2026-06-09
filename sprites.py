"""
Sprite sheet loader for LotemAxe characters.

Characters:
  asaf  – dad (dark-haired adult), from Lotem_sprite.png top half
  lotem – toddler son,             from Lotem_sprite.png bottom half
  gal   – spiky-hair twin,         from twins_sprite.png top half
  nitay – curly-hair twin,         from twins_sprite.png bottom half

Background is removed per-frame via flood-fill from corners so that
white highlights inside sprites are preserved.
"""
import os
import pygame

try:
    from PIL import Image
    import numpy as np
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_DIR = os.path.dirname(__file__)
_LOTEM_PATH = os.path.join(_DIR, 'images', 'KayKit_Adventurers_2.0_FREE', 'Lotem_sprite.png')
_TWINS_PATH = os.path.join(_DIR, 'images', 'KayKit_Adventurers_2.0_FREE', 'twins_sprite.png')

# ---------------------------------------------------------------------------
# Frame layout: (x, y, w, h) in the source PNG — LEFT-facing row
# (right-facing is obtained by flipping)
# ---------------------------------------------------------------------------
_ASAF_FRAMES = {            # dad — Lotem_sprite.png top half, LEFT row y=177-267
    'idle':    [(103,177,44,91), (178,177,45,91)],
    'walk':    [(264,177,46,91), (346,177,51,91),
                (450,177,56,91), (531,177,47,91)],
    'run':     [(578,177,47,91), (662,177,46,91)],
    'attack':  [(738,177,47,91), (785,177,48,91)],
    'jump':    [(883,177,73,91)],
    'hurt':    [(1042,177,77,91)],
    'victory': [(1187,177,74,91)],
}

_LOTEM_FRAMES = {           # son — Lotem_sprite.png bottom half, LEFT row y=663-745
    'idle':    [(104,663,45,83), (170,663,46,83)],
    'walk':    [(262,663,46,83), (338,663,47,83),
                (445,663,51,83), (526,663,42,83)],
    'run':     [(568,663,43,83), (659,663,47,83)],
    'attack':  [(736,663,39,83), (775,663,39,83)],
    'jump':    [(881,663,65,83)],
    'hurt':    [(1047,663,71,83)],
    'victory': [(1186,663,74,83)],
}

_GAL_FRAMES = {             # spiky twin — twins_sprite.png Twin1 LEFT row y=224-321
    'idle':    [(103,224,47,98), (172,224,50,98)],
    'walk':    [(272,224,49,98), (353,224,52,98),
                (459,224,56,98), (549,224,42,98)],
    'run':     [(591,224,42,98), (665,224,54,98)],
    'attack':  [(746,224,44,98), (790,224,44,98)],
    'jump':    [(887,224,68,98)],
    'hurt':    [(1043,224,75,98)],
    'victory': [(1186,224,77,98)],
}

_NITAY_FRAMES = {           # curly twin — twins_sprite.png Twin2 LEFT row y=695-788
    'idle':    [(105,695,46,94), (174,695,47,94)],
    'walk':    [(268,695,49,94), (354,695,47,94),
                (455,695,54,94), (545,695,41,94)],
    'run':     [(586,695,41,94), (666,695,53,94)],
    'attack':  [(748,695,42,94), (790,695,42,94)],
    'jump':    [(887,695,66,94)],
    'hurt':    [(1050,695,68,94)],
    'victory': [(1189,695,76,94)],
}

# Ticks per frame for each animation state
ANIM_SPEED = {
    'idle':    12,
    'walk':     7,
    'run':      5,
    'attack':   6,
    'jump':    14,
    'hurt':    10,
    'victory': 14,
}

# Render heights — Lotem is smaller, Asaf is bigger
_CHAR_HEIGHTS = {
    'asaf':  78,
    'lotem': 55,
    'gal':   68,
    'nitay': 68,
    'yael':  68,
}

# Which source file each char uses
_YAEL_PATH = os.path.join(_DIR, 'images', 'Yael.png')

_YAEL_FRAMES = {            # Yael — Yael.png, dark-navy background
    'idle':    [(349, 60, 66, 145), (437, 60, 71, 145)],
    'walk':    [(532, 60, 64, 145), (683, 60, 69, 142),
                (772, 60, 68, 142), (856, 60, 70, 142)],
    'run':     [(935, 60, 71, 142), (1012, 60, 75, 142)],
    'attack':  [(30, 490, 114, 125), (536, 490, 104, 122)],  # punch + kick
    'jump':    [(106, 280, 73, 155)],
    'hurt':    [(748, 280, 79, 123)],
    'victory': [(158, 665, 91, 156), (290, 665, 72, 156), (387, 665, 98, 156)],
}

_CHAR_SHEET = {
    'asaf':  _LOTEM_PATH,
    'lotem': _LOTEM_PATH,
    'gal':   _TWINS_PATH,
    'nitay': _TWINS_PATH,
    'yael':  _YAEL_PATH,
}
_CHAR_FRAMES = {
    'asaf':  _ASAF_FRAMES,
    'lotem': _LOTEM_FRAMES,
    'gal':   _GAL_FRAMES,
    'nitay': _NITAY_FRAMES,
    'yael':  _YAEL_FRAMES,
}

# Background color per char: None = white/light bg; tuple = dark-bg key color
_CHAR_BG = {
    'yael': (2, 12, 34),
}

# Cache: (char, anim, idx) → pygame.Surface (original-size RGBA)
_cache: dict = {}
_ready = False


# ---------------------------------------------------------------------------
# Background removal
# ---------------------------------------------------------------------------
def _is_bg(r, g, b, thresh=215, spread=35):
    return (r > thresh and g > thresh and b > thresh
            and abs(int(r) - int(g)) < spread
            and abs(int(r) - int(b)) < spread
            and abs(int(g) - int(b)) < spread)


def _flood_fill_bg(crop_rgb):
    from collections import deque
    h, w = crop_rgb.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    q = deque()

    def seed(y, x):
        if not visited[y, x]:
            r, g, b = crop_rgb[y, x]
            if _is_bg(int(r), int(g), int(b)):
                visited[y, x] = True
                q.append((y, x))

    for y in range(h):
        seed(y, 0); seed(y, w - 1)
    for x in range(w):
        seed(0, x); seed(h - 1, x)

    while q:
        y, x = q.popleft()
        for ny, nx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                r, g, b = crop_rgb[ny, nx]
                if _is_bg(int(r), int(g), int(b)):
                    visited[ny, nx] = True
                    q.append((ny, nx))

    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = crop_rgb
    rgba[:, :, 3] = np.where(visited, 0, 255)
    return rgba


def _flood_fill_bg_colored(crop_rgb, bg_col, thresh=32):
    """Flood-fill background removal for a specific (dark) background color."""
    from collections import deque
    h, w = crop_rgb.shape[:2]
    bg = np.array(bg_col, dtype=int)
    visited = np.zeros((h, w), dtype=bool)
    q = deque()

    def seed(y, x):
        if not visited[y, x]:
            if np.abs(crop_rgb[y, x].astype(int) - bg).max() < thresh:
                visited[y, x] = True
                q.append((y, x))

    for y in range(h):
        seed(y, 0); seed(y, w - 1)
    for x in range(w):
        seed(0, x); seed(h - 1, x)

    while q:
        y, x = q.popleft()
        for ny, nx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                if np.abs(crop_rgb[ny, nx].astype(int) - bg).max() < thresh:
                    visited[ny, nx] = True
                    q.append((ny, nx))

    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = crop_rgb
    rgba[:, :, 3] = np.where(visited, 0, 255)
    return rgba


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
_PROCESSED_DIR = os.path.join(_DIR, 'images', 'processed')


def _load_processed() -> bool:
    """Try loading pre-baked RGBA PNGs from images/processed/. Returns True on success."""
    if not os.path.isdir(_PROCESSED_DIR):
        return False
    loaded = 0
    for char, frames_dict in _CHAR_FRAMES.items():
        for anim, rects in frames_dict.items():
            for i in range(len(rects)):
                path = os.path.join(_PROCESSED_DIR, f'{char}_{anim}_{i}.png')
                if not os.path.exists(path):
                    return False
                try:
                    _cache[(char, anim, i)] = pygame.image.load(path).convert_alpha()
                    loaded += 1
                except Exception:
                    return False
    return loaded > 0


def init():
    """Load and cache all sprite frames. Call after pygame.display.init()."""
    global _ready

    # Fast path: pre-processed PNGs work in browser (no PIL needed)
    if _load_processed():
        _ready = True
        return

    if not _PIL_OK:
        return

    # Load source sheets once
    sheets = {}
    for path in set(_CHAR_SHEET.values()):
        if os.path.exists(path):
            try:
                sheets[path] = np.array(Image.open(path).convert('RGB'))
            except Exception as exc:
                print(f'[sprites] cannot load {path}: {exc}')

    if not sheets:
        return

    try:
        for char, frames_dict in _CHAR_FRAMES.items():
            path = _CHAR_SHEET[char]
            src_np = sheets.get(path)
            if src_np is None:
                continue
            bg_col = _CHAR_BG.get(char)
            for anim, rects in frames_dict.items():
                for i, (x, y, w, h) in enumerate(rects):
                    crop = src_np[y:y+h, x:x+w]
                    if bg_col is not None:
                        rgba = _flood_fill_bg_colored(crop, bg_col)
                    else:
                        rgba = _flood_fill_bg(crop)
                    img_pil = Image.fromarray(rgba, 'RGBA')
                    surf = pygame.image.fromstring(
                        img_pil.tobytes(), img_pil.size, 'RGBA'
                    ).convert_alpha()
                    _cache[(char, anim, i)] = surf
        _ready = True
    except Exception as exc:
        print(f'[sprites] init error: {exc}')


def is_ready() -> bool:
    return _ready


def char_height(char: str) -> int:
    """Render height in pixels for this character."""
    return _CHAR_HEIGHTS.get(char, 68)


def get_frame(char: str, anim: str, idx: int,
              target_h: int, flip: bool = False):
    """
    Return a scaled pygame Surface.  Returns None if sprites aren't loaded.
    target_h is the desired render height in pixels.
    """
    frames_dict = _CHAR_FRAMES.get(char, {})
    rects = frames_dict.get(anim, [])
    if not rects:
        return None
    surf = _cache.get((char, anim, idx % len(rects)))
    if surf is None:
        return None

    ow, oh = surf.get_size()
    if oh == 0:
        return None
    scale_w = max(1, int(ow * target_h / oh))
    scaled = pygame.transform.scale(surf, (scale_w, target_h))
    if flip:
        scaled = pygame.transform.flip(scaled, True, False)
    return scaled


def frame_count(char: str, anim: str) -> int:
    return len(_CHAR_FRAMES.get(char, {}).get(anim, []))
