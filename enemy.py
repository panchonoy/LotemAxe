import math
import pygame
from settings import *


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _hp_bar(surface, cx, top_y, hp, max_hp, bar_w, bar_h, boss=False):
    bx = cx - bar_w // 2
    by = top_y - bar_h - 6
    pygame.draw.rect(surface, HP_BG, (bx - 1, by - 1, bar_w + 2, bar_h + 2))
    fill = max(0, int(bar_w * hp / max_hp))
    if fill:
        if boss:
            col = (180, 40, 180)
        elif hp > max_hp * 0.5:
            col = HP_GREEN
        else:
            col = HP_RED
        pygame.draw.rect(surface, col, (bx, by, fill, bar_h))


def _nearest_player(players):
    living = [p for p in players if not p.out_of_lives and not p.dead]
    return living or None


# ---------------------------------------------------------------------------
# Grunt — barbarian minion
# ---------------------------------------------------------------------------

class Grunt:
    W, H = E_W, E_H
    SPEED     = E_SPEED
    HP_MAX    = E_HP
    ATK_DMG   = E_ATK_DMG
    ATK_RANGE = E_ATK_RANGE
    ATK_CD    = E_ATK_CD
    HURT_DUR  = E_HURT_DUR
    SCORE     = E_SCORE
    DEATH_COL = ENEMY_BODY

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = -1
        self.on_ground = False

        self.hp        = self.HP_MAX
        self.atk_cd    = 0
        self.hurt_timer = 0
        self.dead      = False

        self.max_hp      = self.HP_MAX
        self.score_value = self.SCORE
        self.death_color = self.DEATH_COL
        self.atk_dmg     = self.ATK_DMG

        self._walk_t    = 0
        self._die_timer = 0
        self._die_vx    = 0.0
        self._die_vy    = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    # -------------------------------------------------------------- combat
    def can_attack(self, players):
        """Returns (True, target_player) or (False, None)."""
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        dy = abs(target.rect.centery - self.rect.centery)
        if abs(dx) <= self.ATK_RANGE and dy < self.H:
            self.atk_cd = self.ATK_CD
            return True, target
        return False, None

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        self.hp = max(0, self.hp - dmg)
        self.hurt_timer = max(self.HURT_DUR, stun)
        self.vx = kb_dir * 4.0
        self.vy = -2.5
        if self.hp == 0:
            self.dead = True
            self._die_timer = 36   # death anim frames
            self._die_vx    = kb_dir * 3.5
            self._die_vy    = -5.0
        return True

    # -------------------------------------------------------------- update
    def update(self, players):
        if self.dead:
            if self._die_timer > 0:
                self._die_timer -= 1
                self._die_vx *= 0.88
                self._die_vy += GRAVITY
                self.x += self._die_vx
                self.y += self._die_vy
                ground_y = float(GROUND_Y - self.H)
                if self.y >= ground_y:
                    self.y = ground_y
                    self._die_vy *= -0.2
            return
        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))

        if self.hurt_timer <= 0:
            dx = target.rect.centerx - self.rect.centerx
            if abs(dx) > self.ATK_RANGE + 10:
                self.vx = math.copysign(self.SPEED, dx)
                self.facing = 1 if dx > 0 else -1
                self._walk_t += 1
            else:
                self.vx = 0.0
                self.facing = 1 if dx >= 0 else -1
        else:
            self.vx *= 0.75

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy

        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))

        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    # -------------------------------------------------------------- draw
    def draw(self, surface, cam_x):
        if self.dead and self._die_timer <= 0:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        # Death tumble: draw on a temp surface with alpha fade
        dying = self.dead and self._die_timer > 0
        if dying:
            alpha = int(255 * self._die_timer / 36)
            tmp = pygame.Surface((self.W + 40, self.H + 20), pygame.SRCALPHA)
            self._draw_body(tmp, 20, 10)
            # rotate to simulate tumble
            angle = (36 - self._die_timer) * (8 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        t = self._walk_t
        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 10, 6)

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t

        # Legs
        leg_swing = int(math.sin(t * 0.28) * 8) if self.vx != 0 else 0
        leg_y = sy + self.H - 20
        pygame.draw.rect(surface, ENEMY_BODY, (sx + 3,         leg_y + leg_swing,  13, 20))
        pygame.draw.rect(surface, ENEMY_BODY, (sx + self.W - 16, leg_y - leg_swing, 13, 20))

        # Torso with fur strips
        pygame.draw.rect(surface, ENEMY_BODY, (sx + 2, sy + 20, self.W - 4, self.H - 38))
        fur_strip = (min(255, ENEMY_BODY[0] + 30), min(255, ENEMY_BODY[1] + 20), ENEMY_BODY[2])
        for fy in range(sy + 22, sy + self.H - 30, 8):
            pygame.draw.rect(surface, fur_strip, (sx + 4, fy, self.W - 8, 3))
        # Belt
        pygame.draw.rect(surface, HELMET_COL, (sx + 2, sy + self.H - 38, self.W - 4, 8))

        # Head (bigger)
        cx = sx + self.W // 2
        cy = sy + 12
        pygame.draw.circle(surface, ENEMY_HEAD, (cx, cy), 14)

        # Bear helmet dome + ears
        pygame.draw.arc(surface, HELMET_COL,
                        pygame.Rect(cx - 14, cy - 14, 28, 22), 0, math.pi, 7)
        pygame.draw.circle(surface, HELMET_COL, (cx - 11, cy - 13), 6)
        pygame.draw.circle(surface, HELMET_COL, (cx + 11, cy - 13), 6)
        # Inner ear
        pygame.draw.circle(surface, ENEMY_HEAD, (cx - 11, cy - 13), 3)
        pygame.draw.circle(surface, ENEMY_HEAD, (cx + 11, cy - 13), 3)

        # Eye
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, BLACK, (ex, cy + 2), 3)
        pygame.draw.circle(surface, WHITE, (ex + self.facing, cy + 1), 1)

        # Axe
        hx = sx + self.W - 2 if self.facing == 1 else sx - 6
        pygame.draw.rect(surface, AXE_HANDLE, (hx, sy + 22, 5, 32))
        if self.facing == 1:
            blade = [(hx + 4, sy + 22), (hx + 18, sy + 15),
                     (hx + 18, sy + 40), (hx + 4,  sy + 37)]
        else:
            blade = [(hx + 1, sy + 22), (hx - 13, sy + 15),
                     (hx - 13, sy + 40), (hx + 1,  sy + 37)]
        pygame.draw.polygon(surface, AXE_BLADE, blade)


