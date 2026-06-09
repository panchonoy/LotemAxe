import pygame
from settings import SCREEN_W, SCREEN_H

_BLOB_CACHE = {}   # keyed by (radius, kind)


def _bake_blob(radius, kind='warm'):
    radius = max(4, (radius // 2) * 2)   # snap to even numbers
    key = (radius, kind)
    if key in _BLOB_CACHE:
        return _BLOB_CACHE[key]

    diam = radius * 2
    surf = pygame.Surface((diam, diam))
    surf.fill((0, 0, 0))
    steps = max(8, min(radius, 50))
    for i in range(steps, 0, -1):
        t = (i / steps) ** 1.5   # power falloff: sharp edge, bright core
        b = int(255 * t)
        if kind == 'warm':
            col = (b, int(b * 0.58), int(b * 0.20))
        elif kind == 'hot':
            col = (b, int(b * 0.36), int(b * 0.05))
        elif kind == 'cool':
            col = (int(b * 0.80), int(b * 0.72), int(b * 0.48))
        else:
            col = (b, b, b)
        r_draw = max(1, i * radius // steps)
        pygame.draw.circle(surf, col, (radius, radius), r_draw)

    _BLOB_CACHE[key] = surf
    return surf


class LightLayer:
    _AMBIENT = {
        2: (70, 62, 86),    # cave: dark purple-grey
        4: (76, 20, 7),     # inferno: very dark warm
    }

    def __init__(self, level_num):
        self.level_num = level_num
        amb = self._AMBIENT.get(level_num, (60, 60, 60))
        self._dark = pygame.Surface((SCREEN_W, SCREEN_H))
        self._dark.fill(amb)
        # Pre-warm blob cache so first frame has no spike
        if level_num == 2:
            for r in range(50, 78, 2):
                _bake_blob(r, 'warm')
            _bake_blob(68, 'cool')
        elif level_num == 4:
            for r in range(44, 104, 2):
                _bake_blob(r, 'hot')
            _bake_blob(68, 'cool')

    def render(self, surface, lights):
        """Apply lighting over surface.
        lights: list of (screen_x, screen_y, radius, kind_str)
        """
        self._dark.fill(self._AMBIENT.get(self.level_num, (60, 60, 60)))
        for sx, sy, radius, kind in lights:
            if -radius - 2 <= sx <= SCREEN_W + radius + 2:
                blob = _bake_blob(int(radius), kind)
                self._dark.blit(blob, (sx - radius, sy - radius),
                                special_flags=pygame.BLEND_RGB_ADD)
        surface.blit(self._dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
