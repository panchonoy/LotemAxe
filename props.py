import pygame
import math
from settings import GROUND_Y, SCREEN_W

_BARREL_COL  = (110, 65, 25)
_BARREL_RING = (70,  40, 15)
_CRATE_COL   = (155, 120, 60)
_CRATE_LINE  = (120, 90, 40)
_VASE_COL    = (180, 90, 45)
_VASE_LINE   = (140, 70, 30)


class Prop:
    W = 28

    _H = {'barrel': 32, 'crate': 30, 'vase': 36}

    def __init__(self, wx, kind):
        self.wx    = float(wx)
        self.kind  = kind
        self.alive = True
        self.H     = self._H.get(kind, 30)
        self._die_t = 0    # break flash countdown

    @property
    def rect(self):
        return pygame.Rect(int(self.wx), GROUND_Y - self.H, self.W, self.H)

    def hit(self):
        """Returns True when the prop is broken for the first time."""
        if self.alive:
            self.alive  = False
            self._die_t = 16
            return True
        return False

    def update(self):
        """Returns True while still visible (alive or in death flash)."""
        if self._die_t > 0:
            self._die_t -= 1
        return self.alive or self._die_t > 0

    def draw(self, screen, cam_x):
        sx = int(self.wx) - cam_x
        if not (-50 <= sx <= SCREEN_W + 50):
            return
        sy = GROUND_Y - self.H

        if self._die_t > 0:
            self._draw_break(screen, sx, sy)
            return
        if not self.alive:
            return

        if self.kind == 'barrel':
            self._draw_barrel(screen, sx, sy)
        elif self.kind == 'crate':
            self._draw_crate(screen, sx, sy)
        else:
            self._draw_vase(screen, sx, sy)

    # ---------------------------------------------------------------- pieces
    def _draw_break(self, screen, sx, sy):
        frac = self._die_t / 16
        alpha = int(230 * frac)
        spread = int((1 - frac) * 22)
        col = _CRATE_COL if self.kind == 'crate' else (_BARREL_COL if self.kind == 'barrel' else _VASE_COL)
        hw = self.W // 2
        hh = self.H // 2
        # Four flying chunks
        offsets = [(-hw - spread, -spread), (hw + spread, -spread),
                   (-spread, hh + spread),  (spread,      hh + spread)]
        for ox, oy in offsets:
            chunk = pygame.Surface((10, 10), pygame.SRCALPHA)
            chunk.fill((*col, alpha))
            screen.blit(chunk, (sx + self.W // 2 + ox - 5, sy + self.H // 2 + oy - 5))

    # ---------------------------------------------------------------- shapes
    def _draw_barrel(self, screen, sx, sy):
        pygame.draw.rect(screen, _BARREL_COL, (sx + 4, sy, 20, self.H))
        pygame.draw.ellipse(screen, (90, 50, 18), (sx + 2, sy - 4, 24, 10))
        pygame.draw.ellipse(screen, (90, 50, 18), (sx + 2, sy + self.H - 6, 24, 10))
        pygame.draw.rect(screen, _BARREL_RING, (sx + 2, sy + 7, 24, 3))
        pygame.draw.rect(screen, _BARREL_RING, (sx + 2, sy + self.H - 12, 24, 3))

    def _draw_crate(self, screen, sx, sy):
        pygame.draw.rect(screen, _CRATE_COL, (sx, sy, self.W, self.H))
        pygame.draw.rect(screen, _CRATE_LINE, (sx, sy, self.W, self.H), 2)
        pygame.draw.line(screen, _CRATE_LINE, (sx, sy), (sx + self.W, sy + self.H), 2)
        pygame.draw.line(screen, _CRATE_LINE, (sx + self.W, sy), (sx, sy + self.H), 2)

    def _draw_vase(self, screen, sx, sy):
        mid = sx + self.W // 2
        # Body polygon (amphora shape)
        pts = [
            (sx + 4, sy + self.H),
            (sx,     sy + 14),
            (sx + 5, sy + 5),
            (mid,    sy + 2),
            (sx + self.W - 5, sy + 5),
            (sx + self.W,     sy + 14),
            (sx + self.W - 4, sy + self.H),
        ]
        pygame.draw.polygon(screen, _VASE_COL, pts)
        pygame.draw.polygon(screen, _VASE_LINE, pts, 2)
        pygame.draw.rect(screen, (150, 75, 35), (sx + 8, sy, 12, 6))