# ---------------------------------------------------------------------------
# Heavy — armoured bruiser
# ---------------------------------------------------------------------------

class Heavy(Grunt):
    W, H = H_W, H_H
    SPEED     = H_SPEED
    HP_MAX    = H_HP
    ATK_DMG   = H_ATK_DMG
    ATK_RANGE = H_ATK_RANGE
    ATK_CD    = H_ATK_CD
    HURT_DUR  = H_HURT_DUR
    SCORE     = H_SCORE
    DEATH_COL = HEAVY_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp  = self.HP_MAX
        self.atk_dmg    = self.ATK_DMG
        self.score_value = self.SCORE
        self.death_color = self.DEATH_COL

    def draw(self, surface, cam_x):
        if self.dead:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        t = self._walk_t

        # Legs (thicker, armoured)
        leg_swing = int(math.sin(t * 0.22) * 9) if self.vx != 0 else 0
        leg_y = sy + self.H - 24
        pygame.draw.rect(surface, HEAVY_BODY,  (sx + 4,          leg_y + leg_swing,  16, 24))
        pygame.draw.rect(surface, HEAVY_ARMOR, (sx + 4,          leg_y + leg_swing,  16,  8))
        pygame.draw.rect(surface, HEAVY_BODY,  (sx + self.W - 20, leg_y - leg_swing, 16, 24))
        pygame.draw.rect(surface, HEAVY_ARMOR, (sx + self.W - 20, leg_y - leg_swing, 16,  8))

        # Torso (chest plate)
        pygame.draw.rect(surface, HEAVY_BODY,  (sx + 2, sy + 24, self.W - 4, self.H - 46))
        pygame.draw.rect(surface, HEAVY_ARMOR, (sx + 2, sy + 24, self.W - 4, 20))  # breastplate

        # Shoulder guards (big)
        pygame.draw.rect(surface, HEAVY_ARMOR, (sx - 6,          sy + 24, 16, 18))
        pygame.draw.rect(surface, HEAVY_ARMOR, (sx + self.W - 10, sy + 24, 16, 18))

        # Head (big helmet)
        cx = sx + self.W // 2
        cy = sy + 14
        pygame.draw.circle(surface, HEAVY_HEAD, (cx, cy), 17)
        # Full-face helmet dome
        pygame.draw.arc(surface, HEAVY_ARMOR,
                        pygame.Rect(cx - 16, cy - 15, 32, 26), 0, math.pi, 8)
        # Nasal / face plate
        pygame.draw.rect(surface, HEAVY_ARMOR, (cx - 14, cy - 3, 28, 9))
        # Eye slits
        pygame.draw.rect(surface, BLACK, (cx - 10, cy - 1, 7, 4))
        pygame.draw.rect(surface, BLACK, (cx + 3,  cy - 1, 7, 4))

        # Club weapon
        hx = sx + self.W - 2 if self.facing == 1 else sx - 6
        pygame.draw.rect(surface, CLUB_COL, (hx, sy + 26, 7, 38))
        # Club head (spiked ball)
        cbx = hx + (14 if self.facing == 1 else -14)
        cby = sy + 26
        pygame.draw.circle(surface, CLUB_HEAD, (cbx + 3, cby + 8), 12)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            spx = cbx + 3 + int(math.cos(rad) * 13)
            spy = cby + 8 + int(math.sin(rad) * 13)
            pygame.draw.circle(surface, HEAVY_ARMOR, (spx, spy), 3)

        # HP bar (wider, orange tinted since it's a tough enemy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 14, 8)


