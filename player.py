import math
import pygame
from settings import *
import sfx
import sprites

# ---------------------------------------------------------------------------
# Default key bindings — imported by game.py to construct players
# ---------------------------------------------------------------------------
P1_KEYS = {
    'left':   [pygame.K_LEFT,  pygame.K_a],
    'right':  [pygame.K_RIGHT, pygame.K_d],
    'jump':   [pygame.K_UP,    pygame.K_w, pygame.K_SPACE],
    'attack': [pygame.K_INSERT],
    'magic':  [pygame.K_DELETE],
}

P2_KEYS = {
    'left':   [pygame.K_j],
    'right':  [pygame.K_l],
    'jump':   [pygame.K_i],
    'attack': [pygame.K_COMMA],
    'magic':  [pygame.K_PERIOD],
}


_COLOR_PALETTES = {
    'blue':  ((45, 85, 195),  (65, 108, 218),  (28, 50, 155)),
    'red':   ((195, 65, 45),  (218, 90, 65),   (155, 28, 28)),
    'green': ((40, 160, 60),  (65, 195, 85),   (22, 105, 38)),
    'gold':  ((200, 165, 30), (225, 195, 60),  (155, 120, 15)),
}


class Player:
    def __init__(self, x, y, player_id=1, key_bindings=None, joystick=None,
                 color=None, sprite_char=None):
        self.player_id  = player_id
        self.key_bindings = key_bindings or P1_KEYS
        self.joystick   = joystick

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = False

        # Sprite-sheet character ('asaf','lotem','gal','nitay') or None → draw as knight
        self.sprite_char = sprite_char if (sprite_char and sprites.is_ready()) else None
        self._anim_t = 0   # tick counter for sprite animation

        self.hp       = P_HP
        self.max_hp   = P_HP
        self.magic    = P_MAGIC
        self.max_magic = P_MAGIC

        # Combat
        self.atk_timer        = 0
        self.atk_cd           = 0
        self.magic_cd         = 0
        self.hurt_timer       = 0
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

        # Lives & respawn
        self.lives         = PLAYER_LIVES
        self.out_of_lives  = False
        self.respawn_timer = 0

        # Animation
        self._walk_t         = 0
        self._magic_regen_t  = 0
        self._prev_jump      = False  # edge-detect for joystick jump

        # Colour palette — use explicit color arg if given, else default by player_id
        if color is None:
            color = 'blue' if player_id == 1 else 'red'
        if color in _COLOR_PALETTES:
            self._body_col, self._head_col, self._cape_col = _COLOR_PALETTES[color]
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
        state = {a: False for a in ('left', 'right', 'jump', 'attack', 'magic')}

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
                if nb > 3 and j.get_button(3): state['magic']  = True  # Y/Triangle
                if nb > 1 and j.get_button(1): state['attack'] = True  # B/Circle alt
            except Exception:
                pass

        return state

    def handle_input(self, all_keys):
        if self.out_of_lives or self.dead:
            return

        inp = self._read_input(all_keys)

        if self.hurt_timer > 0:
            self.vx *= 0.75
            return

        # Movement
        self.vx = 0.0
        if inp['left']:
            self.vx = -P_SPEED
            self.facing = -1
        if inp['right']:
            self.vx = P_SPEED
            self.facing = 1

        self._walk_t = self._walk_t + 1 if self.vx != 0 else 0

        # Jump (edge-detect for joystick so it doesn't multi-jump)
        jump_now = inp['jump']
        if jump_now and not self._prev_jump and self.on_ground:
            self.vy = JUMP_VY
            self.on_ground = False
        self._prev_jump = jump_now

        # Attack — fires combo
        if inp['attack'] and self.atk_cd <= 0:
            self._fire_attack()

        # Magic
        if inp['magic'] and self.magic_cd <= 0 and self.magic >= P_MAGIC_COST:
            self.magic -= P_MAGIC_COST
            self.magic_cd = P_MAGIC_CD
            self.magic_just_used = True

    def _fire_attack(self):
        # Advance or start combo chain
        if self.combo_window > 0:
            self.combo_count = min(self.combo_count + 1, 2)
        else:
            self.combo_count = 0

        self.combo_window = P_COMBO_WINDOW

        if self.combo_count == 2:                  # ---- FINISHER ----
            self.current_atk_dmg  = P_COMBO3_DMG
            self.current_atk_w    = P_COMBO3_W
            self.current_atk_stun = P_COMBO3_STUN
            self.current_atk_dur  = P_COMBO3_DUR
            self.atk_timer        = P_COMBO3_DUR
            self.atk_cd           = P_ATK_CD + 14
        elif self.combo_count == 1:                # ---- 2nd hit ----
            self.current_atk_dmg  = P_COMBO2_DMG
            self.current_atk_w    = P_ATK_W
            self.current_atk_stun = 0
            self.current_atk_dur  = P_ATK_DUR
            self.atk_timer        = P_ATK_DUR
            self.atk_cd           = P_ATK_CD
        else:                                      # ---- 1st hit ----
            self.current_atk_dmg  = P_ATK_DMG
            self.current_atk_w    = P_ATK_W
            self.current_atk_stun = 0
            self.current_atk_dur  = P_ATK_DUR
            self.atk_timer        = P_ATK_DUR
            self.atk_cd           = P_ATK_CD

        self._hit_set.clear()

    # ------------------------------------------------------------------ damage
    def take_damage(self, dmg):
        if self.hurt_timer > 0 or self.dead or self.out_of_lives:
            return False
        self.hp = max(0, self.hp - dmg)
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
        self.x          = float(max(camera_x + 120, 80))
        self.y          = float(GROUND_Y - P_H)
        self.vx         = 0.0
        self.vy         = 0.0
        self.hp         = P_HP
        self.magic      = P_MAGIC
        self.dead       = False
        self.hurt_timer = INVINCIBILITY_DUR   # invincibility frames on respawn
        self.combo_count = 0
        sfx.play('respawn', 0.6)
        self.combo_window = 0
        self._hit_set.clear()

    # ------------------------------------------------------------------ update
    def update(self, camera_x=0):
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

        ground_y = float(GROUND_Y - P_H)
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(0.0, min(self.x, float(WORLD_W - P_W)))

        # Timers
        if self.atk_timer  > 0:
            self.atk_timer -= 1
            if self.atk_timer == 0:
                self._hit_set.clear()
        if self.atk_cd     > 0: self.atk_cd     -= 1
        if self.magic_cd   > 0: self.magic_cd   -= 1
        if self.hurt_timer > 0: self.hurt_timer -= 1
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

        # Invincibility / hurt flicker
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        if self.sprite_char:
            self._draw_sprite(surface, sx, sy)
            self._draw_hud_extras(surface, sx, sy)
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

        # ---- Shield (off-hand, visible when not attacking) ----
        if self.atk_timer <= 0:
            if self.facing == 1:  # shield on left hand
                pygame.draw.rect(surface, SHIELD_COL,  (sx - 8, sy + 32, 10, 18))
                pygame.draw.rect(surface, (180, 30, 30), (sx - 7, sy + 37, 8,  8))
            else:                 # shield on right hand
                pygame.draw.rect(surface, SHIELD_COL,  (sx + P_W - 2, sy + 32, 10, 18))
                pygame.draw.rect(surface, (180, 30, 30), (sx + P_W - 1, sy + 37, 8,  8))

        # ---- Sword ----
        is_finisher = (self.combo_count == 2 and self.atk_timer > 0)
        sword_col   = SWORD_COMBO if is_finisher else SWORD_COL

        if self.atk_timer > 0:
            sw = self.current_atk_w + 12
            if self.facing == 1:
                pygame.draw.rect(surface, sword_col, (sx + P_W - 8, sy + 24, sw, 9))
                pygame.draw.rect(surface, GUARD_COL, (sx + P_W - 13, sy + 18, 10, 20))
                if is_finisher:  # glow outline
                    pygame.draw.rect(surface, WHITE, (sx + P_W - 8, sy + 24, sw, 9), 1)
            else:
                pygame.draw.rect(surface, sword_col, (sx - sw + 8, sy + 24, sw, 9))
                pygame.draw.rect(surface, GUARD_COL, (sx + 3, sy + 18, 10, 20))
                if is_finisher:
                    pygame.draw.rect(surface, WHITE, (sx - sw + 8, sy + 24, sw, 9), 1)
        else:
            # Idle sword at hip
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
        surface.blit(surf, (blit_x, blit_y))

    def _draw_hud_extras(self, surface, sx, sy):
        """Combo pips — drawn on top of the sprite."""
        if self.combo_window > 0:
            for i in range(3):
                pip_col = SWORD_COMBO if i < self.combo_count + 1 else (60, 60, 60)
                pygame.draw.circle(surface, pip_col,
                                   (sx + 10 + i * 10, sy - 8), 4)

    # ------------------------------------------------------------------ label
    def draw_respawn_countdown(self, surface, cam_x):
        """Show countdown above respawn point while dead."""
        if not self.dead or self.out_of_lives or self.respawn_timer <= 0:
            return
        sx = max(cam_x + 120, 80) - cam_x
        secs = math.ceil(self.respawn_timer / 60)
        font = pygame.font.SysFont('Arial', 20, bold=True)
        txt  = font.render(f'P{self.player_id} respawn {secs}…', True, WHITE)
        surface.blit(txt, (sx, GROUND_Y - P_H - 30))
