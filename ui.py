import pygame
from settings import *

# Module-level caches — survive across frames
_RC     = {}   # render cache: {(font_obj, text, col): surface}
_PANELS = {}   # panel cache:  {(w, h, fill_col): surface}


def _cr(font, text, col):
    key = (font, text, col)
    if key not in _RC:
        _RC[key] = font.render(text, True, col)
    return _RC[key]


def _panel(w, h, col=(0, 0, 0, 165)):
    key = (w, h, col)
    if key not in _PANELS:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(col)
        _PANELS[key] = s
    return _PANELS[key]


def _fonts():
    if not hasattr(_fonts, '_c'):
        _fonts._c = {
            'sm':  pygame.font.SysFont('Arial', 13, bold=True),
            'med': pygame.font.SysFont('Arial', 22, bold=True),
            'lg':  pygame.font.SysFont('Arial', 14, bold=True),
            'xs':  pygame.font.SysFont('Arial', 11, bold=True),
        }
    return _fonts._c


# ---------------------------------------------------------------------------

def draw_hud(surface, players, score, enemies):
    f = _fonts()
    _draw_score(surface, score, f)
    _draw_boss_bar(surface, enemies, f)

    p1 = players[0]
    p2 = players[1] if len(players) > 1 else None

    _draw_player_panel(surface, p1, left=True, fonts=f)
    if p2:
        _draw_player_panel(surface, p2, left=False, fonts=f)

    _draw_controls_hint(surface, f)


# ---------------------------------------------------------------------------

def _draw_player_panel(surface, player, left, fonts):
    pw, ph = 215, 64
    px = 8 if left else SCREEN_W - pw - 8
    py = 8

    surface.blit(_panel(pw, ph), (px, py))

    border_col = (60, 80, 140) if player.player_id == 1 else (140, 60, 60)
    pygame.draw.rect(surface, border_col, (px, py, pw, ph), 2)

    _named_chars = {'asaf', 'lotem', 'gal', 'nitay', 'yael'}
    _cn = getattr(player, 'char_name', '')
    char_name = _cn.upper() if _cn in _named_chars else 'KNIGHT'
    name = f'P{player.player_id} — {char_name}'
    lbl = _cr(fonts['xs'], name, border_col)
    surface.blit(lbl, (px + 6, py + 4))

    max_show = max(PLAYER_LIVES, player.lives)
    for i in range(max_show):
        col = LIFE_COL if i < player.lives else (50, 20, 20)
        hx = px + pw - 14 - i * 16
        hy = py + 5
        _draw_heart(surface, hx, hy, col)

    _bar(surface, px + 6, py + 20, pw - 12, 15,
         player.hp, player.max_hp, HP_GREEN, HP_BG, 'HP', fonts['xs'])
    _bar(surface, px + 6, py + 40, pw - 12, 15,
         player.magic, player.max_magic, MAGIC_COL, MAGIC_BG, 'MP', fonts['xs'])

    gem_surf = _cr(fonts['xs'], f'◆ {player.crystals} / 20', (80, 220, 255))
    surface.blit(gem_surf, (px + 6, py + ph + 2))


def _draw_heart(surface, x, y, col):
    pygame.draw.circle(surface, col, (x + 3, y + 3), 3)
    pygame.draw.circle(surface, col, (x + 9, y + 3), 3)
    pygame.draw.polygon(surface, col, [(x, y + 5), (x + 6, y + 13), (x + 12, y + 5)])


def _bar(surface, x, y, w, h, val, max_val, fill_col, bg_col, label, font):
    pygame.draw.rect(surface, bg_col, (x, y, w, h), border_radius=3)
    fill_w = max(0, int(w * val / max_val)) if max_val else 0
    if fill_w:
        pygame.draw.rect(surface, fill_col, (x, y, fill_w, h), border_radius=3)
        pygame.draw.rect(surface, tuple(min(255, c + 50) for c in fill_col),
                         (x, y, fill_w, h // 3), border_radius=3)
    pygame.draw.rect(surface, (70, 70, 70), (x, y, w, h), 1, border_radius=3)
    surface.blit(_cr(font, label, WHITE), (x + 4, y + 2))


def _draw_score(surface, score, fonts):
    txt    = _cr(fonts['med'], f'SCORE  {score:,}', SCORE_COL)
    shadow = _cr(fonts['med'], f'SCORE  {score:,}', BLACK)
    r = txt.get_rect(centerx=SCREEN_W // 2, top=12)
    surface.blit(shadow, (r.x + 2, r.y + 2))
    surface.blit(txt,    r)


def _draw_boss_bar(surface, enemies, fonts):
    from enemy import Boss
    boss = next((e for e in enemies if isinstance(e, Boss)), None)
    if boss is None:
        return

    bar_w, bar_h = 430, 26
    bx = SCREEN_W // 2 - bar_w // 2
    by = SCREEN_H - 60

    surface.blit(_panel(bar_w + 26, bar_h + 40, (0, 0, 0, 180)), (bx - 13, by - 26))
    pygame.draw.rect(surface, (130, 40, 150),
                     (bx - 13, by - 26, bar_w + 26, bar_h + 40), 2)

    name = _cr(fonts['lg'], '☠  B O S S  ☠', (215, 130, 235))
    surface.blit(name, (SCREEN_W // 2 - name.get_width() // 2, by - 20))

    pygame.draw.rect(surface, (40, 10, 42), (bx, by, bar_w, bar_h), border_radius=5)
    fill_w = max(0, int(bar_w * boss.hp / boss.max_hp))
    if fill_w:
        pygame.draw.rect(surface, (155, 32, 165), (bx, by, fill_w, bar_h), border_radius=5)
        pygame.draw.rect(surface, (195, 58, 208), (bx, by, fill_w, bar_h // 2), border_radius=5)
    pygame.draw.rect(surface, (90, 50, 100), (bx, by, bar_w, bar_h), 2, border_radius=5)

    hp_txt = _cr(fonts['sm'], f'{boss.hp} / {boss.max_hp}', WHITE)
    surface.blit(hp_txt, (SCREEN_W // 2 - hp_txt.get_width() // 2, by + 6))


def _draw_controls_hint(surface, fonts):
    hint = _cr(fonts['xs'],
               'P1: Arrows Move · Space/Up Jump · Ins Attack · Del Heavy · Home Magic      '
               'P2: WASD Move · W Jump · Tab Attack · CapsLock Heavy · LShift Magic',
               (130, 140, 160))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 16))
