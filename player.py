import math
import pygame
from settings import *
import sfx
import sprites

# ---------------------------------------------------------------------------
# Default key bindings — imported by game.py to construct players
# ---------------------------------------------------------------------------
P1_KEYS = {
    'left':   [pygame.K_LEFT],
    'right':  [pygame.K_RIGHT],
    'jump':   [pygame.K_UP, pygame.K_SPACE],
    'attack': [pygame.K_INSERT],
    'heavy':  [pygame.K_DELETE],
    'magic':  [pygame.K_HOME],
}

# P2 uses WASD movement; Tab/CapsLock/LShift for attacks (no overlap with P1)
P2_KEYS = {
    'left':   [pygame.K_a],
    'right':  [pygame.K_d],
    'jump':   [pygame.K_w],
    'attack': [pygame.K_TAB],
    'heavy':  [pygame.K_CAPSLOCK],
    'magic':  [pygame.K_LSHIFT],
}


_COLOR_PALETTES = {
    'blue':  ((45, 85, 195),  (65, 108, 218),  (28, 50, 155)),
    'red':   ((195, 65, 45),  (218, 90, 65),   (155, 28, 28)),
    'green': ((40, 160, 60),  (65, 195, 85),   (22, 105, 38)),
    'gold':  ((200, 165, 30), (225, 195, 60),  (155, 120, 15)),
    'yael':  (YAEL_BODY,      YAEL_HEAD,       YAEL_CAPE),
}


