import pygame
from settings import *


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

    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 165))
    surface.blit(panel, (px, py))

    border_col = (60, 80, 140) if player.player_id == 1 else (140, 60, 60)
    pygame.draw.rect(surface, border_col, (px, py, pw, ph), 2)

    # Label — use char_name (always set) for known chars, else KNIGHT
    _named_chars = {'asaf', 'lotem', 'gal', 'nitay', 'yael'}
    _cn = getattr(player, 'char_name', '')
    char_name = _cn.upper() if _cn in _named_chars else 'KNIGHT'
    name = f'P{player.player_id} — {char_name}'
    lbl = fonts['xs'].render(name, True, border_col)
    surface.blit(lbl, (px + 6, py + 4))

    # Lives (heart icons — show up to PLAYER_LIVES_MAX = 5)
    max_show = max(PLAYER_LIVES, player.lives)
    for i in range(max_show):
        col = LIFE_COL if i < player.lives else (50, 20, 20)
        hx = px + pw - 14 - i * 16
        hy = py + 5
        _draw_heart(surface, hx, hy, col)

    # HP bar
    _bar(surface, px + 6, py + 20, pw - 12, 15,
         player.hp, player.max_hp, HP_GREEN, HP_BG, 'HP', fonts['xs'])

    # Magic bar
    _bar(surface, px + 6, py + 40, pw - 12, 15,
         player.magic, player.max_magic, MAGIC_COL, MAGIC_BG, 'MP', fonts['xs'])

    # Crystal counter — shown below the panel so it never overlaps
    gem_surf = fonts['xs'].render(f'◆ {player.crystals} / 100', True, (80, 220, 255))
    surface.blit(gem_surf, (px + 6, py + ph + 2))


def _draw_heart(surface, x, y, col):
    """Simple heart shape using two circles + triangle."""
    pygame.draw.circle(surface, col, (x + 3, y + 3), 3)
    pygame.draw.circle(surface, col, (x + 9, y + 3), 3)
    pygame.draw.polygon(surface, col, [(x, y + 5), (x + 6, y + 13), (x + 12, y + 5)])


def _bar(surface, x, y, w, h, val, max_val, fill_col, bg_col, label, font):
    pygame.draw.rect(surface, bg_col, (x, y, w, h), border_radius=3)
    fill_w = max(0, int(w * val / max_val)) if max_val else 0
    if fill_w:
        pygame.draw.rect(surface, fill_col, (x, y, fill_w, h), border_radius=3)
        # Highlight strip
        pygame.draw.rect(surface, tuple(min(255, c + 50) for c in fill_col),
                         (x, y, fill_w, h // 3), border_radius=3)
    pygame.draw.rect(surface, (70, 70, 70), (x, y, w, h), 1, border_radius=3)
    lbl = font.render(label, True, WHITE)
    surface.blit(lbl, (x + 4, y + 2))


def _draw_score(surface, score, fonts):
    txt    = fonts['med'].render(f'SCORE  {score:,}', True, SCORE_COL)
    shadow = fonts['med'].render(f'SCORE  {score:,}', True, BLACK)
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

    panel = pygame.Surface((bar_w + 26, bar_h + 40), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    surface.blit(panel, (bx - 13, by - 26))
    pygame.draw.rect(surface, (130, 40, 150),
                     (bx - 13, by - 26, bar_w + 26, bar_h + 40), 2)

    name = fonts['lg'].render('☠  B O S S  ☠', True, (215, 130, 235))
    surface.blit(name, (SCREEN_W // 2 - name.get_width() // 2, by - 20))

    pygame.draw.rect(surface, (40, 10, 42), (bx, by, bar_w, bar_h), border_radius=5)
    fill_w = max(0, int(bar_w * boss.hp / boss.max_hp))
    if fill_w:
        pygame.draw.rect(surface, (155, 32, 165), (bx, by, fill_w, bar_h), border_radius=5)
        pygame.draw.rect(surface, (195, 58, 208), (bx, by, fill_w, bar_h // 2), border_radius=5)
    pygame.draw.rect(surface, (90, 50, 100), (bx, by, bar_w, bar_h), 2, border_radius=5)

    hp_txt = fonts['sm'].render(f'{boss.hp} / {boss.max_hp}', True, WHITE)
    surface.blit(hp_txt, (SCREEN_W // 2 - hp_txt.get_width() // 2, by + 6))


def _draw_controls_hint(surface, fonts):
    hint = fonts['xs'].render(
        'P1: Arrows/WASD Move · Space Jump · Ins Attack · Del Heavy · Home Magic      '
        'P2: J/L Move · I Jump · , Attack · . Heavy · ; Magic',
        True, (130, 140, 160))
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 16))