# ---------------------------------------------------------------------------
# Boss
# ---------------------------------------------------------------------------

class Boss:
    W, H = B_W, B_H
    SPEED     = B_SPEED
    HP_MAX    = B_HP
    ATK_DMG   = B_ATK_DMG
    ATK_RANGE = B_ATK_RANGE
    ATK_CD_VAL = B_ATK_CD
    SCORE     = B_SCORE
    DEATH_COL = BOSS_BODY

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = -1
        self.on_ground = False

        self.hp         = self.HP_MAX
        self.max_hp     = self.HP_MAX
        self.atk_cd     = 0
        self.hurt_timer = 0
        self.dead       = False

        self.score_value = self.SCORE
        self.death_color = self.DEATH_COL
        self.atk_dmg     = self.ATK_DMG

        self._walk_t    = 0
        self._eye_t     = 0

        # Phase 2
        self._phase2        = False
        self._charge_timer  = 0   # frames left in active charge
        self._charge_cd     = 0   # cooldown before next charge
        self._charge_warned = False

    CHARGE_SPEED = 9.0
    CHARGE_DUR   = 40   # frames the charge lasts
    CHARGE_CD    = 180  # frames between charges
    CHARGE_DMG   = 35   # area slam damage on charge hit

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    @property
    def phase2(self):
        return self.hp <= self.max_hp // 2

    def can_attack(self, players):
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        if self._charge_timer > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        dy = abs(target.rect.centery - self.rect.centery)
        if abs(dx) <= self.ATK_RANGE and dy < self.H:
            self.atk_cd = self.ATK_CD_VAL
            return True, target
        return False, None

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        if self._charge_timer > 0:
            dmg = dmg // 2   # damage reduction during charge
        self.hp = max(0, self.hp - dmg)
        if self._charge_timer <= 0:
            self.hurt_timer = max(10, stun // 3)
            self.vx = kb_dir * 1.5
            self.vy = -1.0
        if self.hp == 0:
            self.dead = True
        return True

    def update(self, players):
        if self.dead:
            return
        self._eye_t += 1

        # Enter phase 2
        if not self._phase2 and self.phase2:
            self._phase2 = True
            self._charge_cd = 60   # short delay before first charge

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx

        # Phase 2 charge logic
        if self.phase2:
            if self._charge_cd > 0:
                self._charge_cd -= 1
            if self._charge_timer > 0:
                self._charge_timer -= 1
                # during charge: check area hit
                for p in candidates:
                    if self.rect.colliderect(p.rect):
                        p.take_damage(self.CHARGE_DMG)
                if self._charge_timer == 0:
                    self.vx = 0.0
                    self._charge_cd = self.CHARGE_CD
            elif self._charge_cd == 0 and self.hurt_timer <= 0:
                # launch charge toward target
                self._charge_timer = self.CHARGE_DUR
                self.vx = math.copysign(self.CHARGE_SPEED, dx)
                self.facing = 1 if dx > 0 else -1

        if self._charge_timer <= 0:
            if self.hurt_timer <= 0:
                if abs(dx) > self.ATK_RANGE + 15:
                    speed = self.SPEED * (1.4 if self.phase2 else 1.0)
                    self.vx = math.copysign(speed, dx)
                    self.facing = 1 if dx > 0 else -1
                    self._walk_t += 1
                else:
                    self.vx = 0.0
                    self.facing = 1 if dx >= 0 else -1
            else:
                self.vx *= 0.8

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy

        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def draw(self, surface, cam_x):
        if self.dead:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 20 <= sx <= SCREEN_W + self.W + 20):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        t  = self._walk_t
        et = self._eye_t
        p2 = self.phase2

        body_col  = (min(255, BOSS_BODY[0]  + (40 if p2 else 0)), BOSS_BODY[1],  BOSS_BODY[2])
        armor_col = (min(255, BOSS_ARMOR[0] + (30 if p2 else 0)), BOSS_ARMOR[1], BOSS_ARMOR[2])

        # Charge streak effect
        if self._charge_timer > 0:
            streak_col = (220, 60, 60)
            for i in range(1, 4):
                sx2 = sx - self.facing * i * 14
                pygame.draw.rect(surface, streak_col,
                                 (sx2 + 3, sy + 28, self.W - 6, self.H - 52), 0)
                streak_col = tuple(max(0, c - 50) for c in streak_col)

        # Legs
        leg_swing = int(math.sin(t * 0.25) * 11) if self.vx != 0 else 0
        leg_y = sy + self.H - 26
        pygame.draw.rect(surface, body_col,  (sx + 6,          leg_y + leg_swing,  16, 26))
        pygame.draw.rect(surface, armor_col, (sx + 6,          leg_y + leg_swing,  16,  9))
        pygame.draw.rect(surface, body_col,  (sx + self.W - 22, leg_y - leg_swing, 16, 26))
        pygame.draw.rect(surface, armor_col, (sx + self.W - 22, leg_y - leg_swing, 16,  9))

        # Torso
        pygame.draw.rect(surface, body_col,  (sx + 3, sy + 28, self.W - 6, self.H - 52))
        pygame.draw.rect(surface, armor_col, (sx + 3, sy + 28, self.W - 6, 22))  # chest

        # Shoulder pauldrons
        pygame.draw.rect(surface, armor_col, (sx - 7,          sy + 26, 18, 22))
        pygame.draw.rect(surface, armor_col, (sx + self.W - 11, sy + 26, 18, 22))
        pygame.draw.circle(surface, BOSS_CROWN, (sx - 2,             sy + 26), 5)  # gem
        pygame.draw.circle(surface, BOSS_CROWN, (sx + self.W + 2,    sy + 26), 5)

        # Head (big)
        cx = sx + self.W // 2
        cy = sy + 17
        pygame.draw.circle(surface, BOSS_HEAD, (cx, cy), 19)

        # Crown
        crown = [(cx - 16, cy - 14), (cx - 16, cy - 26),
                 (cx - 9,  cy - 19), (cx,       cy - 28),
                 (cx + 9,  cy - 19), (cx + 16,  cy - 26),
                 (cx + 16, cy - 14)]
        pygame.draw.polygon(surface, BOSS_CROWN, crown)
        for gx in (cx - 13, cx, cx + 13):
            pygame.draw.circle(surface, (220, 80, 80), (gx, cy - 19), 4)

        # Pulsing evil eyes (faster + brighter in phase 2)
        pulse_speed = 0.18 if p2 else 0.08
        pulse = int(abs(math.sin(et * pulse_speed)) * 80)
        eye_col = (200 + pulse // 2, 20, 20) if p2 else (175 + pulse // 2, 20, 20)
        for sign in (-1, 1):
            ex = cx + sign * 8
            pygame.draw.circle(surface, eye_col, (ex, cy + 3), 6)
            pygame.draw.circle(surface, BLACK,   (ex, cy + 3), 3)

        # Giant axe
        hx = sx + self.W - 4 if self.facing == 1 else sx - 8
        pygame.draw.rect(surface, AXE_HANDLE, (hx, sy + 28, 8, 54))
        if self.facing == 1:
            blade = [(hx + 7, sy + 28), (hx + 36, sy + 16),
                     (hx + 36, sy + 58), (hx + 7,  sy + 55)]
        else:
            blade = [(hx + 1, sy + 28), (hx - 28, sy + 16),
                     (hx - 28, sy + 58), (hx + 1,  sy + 55)]
        pygame.draw.polygon(surface, AXE_BLADE, blade)
        # Blade edge highlight
        pygame.draw.polygon(surface, WHITE, blade, 1)

        # Small HP bar above head (big boss bar is in ui.py)
        _hp_bar(surface, cx, sy, self.hp, self.HP_MAX, self.W + 22, 9, boss=True)