class Player:
    def __init__(self, x, y, player_id=1, key_bindings=None, joystick=None,
                 color=None, sprite_char=None, _char_name_override=None):
        self.player_id  = player_id
        self.key_bindings = key_bindings or P1_KEYS
        self.joystick   = joystick

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = False

        # char_name = original arg always (for logic); sprite_char = None when sprites not ready
        self.char_name   = _char_name_override or sprite_char or ''
        self.sprite_char = sprite_char if (sprite_char and sprites.is_ready()) else None
        self._anim_t = 0   # tick counter for sprite animation
        self.virtual_input = {k: False for k in ('left','right','jump','attack','heavy','magic')}

        # Nitay hits 15% harder with his fists
        self._atk_dmg_mult = 1.15 if sprite_char == 'nitay' else 1.0
        # Yael: faster but lower max HP
        self._speed_mult   = YAEL_SPEED_MULT if self.char_name == 'yael' else 1.0

        self.hp       = YAEL_HP if self.char_name == 'yael' else P_HP
        self.max_hp   = YAEL_HP if self.char_name == 'yael' else P_HP
        self.magic    = P_MAGIC
        self.max_magic = P_MAGIC

        # Combat
        self.atk_timer        = 0
        self.atk_cd           = 0
        self.magic_cd         = 0
        self.hurt_timer       = 0
        self._hit_flash       = 0
        self._atk_trail       = []
        self.speed_boost_t    = 0
        self.rage_t           = 0
        self.dead             = False
        self.magic_just_used  = False
        self._hit_set         = set()

        # Combo chain
        self.combo_count      = 0   # 0 = first hit, 1 = second, 2 = finisher
        self.combo_window     = 0   # frames left to continue the chain
        self.current_atk_dmg  = P_ATK_DMG
        self.current_atk_w    = P_ATK_W
        self.current_atk_stun = 0
        self.current_atk_dur  = P_ATK_DUR
        self.is_heavy_atk     = False

        # Lives & respawn
        self.lives         = PLAYER_LIVES
        self.out_of_lives  = False
        self.respawn_timer = 0
        self.crystals      = 0

        # Animation
        self._walk_t         = 0
        self._magic_regen_t  = 0
        self._prev_jump      = False  # edge-detect for joystick jump

        # Colour palette — use explicit color arg if given, else default by player_id
        if color is None:
            color = 'blue' if player_id == 1 else 'red'
        if color in _COLOR_PALETTES:
            self._body_col, self._head_col, self._cape_col = _COLOR_PALETTES[color]
        elif self.char_name == 'yael':
            self._body_col, self._head_col, self._cape_col = YAEL_BODY, YAEL_HEAD, YAEL_CAPE
        else:
            self._body_col  = PLAYER_BODY
            self._head_col  = PLAYER_HEAD
            self._cape_col  = CAPE_COL

    # ------------------------------------------------------------------ rects
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), P_W, P_H)

    @property
    def atk_rect(self):
        if self.atk_timer <= 0:
            return None
        w = self.current_atk_w
        ax = int(self.x) + P_W if self.facing == 1 else int(self.x) - w
        return pygame.Rect(ax, int(self.y) + 16, w, P_ATK_H + 6)

    # ------------------------------------------------------------------ input
    def _read_input(self, all_keys):
        state = {a: False for a in ('left', 'right', 'jump', 'attack', 'heavy', 'magic')}

        # Keyboard
        for action, keys_list in self.key_bindings.items():
            for k in keys_list:
                if all_keys[k]:
                    state[action] = True

        # Gamepad
        if self.joystick:
            j = self.joystick
            try:
                ax = j.get_axis(0) if j.get_numaxes() > 0 else 0
                if ax < -0.28: state['left']  = True
                if ax >  0.28: state['right'] = True
                if j.get_numhats() > 0:
                    hx, _ = j.get_hat(0)
                    if hx < 0: state['left']  = True
                    if hx > 0: state['right'] = True
                nb = j.get_numbuttons()
                if nb > 0 and j.get_button(0): state['jump']   = True  # A/Cross
                if nb > 2 and j.get_button(2): state['attack'] = True  # X/Square
                if nb > 1 and j.get_button(1): state['heavy']  = True  # B/Circle
                if nb > 3 and j.get_button(3): state['magic']  = True  # Y/Triangle
            except Exception:
                pass

        # Touch / virtual input overlay
        for action, val in self.virtual_input.items():
            if val:
                state[action] = True

        return state

    def handle_input(self, all_keys):
        if self.out_of_lives or self.dead:
            return

        inp = self._read_input(all_keys)

        if self.hurt_timer > 0:
            self.vx *= 0.75
            return

        # Movement
        speed = P_SPEED * self._speed_mult * (1.6 if self.speed_boost_t > 0 else 1.0)
        self.vx = 0.0
        if inp['left']:
            self.vx = -speed
            self.facing = -1
        if inp['right']:
            self.vx = speed
            self.facing = 1

        self._walk_t = self._walk_t + 1 if self.vx != 0 else 0

        # Jump (edge-detect for joystick so it doesn't multi-jump)
        jump_now = inp['jump']
        if jump_now and not self._prev_jump and self.on_ground:
            self.vy = JUMP_VY
            self.on_ground = False
        self._prev_jump = jump_now

        # Only one attack type can fire per frame; light takes priority for combo chaining
        if self.atk_cd <= 0:
            if inp['attack']:
                self._fire_attack()
            elif inp['heavy']:
                self._fire_heavy_attack()

        # Magic
        if inp['magic'] and self.magic_cd <= 0 and self.magic >= P_MAGIC_COST:
            self.magic -= P_MAGIC_COST
            self.magic_cd = P_MAGIC_CD
            self.magic_just_used = True

    def _fire_attack(self):
        self.is_heavy_atk = False
        # Advance or start combo chain
        if self.combo_window > 0:
            self.combo_count = min(self.combo_count + 1, 2)
        else:
            self.combo_count = 0

        self.combo_window = P_COMBO_WINDOW

        if self.combo_count == 2:                  # ---- FINISHER ----
            self.current_atk_dmg  = int(P_COMBO3_DMG * self._atk_dmg_mult)
            self.current_atk_w    = P_COMBO3_W
            self.current_atk_stun = P_COMBO3_STUN
            self.current_atk_dur  = P_COMBO3_DUR
            self.atk_timer        = P_COMBO3_DUR
            self.atk_cd           = P_ATK_CD + 14
        elif self.combo_count == 1:                # ---- 2nd hit ----
            self.current_atk_dmg  = int(P_COMBO2_DMG * self._atk_dmg_mult)
            self.current_atk_w    = P_ATK_W
            self.current_atk_stun = 0
            self.current_atk_dur  = P_ATK_DUR
            self.atk_timer        = P_ATK_DUR
            self.atk_cd           = P_ATK_CD
        else:                                      # ---- 1st hit ----
            self.current_atk_dmg  = int(P_ATK_DMG * self._atk_dmg_mult)
            self.current_atk_w    = P_ATK_W
            self.current_atk_stun = 0
            self.current_atk_dur  = P_ATK_DUR
            self.atk_timer        = P_ATK_DUR
            self.atk_cd           = P_ATK_CD

        self._hit_set.clear()
        if self.rage_t > 0:
            self.current_atk_dmg = int(self.current_atk_dmg * 2)

    def _fire_heavy_attack(self):
        self.is_heavy_atk     = True
        self.combo_count      = 0
        self.combo_window     = 0
        self.current_atk_dmg  = int(P_HEAVY_DMG * self._atk_dmg_mult)
        self.current_atk_w    = P_HEAVY_W
        self.current_atk_stun = P_COMBO3_STUN
        self.current_atk_dur  = P_HEAVY_DUR
        self.atk_timer        = P_HEAVY_DUR
        self.atk_cd           = P_HEAVY_CD
        if self.rage_t > 0:
            self.current_atk_dmg = int(self.current_atk_dmg * 2)
        self._hit_set.clear()

    # ------------------------------------------------------------------ damage
    def take_damage(self, dmg):
        if self.hurt_timer > 0 or self.dead or self.out_of_lives:
            return False
        self.hp = max(0, self.hp - dmg)
        self._hit_flash = 8
        self.hurt_timer = P_HURT_DUR
        self.vx = -self.facing * 5.0
        self.vy = -4.0
        if self.hp == 0:
            self._die()
        return True

    def _die(self):
        self.dead = True
        self.lives -= 1
        if self.lives > 0:
            self.respawn_timer = RESPAWN_DELAY
        else:
            self.out_of_lives = True

    def _respawn(self, camera_x):
        self.x            = float(max(camera_x + 120, 80))
        self.y            = float(GROUND_Y - P_H)
        self.vx           = 0.0
        self.vy           = 0.0
        self.hp           = P_HP
        self.magic        = P_MAGIC
        self.dead         = False
        self.hurt_timer   = INVINCIBILITY_DUR   # invincibility frames on respawn
        self.atk_timer    = 0
        self.atk_cd       = 0
        self._atk_trail   = []
        self.speed_boost_t = 0
        self.rage_t        = 0
        self.combo_count  = 0
        self.combo_window = 0
        self.is_heavy_atk = False
        self._hit_set.clear()
        sfx.play('respawn', 0.6)

    # ------------------------------------------------------------------ update
    def update(self, camera_x=0, platforms=None, pits=None):
        if self.out_of_lives:
            return

        if self.dead:
            if self.respawn_timer > 0:
                self.respawn_timer -= 1
                if self.respawn_timer == 0:
                    self._respawn(camera_x)
            return

        # Physics
        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy

        cx = self.x + P_W // 2
        in_pit = pits and any(px1 <= cx <= px2 for px1, px2 in pits)

        ground_y = float(GROUND_Y - P_H)
        if not in_pit and self.y >= ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
            # Platform landing (only outside pits, only while falling)
            if not in_pit and platforms and self.vy >= 0:
                for wx, wy, pw in platforms:
                    if wx <= cx <= wx + pw:
                        prev_feet = (self.y + P_H) - self.vy
                        curr_feet = self.y + P_H
                        if prev_feet <= wy <= curr_feet:
                            self.y = float(wy - P_H)
                            self.vy = 0.0
                            self.on_ground = True
                            break

        self.x = max(0.0, min(self.x, float(WORLD_W - P_W)))

        # Timers
        if self.atk_timer  > 0:
            self.atk_timer -= 1
            if self.atk_timer == 0:
                self._hit_set.clear()
                self.is_heavy_atk = False
        if self.atk_cd     > 0: self.atk_cd     -= 1
        if self.magic_cd      > 0: self.magic_cd      -= 1
        if self.hurt_timer    > 0: self.hurt_timer    -= 1
        if self._hit_flash    > 0: self._hit_flash    -= 1
        if self.speed_boost_t > 0: self.speed_boost_t -= 1
        if self.rage_t        > 0: self.rage_t        -= 1
        if self.combo_window > 0: self.combo_window -= 1
        self._anim_t += 1

        # Magic regen
        self._magic_regen_t += 1
        if self._magic_regen_t >= 60:
            self._magic_regen_t = 0
            self.magic = min(self.max_magic, self.magic + 5)

    # ------------------------------------------------------------------ draw
    def draw(self, surface, cam_x):
        if self.out_of_lives:
            return
        if self.dead:
            return

        sx = int(self.x) - cam_x
        sy = int(self.y)

        # Foot shadow (always at ground level)
        _sw = max(12, int(P_W * 0.80))
        _sh_surf = pygame.Surface((_sw, 7), pygame.SRCALPHA)
        pygame.draw.ellipse(_sh_surf, (0, 0, 0, 52), (0, 0, _sw, 7))
        surface.blit(_sh_surf, (sx + P_W // 2 - _sw // 2, GROUND_Y - 5))

        # Powerup glow aura (ground ellipse + vertical shimmer)
        if self.speed_boost_t > 0 or self.rage_t > 0:
            _pulse = abs(math.sin(self._anim_t * 0.14)) * 0.45 + 0.55
            if self.speed_boost_t > 0:
                _ac = (255, 215, 30, int(110 * _pulse))
            else:
                _ac = (255, 50, 10, int(110 * _pulse))
            _aw = P_W + 26
            _aura = pygame.Surface((_aw, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(_aura, _ac, (0, 0, _aw, 20))
            surface.blit(_aura, (sx - 13, GROUND_Y - 12))
            # Vertical streak above player
            _streak = pygame.Surface((P_W + 10, P_H + 10), pygame.SRCALPHA)
            streak_col = (_ac[0], _ac[1], _ac[2], int(30 * _pulse))
            pygame.draw.ellipse(_streak, streak_col, (0, 0, P_W + 10, P_H + 10))
            surface.blit(_streak, (sx - 5, sy - 5))

        # Invincibility / hurt flicker
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        if self.sprite_char:
            self._draw_sprite(surface, sx, sy)
            self._draw_hud_extras(surface, sx, sy)
            if self._hit_flash > 0:
                _fl = pygame.Surface((P_W + 4, P_H + 4), pygame.SRCALPHA)
                _fl.fill((255, 255, 255, min(220, int(240 * self._hit_flash / 8))))
                surface.blit(_fl, (sx - 2, sy - 2))
            return

        bc = self._body_col
        hc = self._head_col
        cc = self._cape_col
        t  = self._walk_t

        # ---- Cape (drawn first, behind body) ----
        flap = int(math.sin(t * 0.30) * 9) if self.vx != 0 else 3
        if self.facing == 1:   # cape trails left
            cape_pts = [(sx + 3,         sy + 20),
                        (sx - 7,         sy + 22),
                        (sx - 8 - flap,  sy + 52),
                        (sx + 3,         sy + 50)]
        else:                  # cape trails right
            cape_pts = [(sx + P_W - 3,       sy + 20),
                        (sx + P_W + 7,       sy + 22),
                        (sx + P_W + 8 + flap, sy + 52),
                        (sx + P_W - 3,       sy + 50)]
        pygame.draw.polygon(surface, cc, cape_pts)

        # ---- Legs ----
        leg_swing = int(math.sin(t * 0.28) * 9) if self.vx != 0 else 0
        leg_y = sy + P_H - 22
        # Boot dark part
        boot = tuple(max(0, c - 30) for c in bc)
        pygame.draw.rect(surface, bc,   (sx + 4,        leg_y + leg_swing,  14, 14))
        pygame.draw.rect(surface, boot, (sx + 4,        leg_y + leg_swing + 14, 14, 8))
        pygame.draw.rect(surface, bc,   (sx + P_W - 18, leg_y - leg_swing,  14, 14))
        pygame.draw.rect(surface, boot, (sx + P_W - 18, leg_y - leg_swing + 14, 14, 8))

        # ---- Torso ----
        pygame.draw.rect(surface, bc, (sx + 2, sy + 26, P_W - 4, P_H - 48))

        # Shoulder plates
        shoulder = (min(255, bc[0] + 40), min(255, bc[1] + 40), min(255, bc[2] + 40))
        pygame.draw.rect(surface, shoulder, (sx - 4,        sy + 26, 12, 14))  # left
        pygame.draw.rect(surface, shoulder, (sx + P_W - 8,  sy + 26, 12, 14)) # right

        # Belt
        pygame.draw.rect(surface, GUARD_COL, (sx + 2, sy + P_H - 34, P_W - 4, 7))

        # ---- Head (bigger, KayKit-ish) ----
        cx = sx + P_W // 2
        cy = sy + 15
        pygame.draw.circle(surface, hc, (cx, cy), 16)

        # Helmet (full plate) — dome arc
        pygame.draw.arc(surface, GUARD_COL,
                        pygame.Rect(cx - 15, cy - 15, 30, 24), 0, math.pi, 6)
        # Visor band
        pygame.draw.rect(surface, (90, 100, 120), (cx - 13, cy - 2, 26, 7))
        # Eye-glow through visor
        ex = cx + self.facing * 5
        glow_col = (180, 210, 255) if self.player_id == 1 else (255, 180, 180)
        pygame.draw.circle(surface, glow_col, (ex, cy + 1), 2)

        # ---- Shield (off-hand, visible when not attacking; hidden for Nitay/Yael) ----
        if self.atk_timer <= 0 and self.char_name not in ('nitay', 'yael'):
            if self.facing == 1:  # shield on left hand
                pygame.draw.rect(surface, SHIELD_COL,  (sx - 8, sy + 32, 10, 18))
                pygame.draw.rect(surface, (180, 30, 30), (sx - 7, sy + 37, 8,  8))
            else:                 # shield on right hand
                pygame.draw.rect(surface, SHIELD_COL,  (sx + P_W - 2, sy + 32, 10, 18))
                pygame.draw.rect(surface, (180, 30, 30), (sx + P_W - 1, sy + 37, 8,  8))

        # ---- Weapon — Nitay: boxing gloves; Yael: dual daggers; others: sword ----
        if self.char_name == 'yael':
            dag_col  = (210, 120, 200)
            dag_dark = (160, 60, 140)
            if self.atk_timer > 0:
                if self.facing == 1:
                    pygame.draw.rect(surface, dag_dark, (sx + P_W - 2, sy + 22, 4, 28))
                    pygame.draw.polygon(surface, dag_col,
                                        [(sx + P_W + 2, sy + 18), (sx + P_W + 28, sy + 28),
                                         (sx + P_W + 2, sy + 36)])
                else:
                    pygame.draw.rect(surface, dag_dark, (sx - 2, sy + 22, 4, 28))
                    pygame.draw.polygon(surface, dag_col,
                                        [(sx + 2, sy + 18), (sx - 24, sy + 28),
                                         (sx + 2, sy + 36)])
            else:
                ox = sx + P_W - 2 if self.facing == 1 else sx - 2
                pygame.draw.rect(surface, dag_dark, (ox, sy + 26, 3, 24))
        elif self.char_name == 'nitay':
            glove_col  = (220, 30, 30)
            glove_dark = (160, 15, 15)
            if self.atk_timer > 0:
                if self.facing == 1:
                    pygame.draw.rect(surface, glove_dark, (sx + P_W - 5, sy + 26, 14, 18))
                    pygame.draw.circle(surface, glove_col, (sx + P_W + 11, sy + 33), 10)
                else:
                    pygame.draw.rect(surface, glove_dark, (sx - 9, sy + 26, 14, 18))
                    pygame.draw.circle(surface, glove_col, (sx - 11, sy + 33), 10)
            else:
                # Resting fists at sides
                pygame.draw.rect(surface, glove_dark, (sx + P_W - 4, sy + 38, 10, 10))
                pygame.draw.rect(surface, glove_dark, (sx - 6,       sy + 38, 10, 10))
        else:
            is_finisher = (self.combo_count == 2 and self.atk_timer > 0)
            sword_col   = (255, 100, 30) if (self.is_heavy_atk and self.atk_timer > 0) else (SWORD_COMBO if is_finisher else SWORD_COL)

            if self.atk_timer > 0:
                sw = self.current_atk_w + 12
                if self.facing == 1:
                    pygame.draw.rect(surface, sword_col, (sx + P_W - 8, sy + 24, sw, 9))
                    pygame.draw.rect(surface, GUARD_COL, (sx + P_W - 13, sy + 18, 10, 20))
                    if is_finisher:
                        pygame.draw.rect(surface, WHITE, (sx + P_W - 8, sy + 24, sw, 9), 1)
                else:
                    pygame.draw.rect(surface, sword_col, (sx - sw + 8, sy + 24, sw, 9))
                    pygame.draw.rect(surface, GUARD_COL, (sx + 3, sy + 18, 10, 20))
                    if is_finisher:
                        pygame.draw.rect(surface, WHITE, (sx - sw + 8, sy + 24, sw, 9), 1)
            else:
                ox = sx + P_W - 3 if self.facing == 1 else sx - 3
                pygame.draw.rect(surface, SWORD_COL, (ox, sy + 26, 5, 34))

        # ---- Combo pip indicators (small dots above head) ----
        if self.combo_window > 0:
            for i in range(3):
                pip_col = SWORD_COMBO if i < self.combo_count + 1 else (60, 60, 60)
                pygame.draw.circle(surface, pip_col, (sx + 10 + i * 10, sy - 8), 4)

    # -------------------------------------------------------- sprite helpers
    def _current_anim(self):
        if self.hurt_timer > 0:
            return 'hurt'
        if self.atk_timer > 0:
            return 'attack'
        if not self.on_ground:
            return 'jump'
        if abs(self.vx) > 0:
            speed = abs(self.vx)
            return 'run' if speed >= P_SPEED else 'walk'
        return 'idle'

    def _draw_sprite(self, surface, sx, sy):
        char   = self.sprite_char
        anim   = self._current_anim()
        speed  = sprites.ANIM_SPEED.get(anim, 8)
        n      = sprites.frame_count(char, anim)
        if n == 0:
            anim = 'idle'
            n    = sprites.frame_count(char, anim)
        idx    = (self._anim_t // speed) % max(1, n)
        flip   = (self.facing == -1)
        t_h    = sprites.char_height(char)
        surf   = sprites.get_frame(char, anim, idx, t_h, flip=flip)
        if surf is None:
            return
        sw = surf.get_width()
        # Center horizontally; bottom-align to collision box bottom
        blit_x = sx + P_W // 2 - sw // 2
        blit_y = sy + P_H - t_h          # bottom of sprite = bottom of hitbox
        # Attack motion trail: ghost echoes fade from newest to oldest
        if self.atk_timer > 0:
            _TRAIL_ALPHA = (14, 28, 45, 65, 88)
            for i, (tx, ty, tf, tfl) in enumerate(self._atk_trail):
                g = sprites.get_frame(char, anim, tf, t_h, flip=tfl)
                if g is None:
                    continue
                gc = g.copy()
                gc.fill((70, 150, 255, _TRAIL_ALPHA[min(i, 4)]),
                        special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(gc, (tx, ty))
            if len(self._atk_trail) >= 5:
                self._atk_trail.pop(0)
            self._atk_trail.append((blit_x, blit_y, idx, flip))
        else:
            self._atk_trail.clear()
        # 4-direction outline — colored when a powerup is active
        _outline = surf.copy()
        if self.rage_t > 0:
            _outline.fill((220, 30, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        elif self.speed_boost_t > 0:
            _outline.fill((255, 200, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            _outline.fill((18, 14, 10, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for _dx, _dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(_outline, (blit_x + _dx, blit_y + _dy))
        surface.blit(surf, (blit_x, blit_y))

    def _draw_hud_extras(self, surface, sx, sy):
        """Combo pips + Nitay glove overlay — drawn on top of the sprite."""
        if self.combo_window > 0:
            for i in range(3):
                pip_col = SWORD_COMBO if i < self.combo_count + 1 else (60, 60, 60)
                pygame.draw.circle(surface, pip_col,
                                   (sx + 10 + i * 10, sy - 8), 4)
        if self.char_name == 'nitay' and self.atk_timer > 0:
            glove_col = (220, 30, 30)
            fist_x = (sx + int(P_W * 1.0)) if self.facing == 1 else (sx - int(P_W * 0.2))
            fist_y = sy + int(P_H * 0.58)
            pygame.draw.circle(surface, glove_col, (fist_x, fist_y), 9)

    # ------------------------------------------------------------------ label
    _respawn_font = None   # class-level cache — created once

    def draw_respawn_countdown(self, surface, cam_x):
        """Show countdown above respawn point while dead."""
        if not self.dead or self.out_of_lives or self.respawn_timer <= 0:
            return
        if Player._respawn_font is None:
            Player._respawn_font = pygame.font.SysFont('Arial', 20, bold=True)
        sx   = max(cam_x + 120, 80) - cam_x
        secs = math.ceil(self.respawn_timer / 60)
        txt  = Player._respawn_font.render(f'P{self.player_id} respawn {secs}…', True, WHITE)
        surface.blit(txt, (sx, GROUND_Y - P_H - 30))
