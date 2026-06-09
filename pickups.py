import math
import pygame
from settings import *

# Per-kind config: what it gives the player
_CONFIGS = {
    'milk':    {'hp': 25,  'crystals': 0,  'mana': 0,   'label': '+25 HP',      'color': (240, 245, 255)},
    'salmon':  {'hp': 50,  'crystals': 0,  'mana': 0,   'label': '+50 HP',      'color': (255, 140, 100)},
    'crystal': {'hp': 0,   'crystals': 1,  'mana': 0,   'label': '+Crystal',    'color': ( 80, 220, 255)},
    'dog':     {'hp': 0,   'crystals': 10, 'mana': 100, 'label': 'Woof! +Mana', 'color': (160,  90,  30)},
}

_SIZE = 20   # half-size of collision box


class Pickup:
    def __init__(self, world_x, kind):
        self.x         = float(world_x)
        self.y         = float(GROUND_Y - _SIZE)
        self.kind      = kind
        self.collected = False
        self._bob_t    = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - _SIZE, int(self.y) - _SIZE, _SIZE * 2, _SIZE * 2)

    def try_collect(self, player):
        """Attempt collection by player. Returns label string on success, else None."""
        if self.collected:
            return None
        if not self.rect.colliderect(player.rect):
            return None
        cfg = _CONFIGS[self.kind]
        self.collected = True
        if cfg['hp']:
            player.hp = min(player.max_hp, player.hp + cfg['hp'])
        if cfg['crystals']:
            player.crystals += cfg['crystals']
            if player.crystals >= 20:
                player.crystals -= 20
                if player.lives < PLAYER_LIVES_MAX:
                    player.lives += 1
        if cfg['mana']:
            player.magic = player.max_magic
        return cfg['label']

    def draw(self, surface, cam_x):
        if self.collected:
            return
        self._bob_t += 1
        sx = int(self.x) - cam_x
        sy = int(self.y) + int(math.sin(self._bob_t * 0.09) * 4)
        if not (-40 <= sx <= SCREEN_W + 40):
            return
        col = _CONFIGS[self.kind]['color']
        _DRAWERS[self.kind](surface, sx, sy, col)


# ---------------------------------------------------------------------------
# Procedural shapes
# ---------------------------------------------------------------------------

def _draw_milk(surface, sx, sy, col):
    # Body
    pygame.draw.rect(surface, col,          (sx - 6,  sy - 14, 12, 16))
    # Neck
    pygame.draw.rect(surface, col,          (sx - 3,  sy - 18,  6,  6))
    # Blue label stripe
    pygame.draw.rect(surface, (90, 160, 230), (sx - 6, sy - 8,  12,  4))
    # Cap
    pygame.draw.rect(surface, (70, 70, 100),  (sx - 3, sy - 20,  6,  3))


def _draw_salmon(surface, sx, sy, col):
    # Outer slab
    pygame.draw.ellipse(surface, col,              (sx - 14, sy - 8, 28, 12))
    # Inner flesh stripe
    pygame.draw.ellipse(surface, (220, 90, 60),    (sx - 9,  sy - 5, 18,  6))


def _draw_crystal(surface, sx, sy, col):
    pts  = [(sx, sy - 14), (sx + 9, sy - 4), (sx, sy + 8), (sx - 9, sy - 4)]
    pygame.draw.polygon(surface, col, pts)
    inner = (min(255, col[0] + 60), min(255, col[1] + 60), min(255, col[2] + 60))
    pts2 = [(sx, sy - 10), (sx + 5, sy - 4), (sx, sy + 2), (sx - 5, sy - 4)]
    pygame.draw.polygon(surface, inner, pts2)


def _draw_dog(surface, sx, sy, col):
    # Body
    pygame.draw.ellipse(surface, col,         (sx - 12, sy - 7,  24, 12))
    # Head
    pygame.draw.circle(surface, col,          (sx + 11, sy - 8),  8)
    # Ear
    pygame.draw.ellipse(surface, (120, 60, 15), (sx + 14, sy - 16, 6, 8))
    # Eye
    pygame.draw.circle(surface, BLACK,        (sx + 13, sy - 9),  2)
    # Tail
    tail = [(sx - 12, sy - 4), (sx - 20, sy - 12), (sx - 22, sy - 6)]
    pygame.draw.polygon(surface, col, tail)
    # Legs
    for lx in (sx - 7, sx - 2, sx + 3, sx + 8):
        pygame.draw.rect(surface, col, (lx, sy + 4, 4, 6))


_DRAWERS = {
    'milk':    _draw_milk,
    'salmon':  _draw_salmon,
    'crystal': _draw_crystal,
    'dog':     _draw_dog,
}
