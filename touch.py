"""
On-screen virtual gamepad for mobile/tablet web play (Pygbag).
Shows translucent D-pad (left side) and action buttons (right side).
Supports pygame FINGERDOWN/FINGERMOTION/FINGERUP (touch) and
MOUSEBUTTONDOWN/MOUSEBUTTONUP/MOUSEMOTION (desktop testing).
"""
import pygame
from settings import SCREEN_W, SCREEN_H

# ---------------------------------------------------------------------------
# Button layout — bottom corners, chosen to stay out of the action area
# ---------------------------------------------------------------------------
_PAD_BTNS = {
    'left':   pygame.Rect(10,  500, 68, 68),
    'right':  pygame.Rect(90,  500, 68, 68),
    'jump':   pygame.Rect(50,  425, 68, 68),
    'attack': pygame.Rect(868, 500, 68, 68),
    'heavy':  pygame.Rect(948, 500, 68, 68),
    'magic':  pygame.Rect(908, 425, 68, 68),
}

_LABELS = {
    'left':   '<',
    'right':  '>',
    'jump':   '^',
    'attack': 'ATK',
    'heavy':  'HVY',
    'magic':  'MAG',
}

_COLORS = {
    'left':   (100, 140, 240),
    'right':  (100, 140, 240),
    'jump':   (80,  200, 120),
    'attack': (230, 80,  80),
    'heavy':  (230, 160, 60),
    'magic':  (150, 80,  230),
}


class VirtualPad:
    """Stateful virtual gamepad — call handle_event() each frame."""

    def __init__(self):
        self._held    = {k: False for k in _PAD_BTNS}
        self._fingers = {}   # id → (screen_x, screen_y)
        self._font    = None

    # ------------------------------------------------------------------ events

    def handle_event(self, event):
        """Route pygame events here; updates button-held state."""
        t = event.type
        if t == pygame.FINGERDOWN:
            self._fingers[event.finger_id] = (
                int(event.x * SCREEN_W), int(event.y * SCREEN_H))
        elif t == pygame.FINGERMOTION:
            self._fingers[event.finger_id] = (
                int(event.x * SCREEN_W), int(event.y * SCREEN_H))
        elif t == pygame.FINGERUP:
            self._fingers.pop(event.finger_id, None)
        elif t == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._fingers['_m'] = event.pos
        elif t == pygame.MOUSEBUTTONUP and event.button == 1:
            self._fingers.pop('_m', None)
        elif t == pygame.MOUSEMOTION and '_m' in self._fingers:
            self._fingers['_m'] = event.pos
        self._refresh()

    def _refresh(self):
        for name, rect in _PAD_BTNS.items():
            self._held[name] = any(
                rect.collidepoint(pos) for pos in self._fingers.values())

    # ------------------------------------------------------------------ public

    def get_state(self):
        """Return {action: bool} for merging into player virtual_input."""
        return dict(self._held)

    def draw(self, surface):
        """Draw translucent buttons onto surface at fixed screen coords."""
        if self._font is None:
            self._font = pygame.font.SysFont('Arial', 18, bold=True)
        f = self._font
        for name, rect in _PAD_BTNS.items():
            col = _COLORS[name]
            alpha = 200 if self._held[name] else 85
            btn = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            btn.fill((*col, alpha))
            # Rounded border
            pygame.draw.rect(btn, (255, 255, 255, 160),
                             (0, 0, rect.w, rect.h), 2, border_radius=12)
            surface.blit(btn, rect)
            lbl = f.render(_LABELS[name], True, (255, 255, 255))
            surface.blit(lbl, lbl.get_rect(center=rect.center))
