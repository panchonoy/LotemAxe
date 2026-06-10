import sys
import os
import math
import random
import pygame

from settings import *
from player import Player, P1_KEYS, P2_KEYS
from enemy import Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, Grunt, Heavy, Healer, Thrower, Jumper, Bomber, FlyingEye
from particles import spawn_hit, spawn_magic, spawn_death, spawn_pee, spawn_tornado, spawn_heal, spawn_explosion, spawn_lightning_chain
from level import Level
from pickups import Pickup
import ui
import sfx
import sprites
from touch import VirtualPad
from props import Prop, FallingBox
from lighting import LightLayer

# Game states
MENU         = 'menu'
COLOR_SELECT = 'color_select'
PLAYING      = 'playing'
GAME_OVER    = 'game_over'
VICTORY      = 'victory'   # kept for joystick compat; logic uses LEVEL_END
LEVEL_END    = 'level_end'
CREDITS      = 'credits'

HISCORE_FILE  = os.path.join(os.path.dirname(__file__), 'highscore.txt')

_yael_session = False   # True only after F6 or beating all 5 levels this session
_easy_mode    = False   # True after F7 — reduced enemy HP/damage, extra lives


def _is_yael_unlocked():
    return _yael_session


def _unlock_yael():
    global _yael_session
    _yael_session = True


def _toggle_easy_mode():
    global _easy_mode
    _easy_mode = not _easy_mode


def _is_easy_mode():
    return _easy_mode


def _load_hiscore():
    try:
        with open(HISCORE_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _save_hiscore(score):
    try:
        with open(HISCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception:
        pass


class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        sfx.init()
        sprites.init()
        pygame.joystick.init()
        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self._joysticks.append(j)

        self._init_fonts()
        self._vignette      = self._build_vignette()
        self._glow_surf     = pygame.Surface((SCREEN_W, SCREEN_H))
        self._red_flash_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self._red_flash_surf.fill((220, 20, 20))
        # Per-frame allocation caches — avoid WASM Surface/font.render costs
        self._esh_surfs          = {}  # enemy shadows keyed by pixel width
        self._efl_surfs          = {}  # enemy hit-flash surfs keyed by (W, H)
        self._float_text_cache   = {}  # float-text rendered surfs keyed by (text, col)
        self._hz_strip10         = pygame.Surface((SCREEN_W, 10))
        self._hz_strip6          = pygame.Surface((SCREEN_W, 6))
        self._magic_flash_surf   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._berserk_brd_surf   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.rect(self._berserk_brd_surf, (220, 20, 20, 55), (0, 0, SCREEN_W, SCREEN_H), 8)
        self._berserk_lbl        = self.font_float.render('BERSERK', True, (220, 40, 40))
        self._level_ov_surf      = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._level_ov_surf.fill((0, 0, 0, 170))
        self.hiscore              = _load_hiscore()
        self.num_players          = 1
        self.current_level        = 1
        self.state                = MENU
        self.berserk_mode         = False
        self._pending_bonus_lives = 0
        self._vpad                = VirtualPad()
        self._go_to_menu()

    # ------------------------------------------------------------------ setup
    def _init_fonts(self):
        self.font_title    = pygame.font.SysFont('Arial', 76, bold=True)
        self.font_big      = pygame.font.SysFont('Arial', 58, bold=True)
        self.font_med      = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_small    = pygame.font.SysFont('Arial', 19)
        self.font_hint     = pygame.font.SysFont('Arial', 14)
        self.font_float    = pygame.font.SysFont('Arial', 16, bold=True)
        self.font_gameover = pygame.font.SysFont('Arial', 28, bold=True)

    @staticmethod
    def _draw_touch_btn(surface, rect, label, col, font, active=False):
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((*col, 220 if active else 155))
        pygame.draw.rect(s, (255, 255, 255, 180), (0, 0, rect.w, rect.h), 2, border_radius=14)
        surface.blit(s, rect.topleft)
        lbl = font.render(label, True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=rect.center))

    def _build_vignette(self):
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i in range(55):
            alpha = max(0, 115 - i * 2)
            pygame.draw.rect(surf, (0, 0, 0, alpha),
                             (i, i, SCREEN_W - 2 * i, SCREEN_H - 2 * i), 1)
        return surf

    def _add_glow(self, sx, sy, radius, color, life=18):
        self._glows.append([int(sx), int(sy), int(radius),
                            color[0], color[1], color[2], life, life])

    def _draw_glows(self):
        if not self._glows:
            return
        self._glow_surf.fill((0, 0, 0))
        for gw in self._glows:
            lf = gw[6] / max(1, gw[7])
            r2 = max(2, int(gw[2] * (0.7 + 0.5 * (1.0 - lf))))
            sx, sy = gw[0], gw[1]
            if not (-r2 - 2 <= sx <= SCREEN_W + r2 + 2):
                continue
            col = (min(255, int(gw[3] * lf * 1.5)),
                   min(255, int(gw[4] * lf * 1.5)),
                   min(255, int(gw[5] * lf * 1.5)))
            pygame.draw.circle(self._glow_surf, (col[0] // 5, col[1] // 5, col[2] // 5), (sx, sy), r2)
            pygame.draw.circle(self._glow_surf, (col[0] // 2, col[1] // 2, col[2] // 2), (sx, sy), max(1, r2 * 2 // 3))
            pygame.draw.circle(self._glow_surf, col, (sx, sy), max(1, r2 // 3))
        self.screen.blit(self._glow_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def _get_lights(self):
        """Return list of (screen_x, screen_y, radius, kind) for the current frame."""
        lights = []
        cam = int(self.camera_x)
        t   = self.level._torch_t

        # Players always emit a warm aura
        for player in self.players:
            if not player.dead and not player.out_of_lives:
                sx = int(player.x) + P_W // 2 - cam
                sy = int(player.y) + P_H // 2
                lights.append((sx, sy, 68, 'cool'))

        if self.current_level == 2:
            flicker = int(abs(math.sin(t * 0.18)) * 10)
            for bg_x in self.level._torches:
                sx = bg_x - int(cam * 0.80)
                if -130 <= sx <= SCREEN_W + 130:
                    lights.append((sx, GROUND_Y - 85, 58 + flicker, 'warm'))

        return lights

    def _new_game(self, level_num=1):
        # Preserve crystal counts when advancing levels (not on fresh start)
        _saved_crystals = [p.crystals for p in getattr(self, 'players', [])] if level_num > 1 else []

        self.current_level = level_num
        joy2 = self._joysticks[0] if self._joysticks else None

        c1 = getattr(self, 'p1_color', 'asaf'  if sprites.is_ready() else 'blue')
        c2 = getattr(self, 'p2_color', 'lotem' if sprites.is_ready() else 'red')

        _SPRITE_CHARS = {'asaf', 'lotem', 'gal', 'nitay', 'yael'}

        def _make_player(x, pid, keys, color, joy=None):
            if color in _SPRITE_CHARS:
                return Player(x, GROUND_Y - P_H, player_id=pid,
                              key_bindings=keys, joystick=joy,
                              sprite_char=color)
            return Player(x, GROUND_Y - P_H, player_id=pid,
                          key_bindings=keys, joystick=joy, color=color)

        self.players = [_make_player(150, 1, P1_KEYS, c1)]
        if self.num_players == 2:
            self.players.append(_make_player(260, 2, P2_KEYS, c2, joy=joy2))

        # Restore crystal counts from previous level
        for i, p in enumerate(self.players):
            if i < len(_saved_crystals):
                p.crystals = _saved_crystals[i]

        # Apply bonus lives earned from previous level (stars / full-HP reward)
        if self._pending_bonus_lives > 0 and level_num > 1:
            for p in self.players:
                p.lives = min(PLAYER_LIVES_MAX, p.lives + self._pending_bonus_lives)
            self._pending_bonus_lives = 0

        # Easy mode: start each level with extra lives
        if _is_easy_mode() and level_num == 1:
            for p in self.players:
                p.lives = min(PLAYER_LIVES_MAX, p.lives + 4)

        self.enemies   = []
        self.particles = []
        self.camera_x  = 0.0
        self.score     = 0
        self.level     = Level(level_num, num_players=self.num_players)

        _LEVEL_DATA = {
            1: (PICKUPS_L1, PROPS_L1, []),
            2: (PICKUPS_L2, PROPS_L2, HAZARD_ZONES_L2),
            3: (PICKUPS_L3, PROPS_L3, HAZARD_ZONES_L3),
            4: (PICKUPS_L4, PROPS_L4, HAZARD_ZONES_L4),
            5: (PICKUPS_L5, PROPS_L5, HAZARD_ZONES_L5),
        }
        pickup_data, prop_data, hz_data = _LEVEL_DATA.get(level_num, _LEVEL_DATA[5])
        self.pickups   = [Pickup(wx, kind) for wx, kind in pickup_data]
        self._props    = [Prop(wx, kind)   for wx, kind in prop_data]
        self._hz_zones = list(hz_data)
        self._hz_timer = 0
        self._hz_dmg_timers = {}   # {player_index: frames_in_active_zone}
        self._float_texts = []   # [(screen_x, screen_y, text, color, frames_left)]

        self._hit_stop          = 0
        self._shake             = 0.0
        self._magic_flash       = 0
        self._victory_wait      = 0

        # Per-level tracking (stats, streak, stars)
        self._lvl_deaths  = 0
        self._hit_streak  = [0] * len(self.players)
        self._stats = [
            {'kills': 0, 'dmg_dealt': 0, 'dmg_taken': 0, 'specials': 0, 'peak_streak': 0}
            for _ in self.players
        ]
        self._level_stars = 0
        self._gameover_line_idx = random.randint(0, len(self._GAMEOVER_LINES) - 1)
        self._twin_assists      = []  # [[world_x, direction, frames_left, hit_set]]
        self._lava_timers       = {}  # {player_index: frames_in_lava}
        self._tsunami_timers    = {}  # {player_index: frames_in_tsunami}
        self._tsunami_resume_cd = 0   # grace frames after respawn before wave resumes

        # Falling hazards (active during boss fights from level 2+)
        self._hazards   = []  # [[world_x, y, vy, warn_t, type_idx]]
        self._hazard_cd = random.randint(FALL_HAZARD_MIN_CD, FALL_HAZARD_MAX_CD)
        self.rockets    = []  # live Rocket objects from RocketBoss
        self.blocks     = []  # live ToyBlock objects from DoriBoss

        # Buddy special (Team Blast)
        self._frame_t     = 0     # monotonic frame counter for sync detection
        self._buddy_cd    = 0     # cooldown: must reach 0 before next blast
        self._magic_frame = [-999, -999]  # frame each player last used magic

        # Falling crystal boxes
        self._fall_boxes  = []
        self._fall_box_cd = random.randint(FBOX_CD_MIN // 2, FBOX_CD_MIN)

        # Glow bursts (additive blended combat effects)
        self._glows = []
        # Death shockwave rings
        self._shockwaves = []
        self._sw_surf    = pygame.Surface((168, 168), pygame.SRCALPHA)  # max r=80 → 168×168
        # Level countdown timer
        self._level_timer_frames = LEVEL_TIME_LIMIT * FPS
        self._timer_surf_cache   = None  # (key, surf, shad) — avoid font.render every frame

        # Dynamic lighting for cave (L2) only — L4 uses heat shimmer + color grade instead
        self._light_layer = LightLayer(2) if level_num == 2 else None

        # Background music — look for music/level{n}.mp3 / .ogg / .wav
        music_dir = os.path.join(os.path.dirname(__file__), 'music')
        sfx.stop_music()
        for ext in ('mp3', 'ogg', 'wav'):
            music_path = os.path.join(music_dir, f'level{level_num}.{ext}')
            if os.path.exists(music_path):
                sfx.play_music(music_path)
                break

    def _go_to_menu(self):
        """Reset game state, play entry music, switch to MENU."""
        self._new_game()
        sfx.stop_music()
        music_dir = os.path.join(os.path.dirname(__file__), 'music')
        for ext in ('mp3', 'ogg', 'wav'):
            p = os.path.join(music_dir, f'entry.{ext}')
            if os.path.exists(p):
                sfx.play_music(p)
                break
        self.state = MENU

    # ----------------------------------------------------------- color select
    # sprite chars use the sprite sheet; the rest are knight color palettes
    _COLOR_OPTIONS_BASE = ['asaf', 'lotem', 'gal', 'nitay', 'blue', 'red', 'green', 'gold']
    _COLOR_OPTIONS_YAEL = ['asaf', 'lotem', 'gal', 'nitay', 'yael', 'blue', 'red', 'green', 'gold']
    _COLOR_MAP = {
        'blue':  ((45, 85, 195),  (65, 108, 218),  (28, 50, 155)),
        'red':   ((195, 65, 45),  (218, 90, 65),   (155, 28, 28)),
        'green': ((40, 160, 60),  (65, 195, 85),   (22, 105, 38)),
        'gold':  ((200, 165, 30), (225, 195, 60),  (155, 120, 15)),
        # Sprite chars get a representative "swatch" color for the UI circle
        'asaf':  ((60, 45, 25),   (80, 60, 35),    (35, 25, 12)),
        'lotem': ((220, 175, 130),(245, 200, 160),  (180, 140, 100)),
        'gal':   ((40, 35, 55),   (60, 55, 75),    (25, 20, 38)),
        'nitay': ((35, 30, 50),   (55, 50, 70),    (20, 15, 33)),
        'yael':  (YAEL_BODY,      YAEL_HEAD,       YAEL_CAPE),
    }

    @property
    def _COLOR_OPTIONS(self):
        return self._COLOR_OPTIONS_YAEL if _is_yael_unlocked() else self._COLOR_OPTIONS_BASE

    def _handle_color_select(self, key):
        opts = self._COLOR_OPTIONS
        n = len(opts)
        ready = getattr(self, '_p_ready', [False, False])

        def _advance(idx, direction, other_idx):
            idx = (idx + direction) % n
            if self.num_players == 2 and idx == other_idx:
                idx = (idx + direction) % n
            return idx

        # P1: arrow keys only — unready if they change selection
        if key == pygame.K_LEFT:
            if not ready[0]:
                self._color_cursor[0] = _advance(self._color_cursor[0], -1, self._color_cursor[1])
                self.p1_color = opts[self._color_cursor[0]]
        elif key == pygame.K_RIGHT:
            if not ready[0]:
                self._color_cursor[0] = _advance(self._color_cursor[0], +1, self._color_cursor[1])
                self.p1_color = opts[self._color_cursor[0]]

        # P2: A/D keys only
        elif self.num_players == 2 and key == pygame.K_a:
            if not ready[1]:
                self._color_cursor[1] = _advance(self._color_cursor[1], -1, self._color_cursor[0])
                self.p2_color = opts[self._color_cursor[1]]
        elif self.num_players == 2 and key == pygame.K_d:
            if not ready[1]:
                self._color_cursor[1] = _advance(self._color_cursor[1], +1, self._color_cursor[0])
                self.p2_color = opts[self._color_cursor[1]]

        # F7 easy mode toggle
        if key == pygame.K_F7:
            _toggle_easy_mode()

        # F6 Yael unlock (secret)
        if key == pygame.K_F6:
            _unlock_yael()
            opts = self._COLOR_OPTIONS
            n = len(opts)
            if 'yael' in opts:
                yi = opts.index('yael')
                self._color_cursor[0] = yi
                self.p1_color = 'yael'
                ready[0] = False
                if self.num_players == 2 and self._color_cursor[1] == yi:
                    self._color_cursor[1] = (yi + 1) % n
                    self.p2_color = opts[self._color_cursor[1]]

        # Confirm: P1 = ENTER, P2 = W
        if key == pygame.K_RETURN:
            ready[0] = True
        if self.num_players == 2 and key == pygame.K_w:
            ready[1] = True

        self._p_ready = ready

        # Start when all required players are ready
        needed = self.num_players
        if sum(ready[:needed]) == needed:
            lv = getattr(self, '_start_level', 1)
            self._start_level = 1
            self._p_ready = [False, False]
            self._pending_bonus_lives = 0   # fresh game — no carry-over
            self._new_game(level_num=lv)
            self.state = PLAYING

    # ------------------------------------------------------------------ run
    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            if self.state == PLAYING:
                self._update()
            self._draw()

    # ------------------------------------------------------------------ events
    def _handle_events(self):
        for event in pygame.event.get():
            self._vpad.handle_event(event)   # touch / mouse → virtual pad
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        if self.score > self.hiscore:
                            self.hiscore = self.score
                            _save_hiscore(self.hiscore)
                    self._go_to_menu()

                if self.state == MENU:
                    if event.key == pygame.K_b:
                        self.berserk_mode = not self.berserk_mode
                    _LEVEL_KEYS = {
                        pygame.K_F1: 1, pygame.K_F2: 2, pygame.K_F3: 3,
                        pygame.K_F4: 4, pygame.K_F5: 5,
                    }
                    if event.key in _LEVEL_KEYS:
                        self._start_level = _LEVEL_KEYS[event.key]
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif event.key == pygame.K_1:
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif event.key in (pygame.K_2, pygame.K_RETURN):
                        self.num_players = 1 if event.key == pygame.K_RETURN else 2
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT

                elif self.state == COLOR_SELECT:
                    self._handle_color_select(event.key)

                elif self.state in (VICTORY, LEVEL_END):
                    if event.key == pygame.K_RETURN:
                        if self.current_level >= 5:
                            self.state = CREDITS
                        else:
                            next_level = self.current_level + 1
                            self._new_game(level_num=next_level)
                            self.state = PLAYING
                elif self.state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self._go_to_menu()
                elif self.state == CREDITS:
                    if event.key == pygame.K_RETURN:
                        self._go_to_menu()

            # Touch / click on menu and character-select buttons
            if event.type == pygame.FINGERDOWN or \
               (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                if event.type == pygame.FINGERDOWN:
                    pos = (int(event.x * SCREEN_W), int(event.y * SCREEN_H))
                else:
                    pos = event.pos

                if self.state == MENU:
                    mb = getattr(self, '_menu_touch_btns', {})
                    if mb.get('start', pygame.Rect(0,0,0,0)).collidepoint(pos):
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color), opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif mb.get('2p', pygame.Rect(0,0,0,0)).collidepoint(pos):
                        self.num_players = 2
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color), opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif mb.get('berserk', pygame.Rect(0,0,0,0)).collidepoint(pos):
                        self.berserk_mode = not self.berserk_mode

                elif self.state == COLOR_SELECT:
                    cb = getattr(self, '_cs_touch_btns', {})
                    _KEY_MAP = {
                        'p1_left':  pygame.K_LEFT,
                        'p1_right': pygame.K_RIGHT,
                        'p1_ready': pygame.K_RETURN,
                        'p2_left':  pygame.K_a,
                        'p2_right': pygame.K_d,
                        'p2_ready': pygame.K_w,
                    }
                    for name, key in _KEY_MAP.items():
                        if cb.get(name, pygame.Rect(0,0,0,0)).collidepoint(pos):
                            self._handle_color_select(key)
                            break

            # Joystick start button
            if event.type == pygame.JOYBUTTONDOWN:
                if self.state == MENU and event.button == 9:  # Start
                    self.num_players = 1
                    self._new_game()
                    self.state = PLAYING
                elif self.state in (VICTORY, LEVEL_END) and event.button == 9:
                    if self.current_level >= 5:
                        self.state = CREDITS
                    else:
                        next_level = self.current_level + 1
                        self._new_game(level_num=next_level)
                        self.state = PLAYING
                elif self.state in (GAME_OVER, CREDITS) and event.button == 9:
                    self._go_to_menu()

    # ------------------------------------------------------------------ update
    def _update(self):
        if self._hit_stop > 0:
            self._hit_stop -= 1
            return

        self._frame_t += 1
        if self._buddy_cd > 0:
            self._buddy_cd -= 1

        all_keys = pygame.key.get_pressed()

        # Feed touch controls into P1's virtual input
        self.players[0].virtual_input = self._vpad.get_state()

        # --- Player input ---
        platforms = self.level.platforms
        pits      = self.level.pits
        for player in self.players:
            player.handle_input(all_keys)
            was_dead = player.dead
            player.update(int(self.camera_x), platforms, pits)
            if not was_dead and player.dead:
                self._lvl_deaths += 1
                pid = player.player_id - 1
                if pid < len(self._hit_streak):
                    self._hit_streak[pid] = 0
            if player.magic_just_used:
                player.magic_just_used = False
                self._do_magic(player)
            # Level 3: snap respawn position ahead of tsunami so player isn't killed instantly
            if (was_dead and not player.dead
                    and self.current_level == 3
                    and getattr(self.level, 'tsunami_active', False)):
                tsw = self.level.tsunami_world_x
                if player.x < tsw + 60:
                    player.x = float(tsw + 60)

        # --- Camera: follow the leading living player ---
        living = [p for p in self.players if not p.out_of_lives and not p.dead]
        if not living:
            living = self.players  # fallback if all dead (game-over handled below)
        lead_x = max(p.x for p in living)
        target_x = lead_x - CAM_LEAD
        self.camera_x += (target_x - self.camera_x) * 0.14
        # Tsunami camera-minimum: wave forces the viewport forward
        if self.current_level == 3 and getattr(self.level, 'tsunami_active', False):
            cam_min = max(0.0, self.level.tsunami_world_x - TSUNAMI_CAM_GAP)
        else:
            cam_min = 0.0
        self.camera_x = max(cam_min, min(self.camera_x, float(WORLD_W - SCREEN_W)))

        # --- Spawn new enemies ---
        any_alive = any(not p.dead and not p.out_of_lives for p in self.players)
        if not any_alive:
            self._tsunami_resume_cd = 120   # 2-second grace when wave was frozen
        elif self._tsunami_resume_cd > 0:
            self._tsunami_resume_cd -= 1
        freeze = not any_alive or self._tsunami_resume_cd > 0
        new_spawns = self.level.update(int(self.camera_x), freeze_tsunami=freeze)
        for e in new_spawns:
            if isinstance(e, Boss):
                sfx.play('boss_roar', 1.0)
        if self.berserk_mode:
            for e in new_spawns:
                e.SPEED   = e.SPEED * BERSERK_SPEED_MULT
                e.atk_dmg = int(e.atk_dmg * BERSERK_DMG_MULT)
        if _is_easy_mode():
            for e in new_spawns:
                e.hp      = max(1, e.hp // 2)
                e.atk_dmg = max(1, e.atk_dmg // 2)
        self.enemies.extend(new_spawns)

        # Swarm warning flash
        if self.level.swarm_active:
            self.level.swarm_active = False
            self._float_texts.append([SCREEN_W // 2, SCREEN_H // 3,
                                      '!! SWARM !!', (255, 55, 55), 110])
            self._shake       = max(self._shake, 10.0)
            self._magic_flash = max(self._magic_flash, 25)

        # --- Enemy update + combat ---
        dead_this_frame = []
        for enemy in self.enemies:
            enemy.update(self.players)
            if getattr(enemy, '_hit_flash', 0) > 0:
                enemy._hit_flash -= 1
            hit, target_player = enemy.can_attack(self.players)
            if hit and target_player:
                if target_player.take_damage(enemy.atk_dmg):
                    self._shake = max(self._shake, 6.0)
                    tp_pid = target_player.player_id - 1
                    if tp_pid < len(self._stats):
                        self._stats[tp_pid]['dmg_taken'] += enemy.atk_dmg
                        self._hit_streak[tp_pid] = 0
            # Boss charge area-hit shake
            if hasattr(enemy, '_charge_timer') and enemy._charge_timer > 0:
                self._shake = max(self._shake, 5.0)

        # Player swords vs enemies
        for player in self.players:
            if player.dead or player.out_of_lives:
                continue
            atk = player.atk_rect
            if atk and player.atk_timer == player.current_atk_dur - 1:
                sfx.play('swing', 0.6)
            if not atk:
                continue
            for enemy in self.enemies:
                if enemy in player._hit_set:
                    continue
                if atk.colliderect(enemy.rect):
                    player._hit_set.add(enemy)
                    kb_dir = 1 if enemy.rect.centerx >= player.rect.centerx else -1
                    dmg   = player.current_atk_dmg
                    stun  = player.current_atk_stun
                    if enemy.take_damage(dmg, kb_dir, stun):
                        scr_x = atk.centerx - int(self.camera_x)
                        spawn_hit(self.particles, scr_x, atk.centery)
                        self._add_glow(scr_x, atk.centery, 30, (255, 220, 90), 13)
                        self._hit_stop = max(self._hit_stop, 3)
                        sfx.play('hit', 0.7)
                        pid = player.player_id - 1
                        if pid < len(self._stats):
                            self._stats[pid]['dmg_dealt'] += dmg
                            self._hit_streak[pid] += 1
                            if self._hit_streak[pid] > self._stats[pid]['peak_streak']:
                                self._stats[pid]['peak_streak'] = self._hit_streak[pid]
                            if self._hit_streak[pid] >= COMBO_LIFE_THRESHOLD:
                                self._award_combo_life(player, pid)
                        if enemy.dead:
                            score_add = enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                            self.score += score_add
                            dead_this_frame.append(enemy)
                            sfx.play('death', 0.5)
                            if pid < len(self._stats):
                                self._stats[pid]['kills'] += 1

        for e in dead_this_frame:
            if isinstance(e, Bomber):
                continue   # death FX fires when fuse burns (handled below)
            scr_x = e.rect.centerx - int(self.camera_x)
            spawn_death(self.particles, scr_x, e.rect.centery, e.death_color)
            self._add_glow(scr_x, e.rect.centery, 52, e.death_color, 22)
            self._shockwaves.append([e.rect.centerx, e.rect.centery, e.death_color, 18])
            if random.random() < POWERUP_DROP_CHANCE:
                kind = random.choice(['speedstar', 'ragefist'])
                self.pickups.append(Pickup(e.rect.centerx, kind))

        # Bomber explosions: fires after fuse countdown
        for enemy in self.enemies:
            if isinstance(enemy, Bomber) and enemy.pending_explosion:
                enemy.pending_explosion = False
                ecx = enemy.rect.centerx
                scr_x = ecx - int(self.camera_x)
                spawn_explosion(self.particles, scr_x, int(enemy.y + enemy.H // 2))
                self._shake = max(self._shake, 12.0)
                self._magic_flash = max(self._magic_flash, 12)
                for player in self.players:
                    if player.dead or player.out_of_lives:
                        continue
                    if abs(player.rect.centerx - ecx) < BOMBER_RADIUS:
                        player.take_damage(BOMBER_EXPL_DMG)
                # Splash damage to nearby minions (excludes bosses + the bomber itself)
                for other in self.enemies:
                    if other is enemy or other.dead:
                        continue
                    if isinstance(other, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)):
                        continue
                    if abs(other.rect.centerx - ecx) < BOMBER_RADIUS:
                        other.take_damage(BOMBER_EXPL_DMG // 2)
                scr_x_int = scr_x
                self._float_texts.append([scr_x_int, int(enemy.y) - 10,
                                          'BOOM!', (255, 120, 0), 40])

        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        # --- RocketBoss rockets ---
        for enemy in self.enemies:
            if isinstance(enemy, RocketBoss):
                if enemy.pending_rockets:
                    self.rockets.extend(enemy.pending_rockets)
                    enemy.pending_rockets = []
                if enemy.fire_text:
                    scr_x = enemy.rect.centerx - int(self.camera_x)
                    self._float_texts.append([scr_x, int(enemy.y) - 14,
                                              enemy.fire_text, (255, 100, 20), 45])
                    enemy.fire_text = ''

        live_rockets = []
        for rocket in self.rockets:
            rocket.update()
            if not rocket.alive:
                continue
            hit = False
            for player in self.players:
                if player.dead or player.out_of_lives or player.hurt_timer > 0:
                    continue
                if rocket.rect.colliderect(player.rect):
                    if player.take_damage(rocket.dmg):
                        self._shake = max(self._shake, 8.0)
                        rk_pid = player.player_id - 1
                        if rk_pid < len(self._stats):
                            self._stats[rk_pid]['dmg_taken'] += rocket.dmg
                            self._hit_streak[rk_pid] = 0
                    scr_x = rocket.rect.centerx - int(self.camera_x)
                    spawn_explosion(self.particles, scr_x, rocket.rect.centery)
                    hit = True
                    break
            if not hit:
                live_rockets.append(rocket)
        self.rockets = live_rockets

        # --- DoriBoss toy blocks ---
        for enemy in self.enemies:
            if isinstance(enemy, DoriBoss):
                if enemy.pending_blocks:
                    self.blocks.extend(enemy.pending_blocks)
                    enemy.pending_blocks = []
                if enemy.block_text:
                    scr_x = enemy.rect.centerx - int(self.camera_x)
                    self._float_texts.append([scr_x, int(enemy.y) - 14,
                                              enemy.block_text, (238, 202, 45), 50])
                    enemy.block_text = ''

        live_blocks = []
        for block in self.blocks:
            block.update()
            if not block.alive:
                continue
            hit = False
            for player in self.players:
                if player.dead or player.out_of_lives or player.hurt_timer > 0:
                    continue
                if block.rect.colliderect(player.rect):
                    if player.take_damage(block.dmg):
                        self._shake = max(self._shake, 6.0)
                        bl_pid = player.player_id - 1
                        if bl_pid < len(self._stats):
                            self._stats[bl_pid]['dmg_taken'] += block.dmg
                            self._hit_streak[bl_pid] = 0
                    scr_x = block.rect.centerx - int(self.camera_x)
                    spawn_hit(self.particles, scr_x, block.rect.centery)
                    hit = True
                    break
            if not hit:
                live_blocks.append(block)
        self.blocks = live_blocks

        # --- Projectile hits (Thrower + TeacherBoss chalk) ---
        for enemy in self.enemies:
            if hasattr(enemy, 'pending_hits'):
                for player, dmg in enemy.pending_hits:
                    if player.take_damage(dmg):
                        self._shake = max(self._shake, 4.0)
                        sfx.play('hit', 0.5)
                        pr_pid = player.player_id - 1
                        if pr_pid < len(self._stats):
                            self._stats[pr_pid]['dmg_taken'] += dmg
                            self._hit_streak[pr_pid] = 0

        # --- TeacherBoss: reinforcement spawns + SILENCE! float text ---
        for enemy in self.enemies:
            if hasattr(enemy, 'pending_spawns') and enemy.pending_spawns:
                for gx in enemy.pending_spawns:
                    gx = max(50, min(int(gx), WORLD_W - 50))
                    self.enemies.append(self.level.spawn_grunt(gx))
                enemy.pending_spawns = []

            # Mid-fight wave spawns (Boss weakpoint HP-threshold waves)
            if getattr(enemy, 'pending_wave_spawns', None):
                _KIND_MAP = {
                    'grunt': lambda gx: Grunt(gx, GROUND_Y - Grunt.H),
                    'heavy': lambda gx: Heavy(gx, GROUND_Y - Heavy.H),
                    'eye':   lambda gx: FlyingEye(gx, GROUND_Y - FlyingEye.H - 30),
                }
                for (gx, kind) in enemy.pending_wave_spawns:
                    gx = max(50, min(int(gx), WORLD_W - 50))
                    factory = _KIND_MAP.get(kind)
                    if factory:
                        new_e = factory(gx)
                        if self.berserk_mode:
                            new_e.SPEED   = new_e.SPEED   * BERSERK_SPEED_MULT
                            new_e.atk_dmg = int(new_e.atk_dmg * BERSERK_DMG_MULT)
                        self.enemies.append(new_e)
                # Show wave alert on boss
                scr_x = enemy.rect.centerx - int(self.camera_x)
                self._float_texts.append([scr_x, enemy.rect.top - 14,
                                          'MINION WAVE!', (255, 200, 60), 80])
                enemy.pending_wave_spawns = []
            if hasattr(enemy, 'swing_text') and enemy.swing_text:
                scr_x = enemy.rect.centerx - int(self.camera_x)
                self._float_texts.append([scr_x, enemy.rect.top - 10, enemy.swing_text,
                                          (255, 80, 80), 55])
                enemy.swing_text = ''

        # --- Enemy platform correction ---
        if platforms:
            for enemy in self.enemies:
                if not enemy.dead and not enemy.on_ground and enemy.vy >= 0:
                    ecx = enemy.x + enemy.W // 2
                    for wx, wy, pw in platforms:
                        if wx <= ecx <= wx + pw:
                            prev_feet = (enemy.y + enemy.H) - enemy.vy
                            curr_feet = enemy.y + enemy.H
                            if prev_feet <= wy <= curr_feet:
                                enemy.y = float(wy - enemy.H)
                                enemy.vy = 0.0
                                enemy.on_ground = True
                                break

        # --- Pit collision ---
        # Decrement pit-avoidance cooldowns once per frame (outside pit loop)
        for enemy in self.enemies:
            if getattr(enemy, '_pit_avoid_cd', 0) > 0:
                enemy._pit_avoid_cd -= 1

        for pit_x1, pit_x2 in self.level.pits:
            # Players: always bounce out — don't wait for hurt_timer to expire
            for player in self.players:
                if player.dead or player.out_of_lives:
                    continue
                pcx = int(player.x) + P_W // 2
                if pit_x1 <= pcx <= pit_x2 and player.y > GROUND_Y + 20:
                    # Snap back above ground and eject to nearest pit edge
                    player.vy = JUMP_VY * 0.85
                    player.y  = float(GROUND_Y - P_H)
                    if pcx - pit_x1 < pit_x2 - pcx:
                        player.x = float(pit_x1 - P_W - 2)
                    else:
                        player.x = float(pit_x2 + 2)
                    self._shake = max(self._shake, 5.0)
                    player.take_damage(30)  # damage attempt (blocked by hurt_timer = intentional)

            # --- Pit avoidance AI ---
            # Runs every frame: hard-walls enemies out of the pit, no intentional fall-ins
            GUARD = 22   # px before pit edge to start blocking
            for enemy in self.enemies:
                if enemy.dead or not enemy.on_ground:
                    continue
                if isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, FlyingEye)):
                    continue
                ecx = enemy.rect.centerx
                if not (pit_x1 - GUARD <= ecx <= pit_x2 + GUARD):
                    continue

                closer_to_left = (ecx - pit_x1) < (pit_x2 - ecx)
                toward_pit = 1 if closer_to_left else -1

                # Hard reposition if inside kill zone (safety net)
                if pit_x1 <= ecx <= pit_x2:
                    enemy.x = float(pit_x1 - enemy.W) if closer_to_left else float(pit_x2 + 1)
                    enemy.vx = -float(toward_pit) * enemy.SPEED
                    enemy.facing = 1 if enemy.vx > 0 else -1

                # Block forward movement toward the pit every frame
                elif ecx < pit_x1 and enemy.vx > 0:
                    enemy.x  = float(pit_x1 - enemy.W)
                    enemy.vx = 0.0
                elif ecx > pit_x2 and enemy.vx < 0:
                    enemy.x  = float(pit_x2 + 1)
                    enemy.vx = 0.0
                else:
                    continue   # inside guard zone but moving away — nothing to do

                # Jumpers jump across (cooldown prevents repeated triggering)
                if isinstance(enemy, Jumper) and getattr(enemy, '_pit_avoid_cd', 0) == 0:
                    enemy.vy = JP_LEAP_VY
                    enemy.on_ground = False
                    enemy._is_leaping = True
                    enemy.vx = float(toward_pit) * max(abs(enemy.vx) if enemy.vx else 1.0,
                                                        enemy.SPEED * 2.5)
                    enemy._pit_avoid_cd = 55

            # Enemies: die immediately when they walk into the pit
            for enemy in self.enemies:
                if not enemy.dead and enemy.on_ground:
                    if isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, FlyingEye)):
                        continue
                    ecx = enemy.rect.centerx
                    if pit_x1 <= ecx <= pit_x2:
                        pit_cx = (pit_x1 + pit_x2) // 2
                        enemy.dead       = True
                        enemy._die_timer = 36
                        enemy._die_vx    = 2.5 if pit_cx > ecx else -2.5
                        enemy._die_vy    = 3.0   # fall downward
                        self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                        scr_x = ecx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery,
                                    enemy.death_color)

        # --- Lava: enemy avoidance + typed damage ---
        # Heavy, Healer, and FlyingEye are immune; others take slow damage and avoid the edge
        _LAVA_IMMUNE = (Heavy, Healer, FlyingEye)
        for lx1, lx2 in self.level.lava:
            for enemy in self.enemies:
                if enemy.dead:
                    continue
                if isinstance(enemy, _LAVA_IMMUNE):
                    continue  # immune — walk right through
                ecx = enemy.rect.centerx
                # Smart avoidance: stop 12px before the lava edge
                if enemy.on_ground and not isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)):
                    if enemy.vx > 0 and lx1 - 12 < ecx < lx1 + 8:
                        enemy.vx = 0.0  # halt before left edge
                    elif enemy.vx < 0 and lx2 - 8 < ecx < lx2 + 12:
                        enemy.vx = 0.0  # halt before right edge

                if enemy.on_ground and lx1 <= ecx <= lx2:
                    # Slow tick damage (1 HP every 30 frames per enemy)
                    eid = id(enemy)
                    self._lava_timers[eid] = self._lava_timers.get(eid, 0) + 1
                    if self._lava_timers[eid] >= 30:
                        self._lava_timers[eid] = 0
                        enemy.hp = max(0, enemy.hp - 1)
                        if enemy.hp == 0:
                            enemy.dead       = True
                            enemy._die_timer = 36
                            enemy._die_vx    = 0.0
                            enemy._die_vy    = -4.0
                            self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                            scr_x = ecx - int(self.camera_x)
                            spawn_death(self.particles, scr_x, enemy.rect.centery,
                                        enemy.death_color)
                else:
                    self._lava_timers.pop(id(enemy), None)

        # --- Lava damage to players ---
        for i, player in enumerate(self.players):
            if player.dead or player.out_of_lives:
                continue
            pcx = int(player.x) + P_W // 2
            in_lava = player.on_ground and any(lx1 <= pcx <= lx2 for lx1, lx2 in self.level.lava)
            if in_lava:
                self._lava_timers[i] = self._lava_timers.get(i, 0) + 1
                if self._lava_timers[i] >= LAVA_INTERVAL:
                    self._lava_timers[i] = 0
                    player.hp = max(0, player.hp - LAVA_DMG)
                    self._shake = max(self._shake, 2.0)
                    if player.hp == 0 and not player.dead:
                        player._die()
            else:
                self._lava_timers[i] = 0

        # --- Tsunami damage to players (Level 3) ---
        if self.current_level == 3 and getattr(self.level, 'tsunami_active', False):
            tsw = self.level.tsunami_world_x
            for i, player in enumerate(self.players):
                if player.dead or player.out_of_lives:
                    continue
                if player.x < tsw:
                    self._tsunami_timers[i] = self._tsunami_timers.get(i, 0) + 1
                    if self._tsunami_timers[i] >= TSUNAMI_INTERVAL:
                        self._tsunami_timers[i] = 0
                        player.hp = max(0, player.hp - TSUNAMI_DMG)
                        self._shake = max(self._shake, 3.0)
                        if player.hp == 0 and not player.dead:
                            player._die()
                else:
                    self._tsunami_timers[i] = 0

        # --- Healer ally healing ---
        for enemy in self.enemies:
            if not enemy.dead and hasattr(enemy, '_heal_cd') and enemy._heal_cd == 0:
                for target in self.enemies:
                    if (target is not enemy and not target.dead and
                            target.hp < target.max_hp and
                            abs(target.rect.centerx - enemy.rect.centerx) < 300):
                        target.hp = min(target.max_hp, target.hp + HL_HEAL_AMT)
                        enemy._heal_cd = HL_HEAL_CD
                        mid_x = (target.rect.centerx + enemy.rect.centerx) // 2 - int(self.camera_x)
                        mid_y = min(target.rect.centery, enemy.rect.centery)
                        spawn_heal(self.particles, mid_x, mid_y)
                        break

        # --- Twin assists (Nitay magic) ---
        for ta in self._twin_assists:
            ta[0] += P_TWIN_SPEED * ta[1]
            ta[2] -= 1
            ta_rect = pygame.Rect(int(ta[0]) - 20, GROUND_Y - P_H - 5, 40, P_H + 10)
            for enemy in self.enemies:
                if enemy not in ta[3] and not enemy.dead:
                    if ta_rect.colliderect(enemy.rect):
                        ta[3].add(enemy)
                        if enemy.take_damage(P_TWIN_DMG, int(ta[1]), 30):
                            scr_x = enemy.rect.centerx - int(self.camera_x)
                            spawn_hit(self.particles, scr_x, enemy.rect.centery)
                            if enemy.dead:
                                self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                                spawn_death(self.particles, scr_x, enemy.rect.centery,
                                            enemy.death_color)
        self._twin_assists = [ta for ta in self._twin_assists if ta[2] > 0]
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        # --- Destructible props ---
        for player in self.players:
            if player.dead or player.out_of_lives:
                continue
            atk_p = player.atk_rect
            if not atk_p:
                continue
            for prop in self._props:
                if not prop.alive:
                    continue
                if atk_p.colliderect(prop.rect):
                    if prop.hit():
                        scr_x = int(prop.wx) - int(self.camera_x) + prop.W // 2
                        spawn_hit(self.particles, scr_x, GROUND_Y - prop.H // 2)
                        if random.random() < PROP_DROP_CHANCE:
                            kind = random.choice(['milk', 'crystal'])
                            self.pickups.append(Pickup(prop.wx, kind))
        self._props = [p for p in self._props if p.update()]

        # --- Falling crystal boxes ---
        self._fall_box_cd -= 1
        if self._fall_box_cd <= 0:
            self._fall_box_cd = random.randint(FBOX_CD_MIN, FBOX_CD_MAX)
            cam_x_now = int(self.camera_x)
            wx = cam_x_now + random.randint(60, SCREEN_W - 60)
            wx = max(50, min(wx, WORLD_W - 50))
            self._fall_boxes.append(FallingBox(wx))

        collected_boxes = []
        for fb in self._fall_boxes:
            if not fb.alive:
                continue
            # Walk-over collection
            for player in self.players:
                if player.dead or player.out_of_lives:
                    continue
                if fb.rect.colliderect(pygame.Rect(int(player.x), int(player.y), P_W, P_H)):
                    if fb.collect():
                        collected_boxes.append((player, fb))
                    break
            # Sword-hit collection (player swing rect)
            if fb.alive:
                for player in self.players:
                    atk_r = player.atk_rect
                    if atk_r and atk_r.colliderect(fb.rect):
                        if fb.collect():
                            collected_boxes.append((player, fb))
                        break

        for player, fb in collected_boxes:
            player.crystals += FBOX_CRYSTALS
            scr_x = fb.rect.centerx - int(self.camera_x)
            scr_y = fb.rect.top - 8
            self._float_texts.append([scr_x, scr_y,
                                       f'+{FBOX_CRYSTALS} crystals!', (160, 230, 255), 70])
            self._add_glow(scr_x, scr_y + 20, 32, (140, 230, 255), 18)
            sfx.play('crystal', 0.8)

        self._fall_boxes = [fb for fb in self._fall_boxes if fb.update()]

        # --- Hazard zones (persistent cycling floor hazards) ---
        if self._hz_zones:
            self._hz_timer += 1
            phase = self._hz_timer % HAZARD_ZONE_CYCLE
            hz_active  = HAZARD_ZONE_WARN <= phase < HAZARD_ZONE_WARN + HAZARD_ZONE_ACTIVE
            hz_warning = phase < HAZARD_ZONE_WARN
            for i, player in enumerate(self.players):
                if player.dead or player.out_of_lives:
                    self._hz_dmg_timers.pop(i, None)
                    continue
                pcx = int(player.x) + P_W // 2
                in_hz = player.on_ground and any(
                    x1 <= pcx <= x2 for x1, x2, _ in self._hz_zones
                )
                if in_hz and hz_active:
                    self._hz_dmg_timers[i] = self._hz_dmg_timers.get(i, 0) + 1
                    if self._hz_dmg_timers[i] >= HAZARD_ZONE_TICK:
                        self._hz_dmg_timers[i] = 0
                        player.hp = max(0, player.hp - HAZARD_ZONE_DMG)
                        self._shake = max(self._shake, 2.0)
                        if player.hp == 0 and not player.dead:
                            player._die()
                        pid = player.player_id - 1
                        if pid < len(self._stats):
                            self._stats[pid]['dmg_taken'] += HAZARD_ZONE_DMG
                            self._hit_streak[pid] = 0
                else:
                    self._hz_dmg_timers.pop(i, None)

        # --- Pickups ---
        for pickup in self.pickups:
            for player in self.players:
                if player.dead or player.out_of_lives:
                    continue
                label = pickup.try_collect(player)
                if label:
                    scr_x = int(player.x) - int(self.camera_x) + 19
                    scr_y = int(player.y) - 20
                    col   = (80, 220, 255) if 'Crystal' in label else (255, 220, 80) if 'Woof' in label else (80, 220, 80)
                    self._float_texts.append([scr_x, scr_y, label, col, 50])
                    self._add_glow(scr_x, scr_y + 10, 28, col, 16)

        # --- Falling hazards (level 2+ during boss fight) ---
        if self.current_level >= 2 and self.level.boss_triggered:
            self._hazard_cd -= 1
            if self._hazard_cd <= 0:
                self._hazard_cd = random.randint(FALL_HAZARD_MIN_CD, FALL_HAZARD_MAX_CD)
                # Spawn above a living player's area
                living = [p for p in self.players if not p.out_of_lives and not p.dead]
                if living:
                    tx = random.choice(living)
                    wx = int(tx.x) + random.randint(-120, 120)
                    wx = max(50, min(wx, WORLD_W - 50))
                    self._hazards.append([wx, -30.0, 0.0,
                                          FALL_HAZARD_WARN, random.randint(0, 2), False])

            hit_players = set()
            for hz in self._hazards:
                hz[3] -= 1   # warn_t countdown
                if hz[3] <= 0:
                    hz[1] += FALL_HAZARD_SPEED   # constant fall velocity
                    if hz[1] >= GROUND_Y - 20 and not hz[5]:
                        hz[5] = True   # damage applied once at ground level
                        for player in self.players:
                            if player.dead or player.out_of_lives:
                                continue
                            if abs(player.x + P_W // 2 - hz[0]) < 30:
                                if player not in hit_players:
                                    hit_players.add(player)
                                    if player.take_damage(FALL_HAZARD_DMG):
                                        self._shake = max(self._shake, 4.0)
                                        fh_pid = player.player_id - 1
                                        if fh_pid < len(self._stats):
                                            self._stats[fh_pid]['dmg_taken'] += FALL_HAZARD_DMG
                                            self._hit_streak[fh_pid] = 0
            self._hazards = [hz for hz in self._hazards if hz[1] < SCREEN_H + 60]

        # --- Particles ---
        self.particles = [p for p in self.particles if p.update()]

        # --- Glow decay ---
        for gw in self._glows:
            gw[6] -= 1
        self._glows = [gw for gw in self._glows if gw[6] > 0]

        # --- Decay ---
        self._shake       = max(0.0, self._shake - 0.4)
        if self._magic_flash > 0: self._magic_flash -= 1
        for ft in self._float_texts:
            ft[1] -= 1   # float upward
            ft[4] -= 1   # tick down lifetime
        self._float_texts = [ft for ft in self._float_texts if ft[4] > 0]

        # --- Level countdown timer ---
        if self._victory_wait == 0 and any(not p.out_of_lives for p in self.players):
            self._level_timer_frames -= 1
            if self._level_timer_frames <= 0:
                self._level_timer_frames = 0
                self.state = GAME_OVER

        # --- Win/Lose ---
        boss_dead = self.level.boss_triggered and not any(
            isinstance(e, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)) and not e.dead
            for e in self.enemies
        )
        if boss_dead:
            self._victory_wait += 1
            if self._victory_wait > 100:
                if self.score > self.hiscore:
                    self.hiscore = self.score
                    _save_hiscore(self.hiscore)
                if self.current_level >= 5:
                    _unlock_yael()               # beat all 5 levels!
                self._calc_level_stars()
                self.state = LEVEL_END

        all_out = all(p.out_of_lives for p in self.players)
        if all_out:
            self.state = GAME_OVER

    # ------------------------------------------------------------------ stars / combo
    def _calc_level_stars(self):
        total_dmg    = sum(s['dmg_taken'] for s in self._stats)
        total_max_hp = sum(p.max_hp for p in self.players)
        dmg_frac     = total_dmg / max(1, total_max_hp)

        if dmg_frac < STAR_3_DMG_FRAC:
            self._level_stars = 3
        elif dmg_frac < STAR_2_DMG_FRAC:
            self._level_stars = 2
        else:
            self._level_stars = 1

        if self._level_timer_frames > TIME_STAR_THRESHOLD * FPS:
            self._level_stars = min(3, self._level_stars + 1)

        self._pending_bonus_lives = 0
        _min_hp = min((p.hp for p in self.players if not p.out_of_lives), default=0)
        if self._level_stars == 3:
            self._pending_bonus_lives += 1          # 3-star performance reward
        if _min_hp >= 3:
            self._pending_bonus_lives += 1          # finish with 3+ hearts reward

    def _award_combo_life(self, player, pid):
        if player.lives < PLAYER_LIVES_MAX:
            player.lives = min(PLAYER_LIVES_MAX, player.lives + 1)
            scr_x = int(player.x) - int(self.camera_x) + P_W // 2
            scr_y = int(player.y) - 35
            self._float_texts.append([scr_x, scr_y, 'x20 COMBO  +1 LIFE!', (80, 255, 80), 100])
            sfx.play('respawn', 0.8)
        self._hit_streak[pid] = 0

    # ------------------------------------------------------------------ magic
    def _do_magic(self, caster):
        pid = caster.player_id - 1
        if pid < len(self._stats):
            self._stats[pid]['specials'] += 1
        char = getattr(caster, 'char_name', '')
        if   char == 'lotem': self._magic_lotem(caster)
        elif char == 'gal':   self._magic_gal(caster)
        elif char == 'nitay': self._magic_nitay(caster)
        else:                 self._magic_asaf(caster)
        self._shake       = 12.0
        self._magic_flash = 18
        sfx.play('magic', 0.8)

        # Record this player's magic frame and check for buddy sync
        if len(self.players) == 2 and pid < 2:
            self._magic_frame[pid] = self._frame_t
            other_pid = 1 - pid
            other_frame = self._magic_frame[other_pid]
            if (self._buddy_cd == 0 and
                    self._frame_t - other_frame <= BUDDY_SYNC_WINDOW and
                    other_frame > 0):
                other_player = self.players[other_pid]
                dist = abs(int(caster.x) - int(other_player.x))
                if dist <= BUDDY_SYNC_DIST:
                    self._magic_buddy()

    def _magic_buddy(self):
        """Team Blast — triggered when both players cast magic within sync window."""
        cam = int(self.camera_x)
        for enemy in self.enemies:
            if not enemy.dead:
                kb_dir = 1 if enemy.rect.centerx >= SCREEN_W // 2 + cam else -1
                if enemy.take_damage(BUDDY_BLAST_DMG, kb_dir, BUDDY_BLAST_STUN):
                    if enemy.dead:
                        self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                        scr_x = enemy.rect.centerx - cam
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        for player in self.players:
            if not player.dead and not player.out_of_lives:
                player.hurt_timer = max(player.hurt_timer, BUDDY_INVINC)

        self._float_texts.append([SCREEN_W // 2, SCREEN_H // 3,
                                   'TEAM BLAST!', (255, 255, 80), 100])
        self._add_glow(SCREEN_W // 2, SCREEN_H // 2, 190, (60, 220, 255), 40)
        self._buddy_cd    = BUDDY_CD
        self._magic_frame = [-999, -999]
        self._shake       = max(self._shake, 18.0)
        self._magic_flash = max(self._magic_flash, 30)
        sfx.play('magic', 1.0)

    def _magic_asaf(self, caster):
        """Power Slam — wide shockwave in all directions."""
        cx = int(caster.x) + P_W // 2
        cy = int(caster.y) + P_H // 2
        for enemy in self.enemies:
            if abs(enemy.rect.centerx - cx) < P_MAGIC_RAD_ASAF:
                kb_dir = 1 if enemy.rect.centerx >= cx else -1
                if enemy.take_damage(P_MAGIC_DMG_ASAF, kb_dir, 0):
                    if enemy.dead:
                        self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                        scr_x = enemy.rect.centerx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        spawn_magic(self.particles, cx - int(self.camera_x), cy, P_MAGIC_RAD_ASAF)
        self._add_glow(cx - int(self.camera_x), cy, 60, (255, 110, 20), 24)

    def _magic_lotem(self, caster):
        """Pee Stream — forward cone that stuns enemies."""
        cx = int(caster.x) + P_W // 2
        cy = int(caster.y) + P_H // 2
        for enemy in self.enemies:
            dx = enemy.rect.centerx - cx
            in_front = (caster.facing == 1 and dx > 0) or (caster.facing == -1 and dx < 0)
            if in_front and abs(dx) <= P_PEE_RANGE and abs(enemy.rect.centery - cy) < 45:
                if enemy.take_damage(P_PEE_DMG, caster.facing, P_PEE_STUN):
                    if enemy.dead:
                        self.score += enemy.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                        scr_x = enemy.rect.centerx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        spawn_pee(self.particles, cx - int(self.camera_x), cy, caster.facing)
        self._add_glow(cx - int(self.camera_x), cy, 45, (180, 255, 50), 18)

    def _magic_gal(self, caster):
        """Chain Lightning — zaps up to 5 enemies, bolt jumps to the nearest next."""
        cam = int(self.camera_x)
        cx  = int(caster.x) + P_W // 2
        cy  = int(caster.y) + P_H // 2

        # Build chain: start at caster, greedily pick nearest un-hit enemy
        remaining = [e for e in self.enemies if not e.dead]
        chain_world  = [(cx, cy)]          # world-space positions for distance calc
        chain_screen = [(cx - cam, cy)]    # screen-space for drawing

        prev_x, prev_y = cx, cy
        for _ in range(P_CHAIN_MAX):
            if not remaining:
                break
            # Nearest enemy within range of previous node
            candidates = [
                e for e in remaining
                if math.hypot(e.rect.centerx - prev_x, e.rect.centery - prev_y) <= P_CHAIN_RANGE
            ]
            if not candidates:
                break
            target = min(candidates, key=lambda e: math.hypot(
                e.rect.centerx - prev_x, e.rect.centery - prev_y))
            remaining.remove(target)

            kb_dir = 1 if target.rect.centerx >= cx else -1
            if target.take_damage(P_CHAIN_DMG, kb_dir, 20):
                if target.dead:
                    self.score += target.score_value * (BERSERK_SCORE_MULT if self.berserk_mode else 1)
                    scr_x = target.rect.centerx - cam
                    spawn_death(self.particles, scr_x, target.rect.centery, target.death_color)

            prev_x, prev_y = target.rect.centerx, target.rect.centery
            chain_world.append((prev_x, prev_y))
            chain_screen.append((prev_x - cam, prev_y))

        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        if len(chain_screen) > 1:
            spawn_lightning_chain(self.particles, chain_screen)
            for _csx, _csy in chain_screen:
                self._add_glow(_csx, _csy, 26, (80, 200, 255), 16)

    def _magic_nitay(self, caster):
        """Twin Assist — ghost Gal flies across the screen dealing damage."""
        direction = float(caster.facing)
        if caster.facing == 1:
            start_wx = float(int(self.camera_x) - 60)
        else:
            start_wx = float(int(self.camera_x) + SCREEN_W + 60)
        self._twin_assists.append([start_wx, direction, 80, set()])
        spawn_magic(self.particles,
                    int(caster.x) + P_W // 2 - int(self.camera_x),
                    int(caster.y) + P_H // 2,
                    60)
        self._add_glow(int(caster.x) + P_W // 2 - int(self.camera_x),
                       int(caster.y) + P_H // 2, 50, (200, 80, 255), 20)

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill((0, 0, 0))  # clear first — prevents ghost pixels in fullscreen
        shake_ox = random.randint(-int(self._shake), int(self._shake)) if self._shake > 1 else 0
        shake_oy = random.randint(-int(self._shake), int(self._shake)) if self._shake > 1 else 0
        cam_x = int(self.camera_x) + shake_ox

        if self.state == MENU:
            self._draw_menu()
        elif self.state == COLOR_SELECT:
            self._draw_color_select()
        elif self.state == CREDITS:
            self._draw_credits()
        else:
            self._draw_world(cam_x)
            if self.state == GAME_OVER:
                self._draw_game_over()
            elif self.state in (VICTORY, LEVEL_END):
                self._draw_level_end()
        pygame.display.flip()

    def _draw_world(self, cam_x):
        self.level.draw_background(self.screen, int(self.camera_x))

        for pickup in self.pickups:
            pickup.draw(self.screen, cam_x)

        for p in self.particles:
            p.draw(self.screen, 0)   # particles already in screen-space

        # Character foot shadows (drawn before entities so they appear beneath)
        for _e in self.enemies:
            if not _e.dead:
                _esx = int(_e.x) + _e.W // 2 - cam_x
                if -40 <= _esx <= SCREEN_W + 40:
                    _esw = max(10, int(_e.W * 0.82))
                    if _esw not in self._esh_surfs:
                        _s = pygame.Surface((_esw, 7), pygame.SRCALPHA)
                        pygame.draw.ellipse(_s, (0, 0, 0, 50), (0, 0, _esw, 7))
                        self._esh_surfs[_esw] = _s
                    self.screen.blit(self._esh_surfs[_esw], (_esx - _esw // 2, GROUND_Y - 5))

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        # Enemy hit-flash white overlay
        for _e in self.enemies:
            _hf = getattr(_e, '_hit_flash', 0)
            if _hf > 0 and not (_e.dead and not getattr(_e, '_die_timer', 0)):
                _esx = int(_e.x) - cam_x
                _a = min(220, int(240 * _hf / 5))
                _efl_key = (_e.W, _e.H)
                if _efl_key not in self._efl_surfs:
                    self._efl_surfs[_efl_key] = pygame.Surface(_efl_key, pygame.SRCALPHA)
                _efl = self._efl_surfs[_efl_key]
                _efl.fill((255, 255, 255, _a))
                self.screen.blit(_efl, (_esx, int(_e.y)))

        for rocket in self.rockets:
            rocket.draw(self.screen, cam_x)

        for block in self.blocks:
            block.draw(self.screen, cam_x)

        # Twin assists (Nitay magic) — ghost Gal sprinting across the screen
        for ta in self._twin_assists:
            scr_x = int(ta[0]) - cam_x
            if -80 <= scr_x <= SCREEN_W + 80:
                t_norm = 1.0 - ta[2] / 80.0
                edge_fade = 1.0 - abs(t_norm - 0.5) * 2.0
                base_alpha = max(40, int(180 * edge_fade))

                # Animated Gal sprite, tinted electric-purple
                anim_tick = (80 - ta[2]) // 6
                flip_sprite = ta[1] < 0
                ghost = sprites.get_frame('gal', 'run', anim_tick, P_H, flip_sprite)
                if ghost is not None:
                    ghost = ghost.copy()
                    # Purple-electric tint: keep blues, cut green, boost red a bit
                    ghost.fill((210, 80, 255), special_flags=pygame.BLEND_RGB_MULT)
                    ghost.set_alpha(base_alpha)
                    self.screen.blit(ghost, (scr_x - ghost.get_width() // 2, GROUND_Y - P_H))

                # Small purple glow on the ground
                sw, sh = 50, 10
                shad = pygame.Surface((sw, sh), pygame.SRCALPHA)
                pygame.draw.ellipse(shad, (180, 60, 255, base_alpha // 2), (0, 0, sw, sh))
                self.screen.blit(shad, (scr_x - sw // 2, GROUND_Y + 2))

        # Falling hazards
        for hz in self._hazards:
            sx = hz[0] - cam_x
            if not (-40 <= sx <= SCREEN_W + 40):
                continue
            ht = hz[4]  # type: 0=bag, 1=broccoli, 2=clothing
            if hz[3] > 0:
                # Shadow warning on ground
                warn_alpha = int(180 * (1 - hz[3] / FALL_HAZARD_WARN))
                shadow_w   = max(8, int(40 * (1 - hz[3] / FALL_HAZARD_WARN)))
                shad = pygame.Surface((shadow_w, 8), pygame.SRCALPHA)
                shad.fill((0, 0, 0, warn_alpha))
                self.screen.blit(shad, (sx - shadow_w // 2, GROUND_Y - 4))
            else:
                sy = int(hz[1])
                if ht == 0:   # school bag (dark rectangle with straps)
                    pygame.draw.rect(self.screen, (40, 35, 80),  (sx - 14, sy - 20, 28, 22))
                    pygame.draw.rect(self.screen, (60, 55, 100), (sx - 10, sy - 22, 20, 4))
                    pygame.draw.line(self.screen, (40, 35, 80), (sx - 8, sy - 20), (sx - 14, sy + 2), 3)
                    pygame.draw.line(self.screen, (40, 35, 80), (sx + 8, sy - 20), (sx + 14, sy + 2), 3)
                elif ht == 1: # broccoli
                    pygame.draw.rect(self.screen, (60, 140, 30), (sx - 4, sy - 10, 8, 16))
                    pygame.draw.circle(self.screen, (40, 120, 20), (sx, sy - 14), 12)
                    pygame.draw.circle(self.screen, (60, 150, 35), (sx - 6, sy - 12), 7)
                    pygame.draw.circle(self.screen, (60, 150, 35), (sx + 6, sy - 12), 7)
                else:         # clothing (floppy shirt)
                    pts = [(sx - 14, sy - 14), (sx + 14, sy - 14),
                           (sx + 18, sy + 6),  (sx - 18, sy + 6)]
                    pygame.draw.polygon(self.screen, (180, 80, 80), pts)
                    pygame.draw.rect(self.screen, (200, 100, 100), (sx - 12, sy - 14, 24, 5))

        # --- Hazard zones ---
        if self._hz_zones:
            phase    = self._hz_timer % HAZARD_ZONE_CYCLE
            hz_act   = HAZARD_ZONE_WARN <= phase < HAZARD_ZONE_WARN + HAZARD_ZONE_ACTIVE
            hz_warn  = phase < HAZARD_ZONE_WARN
            # Colour by kind
            _HZ_COLS = {
                'acid':     (40,  200, 60),
                'electric': (240, 220, 40),
                'vent':     (255, 140, 20),
                'slime':    (220, 80,  220),
            }
            for x1, x2, kind in self._hz_zones:
                sx1 = x1 - cam_x
                sx2 = x2 - cam_x
                if sx2 < -10 or sx1 > SCREEN_W + 10:
                    continue
                col = _HZ_COLS.get(kind, (200, 200, 200))
                if hz_act:
                    # Solid active glow strip on the ground
                    strip_w = max(1, min(sx2 - sx1, SCREEN_W))
                    self._hz_strip10.fill(col)
                    self._hz_strip10.set_alpha(160)
                    self.screen.blit(self._hz_strip10, (sx1, GROUND_Y - 4), (0, 0, strip_w, 10))
                    # Animated sparks / spikes
                    t = pygame.time.get_ticks()
                    for xi in range(sx1 + 4, sx2, 14):
                        h = 6 + int(4 * math.sin((t * 0.02 + xi * 0.3)))
                        pygame.draw.line(self.screen, col, (xi, GROUND_Y - 4), (xi, GROUND_Y - 4 - h), 2)
                elif hz_warn:
                    # Flicker warning
                    blink = (self._hz_timer // 8) % 2 == 0
                    if blink:
                        strip_w = max(1, min(sx2 - sx1, SCREEN_W))
                        self._hz_strip6.fill(col)
                        self._hz_strip6.set_alpha(80)
                        self.screen.blit(self._hz_strip6, (sx1, GROUND_Y - 4), (0, 0, strip_w, 6))

        # --- Destructible props ---
        for prop in self._props:
            prop.draw(self.screen, cam_x)

        # --- Falling crystal boxes ---
        for fb in self._fall_boxes:
            fb.draw(self.screen, cam_x)

        for player in self.players:
            player.draw(self.screen, cam_x)
            player.draw_respawn_countdown(self.screen, cam_x)

        # Damage red flash
        _max_phf = max((p._hit_flash for p in self.players), default=0)
        if _max_phf > 0:
            self._red_flash_surf.set_alpha(int(72 * _max_phf / 8))
            self.screen.blit(self._red_flash_surf, (0, 0))

        if self._magic_flash > 0:
            alpha = int(110 * self._magic_flash / 18)
            self._magic_flash_surf.fill((50, 80, 220, alpha))
            self.screen.blit(self._magic_flash_surf, (0, 0))

        if self._light_layer:
            self._light_layer.render(self.screen, self._get_lights())

        self._draw_glows()

        # Death shockwave expanding rings
        _live_sw = []
        for sw in self._shockwaves:
            sw[3] -= 1
            if sw[3] <= 0:
                continue
            t     = 1.0 - sw[3] / 18
            r     = max(2, int(80 * t))
            a     = int(220 * (1.0 - t))
            thick = max(1, 4 - int(t * 3))
            scr_x = sw[0] - cam_x
            self._sw_surf.fill((0, 0, 0, 0))
            pygame.draw.circle(self._sw_surf, (*sw[2][:3], a), (84, 84), r, thick)
            self.screen.blit(self._sw_surf, (scr_x - 84, sw[1] - 84))
            _live_sw.append(sw)
        self._shockwaves = _live_sw

        self.level.draw_color_grade(self.screen)
        self.screen.blit(self._vignette, (0, 0))

        # --- Tsunami HUD warning (Level 3) ---
        if self.current_level == 3:
            lv = self.level
            if not lv.tsunami_active and lv._tsunami_delay <= 240:
                # Countdown warning before the wave starts
                frames_left = lv._tsunami_delay
                secs = math.ceil(frames_left / 60)
                blink = (lv._tsunami_delay // 15) % 2 == 0
                if blink:
                    warn = self.font_gameover.render(f'TSUNAMI IN {secs}s!', True, (255, 80, 40))
                    self.screen.blit(warn, warn.get_rect(center=(SCREEN_W // 2, 80)))
            elif lv.tsunami_active:
                # Show a small "WAVE" danger tag at the left side of screen
                sx = int(lv.tsunami_world_x - self.camera_x)
                if 0 < sx < SCREEN_W:
                    blink2 = (int(lv.tsunami_world_x) // 12) % 2 == 0
                    if blink2:
                        tag = self.font_float.render('WAVE ►', True, (100, 200, 255))
                        self.screen.blit(tag, (max(0, sx - 50), SCREEN_H // 2 - 10))

        ui.draw_hud(self.screen, self.players, self.score, self.enemies)

        # --- Level countdown timer (surfaces cached — only re-render when text/colour changes) ---
        _tsecs = self._level_timer_frames // FPS
        if _tsecs <= 10:
            _tcol = (255, 50, 30) if (self._level_timer_frames // 15) % 2 == 0 else (255, 160, 30)
        elif _tsecs <= 30:
            _tcol = (255, 160, 30)
        else:
            _tcol = (230, 230, 100)
        _cache_key = (_tsecs, _tcol)
        if self._timer_surf_cache is None or self._timer_surf_cache[0] != _cache_key:
            _tsurf = self.font_small.render(f'TIME  {_tsecs}', True, _tcol)
            _tshad = self.font_small.render(f'TIME  {_tsecs}', True, (0, 0, 0))
            self._timer_surf_cache = (_cache_key, _tsurf, _tshad)
        _, _tsurf, _tshad = self._timer_surf_cache
        _tr = _tsurf.get_rect(centerx=SCREEN_W // 2, top=36)
        self.screen.blit(_tshad, (_tr.x + 1, _tr.y + 1))
        self.screen.blit(_tsurf, _tr)

        # --- Hit streak counter above each player ---
        for i, player in enumerate(self.players):
            if player.dead or player.out_of_lives:
                continue
            if i < len(self._hit_streak) and self._hit_streak[i] >= 5:
                streak = self._hit_streak[i]
                col = (255, 80, 0) if streak >= 15 else (255, 180, 0)
                s_surf = self.font_med.render(f'{streak}x', True, col)
                sx = int(player.x) - cam_x + P_W // 2
                sy = int(player.y) - 48
                self.screen.blit(s_surf, s_surf.get_rect(center=(sx, sy)))

        # --- Berserk mode border + label ---
        if self.berserk_mode:
            self.screen.blit(self._berserk_brd_surf, (0, 0))
            self.screen.blit(self._berserk_lbl, (SCREEN_W - self._berserk_lbl.get_width() - 8, 6))

        # --- Team Blast indicator (2-player only) ---
        if self.num_players == 2:
            if self._buddy_cd == 0:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
                col = (int(200 + 55 * pulse), int(200 + 55 * pulse), 60)
                tbl = self.font_float.render('TEAM BLAST READY  [use magic together]', True, col)
                self.screen.blit(tbl, (SCREEN_W // 2 - tbl.get_width() // 2, SCREEN_H - 24))
            else:
                frac = 1.0 - self._buddy_cd / BUDDY_CD
                bar_w = int(160 * frac)
                pygame.draw.rect(self.screen, (60, 60, 100), (SCREEN_W // 2 - 80, SCREEN_H - 18, 160, 8))
                pygame.draw.rect(self.screen, (140, 140, 255), (SCREEN_W // 2 - 80, SCREEN_H - 18, bar_w, 8))

        self._vpad.draw(self.screen)

        for fx, fy, text, col, life in self._float_texts:
            max_life = 110 if text.startswith('!!') else 55
            alpha = max(0, int(255 * life / max_life))
            _ft_key = (text, col)
            if _ft_key not in self._float_text_cache:
                font = self.font_big if text.startswith('!!') else self.font_float
                self._float_text_cache[_ft_key] = font.render(text, True, col)
            surf = self._float_text_cache[_ft_key]
            surf.set_alpha(alpha)
            self.screen.blit(surf, (fx - surf.get_width() // 2, fy))

    # ------------------------------------------------------------------ level end
    def _draw_star(self, cx, cy, r, color):
        pts = []
        for i in range(5):
            oa = math.radians(-90 + i * 72)
            ia = math.radians(-90 + i * 72 + 36)
            pts.append((cx + r * math.cos(oa), cy + r * math.sin(oa)))
            pts.append((cx + r * 0.42 * math.cos(ia), cy + r * 0.42 * math.sin(ia)))
        pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.polygon(self.screen, (0, 0, 0), pts, 1)

    def _draw_level_end(self):
        # Dark overlay over the game world
        self.screen.blit(self._level_ov_surf, (0, 0))

        # ---- Title ----
        if self.current_level >= 5:
            title_text = 'GAME COMPLETE!'
            title_col  = (100, 255, 100)
        else:
            title_text = f'LEVEL {self.current_level} COMPLETE!'
            title_col  = SCORE_COL
        title_surf = self.font_big.render(title_text, True, title_col)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_W // 2, 52)))

        # ---- Stars ----
        STAR_R = 28
        star_y = 105
        star_xs = [SCREEN_W // 2 - 70, SCREEN_W // 2, SCREEN_W // 2 + 70]
        gold   = (255, 210, 0)
        empty  = (55, 55, 55)
        for i, sx in enumerate(star_xs):
            col = gold if i < self._level_stars else empty
            self._draw_star(sx, star_y, STAR_R, col)

        # ---- Bonus lives text ----
        bonus_y = 150
        if self._pending_bonus_lives > 0:
            hearts = '+' + ('♥' * self._pending_bonus_lives)
            msg = f'{hearts}  for next level!'
            b_surf = self.font_med.render(msg, True, (90, 255, 90))
            self.screen.blit(b_surf, b_surf.get_rect(center=(SCREEN_W // 2, bonus_y)))

        # ---- Hi-score line ----
        hi_col = (255, 80, 80) if self.score >= self.hiscore else (180, 180, 180)
        hi_txt = 'NEW HI-SCORE!' if self.score >= self.hiscore else f'Hi: {self.hiscore:,}'
        hi_surf = self.font_small.render(f'Score: {self.score:,}   {hi_txt}', True, hi_col)
        self.screen.blit(hi_surf, hi_surf.get_rect(center=(SCREEN_W // 2, 178)))

        # ---- Per-player stats table ----
        num_p      = len(self.players)
        row_h      = 30
        tbl_top    = 215
        _STAT_ROWS = [
            ('Enemies killed', 'kills'),
            ('Dmg dealt',      'dmg_dealt'),
            ('Dmg taken',      'dmg_taken'),
            ('Specials used',  'specials'),
            ('Best streak',    'peak_streak'),
        ]

        # Fixed label column on the left; value columns share the remaining width
        label_right = 230
        val_zone    = SCREEN_W - label_right
        val_xs      = [label_right + (i + 1) * val_zone // (num_p + 1)
                       for i in range(num_p)]

        for pi, player in enumerate(self.players):
            char = player.char_name or f'P{player.player_id}'
            hdr  = self.font_med.render(char.upper(), True, WHITE)
            self.screen.blit(hdr, hdr.get_rect(center=(val_xs[pi], tbl_top)))

        for ri, (label, key) in enumerate(_STAT_ROWS):
            row_y = tbl_top + row_h * (ri + 1) + 6
            lbl_surf = self.font_small.render(label, True, (180, 180, 180))
            self.screen.blit(lbl_surf, lbl_surf.get_rect(midright=(label_right - 12, row_y)))
            for pi in range(num_p):
                val   = self._stats[pi][key] if pi < len(self._stats) else 0
                vcol  = WHITE if key != 'dmg_taken' else (255, 120, 120)
                v_surf = self.font_small.render(str(val), True, vcol)
                self.screen.blit(v_surf, v_surf.get_rect(center=(val_xs[pi], row_y)))

        # ---- Time remaining row ----
        _t_row_y   = tbl_top + row_h * (len(_STAT_ROWS) + 1) + 6
        _tsecs_end = self._level_timer_frames // FPS
        _tstar     = _tsecs_end > TIME_STAR_THRESHOLD
        _tcol3     = (100, 220, 100) if _tstar else (180, 180, 180)
        _t_lbl     = self.font_small.render('Time left', True, (180, 180, 180))
        self.screen.blit(_t_lbl, _t_lbl.get_rect(midright=(label_right - 12, _t_row_y)))
        _t_tag     = '  ★' if _tstar else ''
        _t_val     = self.font_small.render(f'{_tsecs_end}s{_t_tag}', True, _tcol3)
        _val_cx    = label_right + (SCREEN_W - label_right) // 2
        self.screen.blit(_t_val, _t_val.get_rect(center=(_val_cx, _t_row_y)))

        # ---- Continue prompt ----
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink:
            if self.current_level >= 5:
                prompt = 'Press ENTER to see credits'
            else:
                prompt = f'Press ENTER for Level {self.current_level + 1}'
            p_surf = self.font_small.render(prompt, True, WHITE)
            self.screen.blit(p_surf, p_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H - 32)))

    def _draw_menu(self):
        # Lazy-load and cache the entry screen background
        if not hasattr(self, '_entry_bg'):
            try:
                raw = pygame.image.load(
                    os.path.join(os.path.dirname(__file__), 'images', 'entry_screen.png')
                ).convert()
                self._entry_bg = pygame.transform.scale(raw, (SCREEN_W, SCREEN_H))
            except Exception:
                self._entry_bg = None

        if self._entry_bg:
            self.screen.blit(self._entry_bg, (0, 0))
            # Dark overlay so text stays readable
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(SKY_TOP)
            pygame.draw.rect(self.screen, SKY_BOT,   (0, SCREEN_H // 2, SCREEN_W, SCREEN_H // 2))
            pygame.draw.rect(self.screen, GRASS_COL, (0, SCREEN_H - 75, SCREEN_W, 75))
            pygame.draw.rect(self.screen, GROUND_COL,(0, SCREEN_H - 50, SCREEN_W, 50))

        # Title
        title  = self.font_title.render('The NOYS', True, SCORE_COL)
        shadow = self.font_title.render('The NOYS', True, (70, 55, 0))
        tr = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3))
        self.screen.blit(shadow, (tr.x + 4, tr.y + 4))
        self.screen.blit(title,  tr)

        # Hi-score
        if self.hiscore > 0:
            hi = self.font_small.render(f'Hi-Score: {self.hiscore:,}', True, SCORE_COL)
            self.screen.blit(hi, hi.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3 + 88)))

        # Start options
        opts = [
            'Press  1  for 1 Player',
            'Press  2  for 2 Players Co-op',
            'Press  ENTER  for 1 Player',
        ]
        blink = (pygame.time.get_ticks() // 520) % 2 == 0
        for i, text in enumerate(opts):
            col = WHITE if (i < 2 or blink) else (100, 100, 100)
            t = self.font_small.render(text, True, col)
            self.screen.blit(t, t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20 + i * 28)))

        # Touch buttons (tablet / web)
        cx = SCREEN_W // 2
        btns = {
            'start':   pygame.Rect(cx - 100, 436, 200, 64),
            '2p':      pygame.Rect(cx + 116,  448, 158, 48),
            'berserk': pygame.Rect(cx - 274,  448, 148, 48),
        }
        self._menu_touch_btns = btns
        self._draw_touch_btn(self.screen, btns['start'],   'START',     (35, 155, 55),  self.font_med)
        self._draw_touch_btn(self.screen, btns['2p'],      '2 PLAYERS', (40, 100, 200), self.font_small)
        bk_col = (180, 30, 30) if self.berserk_mode else (70, 70, 70)
        bk_label = 'BERSERK: ON' if self.berserk_mode else 'BERSERK'
        self._draw_touch_btn(self.screen, btns['berserk'], bk_label,    bk_col, self.font_small,
                             active=self.berserk_mode)


    def _draw_color_select(self):
        self.screen.fill(SKY_TOP)
        pygame.draw.rect(self.screen, GROUND_COL, (0, SCREEN_H - 80, SCREEN_W, 80))
        pygame.draw.rect(self.screen, GRASS_COL,  (0, SCREEN_H - 80, SCREEN_W, 14))

        title = self.font_big.render('Choose Your Character', True, SCORE_COL)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 65)))

        lv = getattr(self, '_start_level', 1)
        if lv > 1:
            lv_label = self.font_small.render(f'Starting at Level {lv}', True, (255, 200, 80))
            self.screen.blit(lv_label, lv_label.get_rect(center=(SCREEN_W // 2, 105)))

        opts   = self._COLOR_OPTIONS
        cmap   = self._COLOR_MAP
        num_p  = self.num_players
        cx_arr = getattr(self, '_color_cursor', [0, 0])
        _SPRITE_CHARS = {'asaf', 'lotem', 'gal', 'nitay', 'yael'}
        spr_tick = pygame.time.get_ticks() // (sprites.ANIM_SPEED.get('idle', 12) * 1000 // 60)

        n_opts  = len(opts)
        # Available width per player; derive spacing and circle radius to always fit
        avail_w  = SCREEN_W if num_p == 1 else SCREEN_W // 2
        spacing  = min(90, (avail_w - 60) // n_opts)
        r        = min(30, spacing // 2 - 2)

        ready  = getattr(self, '_p_ready', [False, False])
        p_keys = ['← → then ENTER', 'A  D  then W']

        for pi in range(num_p):
            is_ready = ready[pi]
            col    = (80, 220, 80) if is_ready else WHITE
            status = '  READY!' if is_ready else f'  {p_keys[pi]}'
            label  = f'P{pi + 1}{status}'
            if num_p == 1:
                base_x = SCREEN_W // 2
            else:
                base_x = SCREEN_W // 4 + pi * SCREEN_W // 2
            lbl = self.font_med.render(label, True, col)
            self.screen.blit(lbl, lbl.get_rect(center=(base_x, 130)))

            sel = cx_arr[pi]
            for i, name in enumerate(opts):
                bx = base_x - (n_opts // 2) * spacing + i * spacing + spacing // 2
                by = 220
                is_sel = (i == sel)

                if name in _SPRITE_CHARS and sprites.is_ready():
                    n_frames = sprites.frame_count(name, 'idle')
                    fidx = spr_tick % max(1, n_frames)
                    thumb = sprites.get_frame(name, 'idle', fidx, r * 2)
                    if thumb:
                        tw = thumb.get_width()
                        self.screen.blit(thumb, (bx - tw // 2, by - r))
                    else:
                        body, _, _ = cmap[name]
                        pygame.draw.circle(self.screen, body, (bx, by), r)
                else:
                    body, _, _ = cmap[name]
                    pygame.draw.circle(self.screen, body, (bx, by), r)

                if is_sel:
                    ring_col = (80, 220, 80) if is_ready else WHITE
                    pygame.draw.circle(self.screen, ring_col, (bx, by), r + 5, 3)
                    n_surf = self.font_small.render(name.upper(), True, ring_col)
                    self.screen.blit(n_surf, n_surf.get_rect(center=(bx, by + r + 18)))

        # Touch navigation + ready buttons
        by   = 464
        cx   = SCREEN_W // 2
        rdy  = getattr(self, '_p_ready', [False, False])
        if self.num_players == 1:
            cs_btns = {
                'p1_left':  pygame.Rect(cx - 240, by, 54, 54),
                'p1_right': pygame.Rect(cx + 186, by, 54, 54),
                'p1_ready': pygame.Rect(cx -  88, by, 176, 54),
            }
        else:
            cs_btns = {
                'p1_left':  pygame.Rect( 18, by, 52, 52),
                'p1_right': pygame.Rect( 78, by, 52, 52),
                'p1_ready': pygame.Rect(140, by, 130, 52),
                'p2_left':  pygame.Rect(694, by, 52, 52),
                'p2_right': pygame.Rect(754, by, 52, 52),
                'p2_ready': pygame.Rect(816, by, 140, 52),
            }
        self._cs_touch_btns = cs_btns
        nav_col   = (70, 70, 140)
        self._draw_touch_btn(self.screen, cs_btns['p1_left'],  '<', nav_col, self.font_med)
        self._draw_touch_btn(self.screen, cs_btns['p1_right'], '>', nav_col, self.font_med)
        p1_col = (25, 130, 25) if rdy[0] else (35, 155, 55)
        self._draw_touch_btn(self.screen, cs_btns['p1_ready'],
                             'READY!' if not rdy[0] else 'READY!', p1_col, self.font_med, active=rdy[0])
        if self.num_players == 2:
            self._draw_touch_btn(self.screen, cs_btns['p2_left'],  '<', nav_col, self.font_med)
            self._draw_touch_btn(self.screen, cs_btns['p2_right'], '>', nav_col, self.font_med)
            p2_col = (25, 130, 25) if rdy[1] else (35, 155, 55)
            self._draw_touch_btn(self.screen, cs_btns['p2_ready'],
                                 'P2 READY!' if not rdy[1] else 'P2 READY!',
                                 p2_col, self.font_small, active=rdy[1])

        # Easy mode indicator
        if _is_easy_mode():
            em_surf = self.font_med.render('EASY MODE ON  (F7 to toggle)', True, (80, 255, 120))
        else:
            em_surf = self.font_hint.render('F7 = Easy Mode', True, (160, 160, 160))
        self.screen.blit(em_surf, em_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H - 22)))

    def _draw_credits(self):
        # Lazy-load finish.png background
        if not hasattr(self, '_finish_bg'):
            try:
                _raw = pygame.image.load(
                    os.path.join(os.path.dirname(__file__), 'images', 'finish.png')
                ).convert()
                self._finish_bg = pygame.transform.scale(_raw, (SCREEN_W, SCREEN_H))
            except Exception:
                self._finish_bg = None

        if self._finish_bg:
            self.screen.blit(self._finish_bg, (0, 0))
        else:
            self.screen.fill((8, 5, 18))

        # Dark panels top + bottom so text is legible over the colourful image
        _tp = pygame.Surface((SCREEN_W, 195), pygame.SRCALPHA)
        _tp.fill((0, 0, 0, 178))
        self.screen.blit(_tp, (0, 0))
        _bp = pygame.Surface((SCREEN_W, 215), pygame.SRCALPHA)
        _bp.fill((0, 0, 0, 158))
        self.screen.blit(_bp, (0, SCREEN_H - 215))

        def _txt(font, text, col, cx, cy, shadow_off=3):
            _sh = font.render(text, True, (0, 0, 0))
            _s  = font.render(text, True, col)
            _r  = _s.get_rect(center=(cx, cy))
            self.screen.blit(_sh, (_r.x + shadow_off, _r.y + shadow_off))
            self.screen.blit(_s,  _r)

        # --- Top panel: title + score ---
        _txt(self.font_title, 'YOU WIN!', (255, 235, 55), SCREEN_W // 2, 72, 4)

        hi_new    = self.score >= self.hiscore
        score_col = (255, 215, 50) if hi_new else WHITE
        score_lbl = '★ NEW HI-SCORE! ★' if hi_new else 'Final Score'
        _txt(self.font_med, f'{score_lbl}  {self.score:,}', score_col, SCREEN_W // 2, 138, 2)
        _txt(self.font_small, f'All-time best: {self.hiscore:,}', (210, 210, 210),
             SCREEN_W // 2, 170, 2)

        # --- Bottom panel: credits + prompt ---
        _by = SCREEN_H - 208
        if _is_yael_unlocked():
            _txt(self.font_small, '★ YAEL UNLOCKED! ★', (255, 120, 220), SCREEN_W // 2, _by, 2)
            _by += 28
        _txt(self.font_small,
             'Game: Lotem & Asaf  |  Art: KayKit (CC0)  |  Engine: Python + Pygame',
             (200, 220, 255), SCREEN_W // 2, _by, 2)
        _by += 28
        _txt(self.font_small, 'Thanks for playing The NOYS!', (230, 190, 255),
             SCREEN_W // 2, _by, 2)

        blink = (pygame.time.get_ticks() // 600) % 2 == 0
        if blink:
            _txt(self.font_med, 'Press ENTER to return to Menu', WHITE,
                 SCREEN_W // 2, SCREEN_H - 42, 2)

    def _draw_overlay(self, title, color, subtitle):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        t      = self.font_big.render(title, True, color)
        shadow = self.font_big.render(title, True, BLACK)
        tr = t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 55))
        self.screen.blit(shadow, (tr.x + 3, tr.y + 3))
        self.screen.blit(t, tr)

        s = self.font_med.render(subtitle, True, WHITE)
        self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))

    # Game over screen with random Hebrew/English flavor text
    _GAMEOVER_LINES = [
        ('אמא אמרה שעת שינה',  'Mom said it\'s bedtime.'),
        ('לך לסדר את החדר',              'Go clean your room.'),
        ('יש לך שיעורי בית',        'You have homework!'),
        ('אין קינוח בשבילך',   'No dessert for you!'),
    ]

    def _draw_game_over(self):
        self._draw_overlay('GAME OVER', (210, 45, 45), 'Press ENTER to return to Menu')

        heb, eng = self._GAMEOVER_LINES[self._gameover_line_idx]

        # Try Hebrew first; fall back to English if the font can't render it
        flavor_surf = None
        try:
            flavor_surf = self.font_gameover.render(heb, True, (255, 220, 80))
            # Sanity check: if all glyphs rendered as boxes (width too small), fallback
            if flavor_surf.get_width() < 30:
                raise ValueError('font missing glyphs')
        except Exception:
            flavor_surf = None

        if flavor_surf is None:
            flavor_surf = self.font_med.render(eng, True, (255, 220, 80))

        self.screen.blit(flavor_surf,
                         flavor_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 68)))
