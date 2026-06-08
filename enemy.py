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

        self._walk_t      = 0
        self._die_timer   = 0
        self._die_vx      = 0.0
        self._die_vy      = 0.0
        self._pit_avoid_cd = 0  # frames before this enemy can re-evaluate pit avoidance

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
        self._die_timer = 0

        # Phase 2 charge
        self._phase2        = False
        self._charge_timer  = 0
        self._charge_cd     = 0
        self._charge_warned = False

        # Lunge attack (state: 0=idle, 1=windup, 2=active)
        self._lunge_state   = 0
        self._lunge_t       = 0
        self._lunge_cd      = B_LUNGE_CD
        self._lunge_hit_set = set()

        # Ground Slam (state: 0=idle, 1=airborne)
        self._slam_state    = 0
        self._slam_cd       = B_SLAM_CD // 2
        self._slam_hit_set  = set()

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
            self._charge_cd = 60

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
                for p in candidates:
                    if self.rect.colliderect(p.rect):
                        p.take_damage(self.CHARGE_DMG)
                if self._charge_timer == 0:
                    self.vx = 0.0
                    self._charge_cd = B_P2_CHARGE_CD  # shorter in phase 2
            elif self._charge_cd == 0 and self.hurt_timer <= 0 and self._lunge_state == 0:
                self._charge_timer = self.CHARGE_DUR
                self.vx = math.copysign(self.CHARGE_SPEED, dx)
                self.facing = 1 if dx > 0 else -1

        # Lunge attack (triggers at 70% HP — earlier than phase 2)
        if self.hp < self.max_hp * 0.7 and self._charge_timer == 0 and self.hurt_timer == 0:
            if self._lunge_state == 0:
                if self._lunge_cd > 0:
                    self._lunge_cd -= 1
                elif abs(dx) < B_LUNGE_RANGE * 2.5:
                    self._lunge_state = 1
                    self._lunge_t = B_LUNGE_WINDUP
                    self._lunge_cd = B_LUNGE_CD
                    self._lunge_hit_set.clear()
                    self.facing = 1 if dx >= 0 else -1
            elif self._lunge_state == 1:
                self._lunge_t -= 1
                if self._lunge_t == 0:
                    self._lunge_state = 2
                    self._lunge_t = B_LUNGE_DUR
                    self.vx = math.copysign(7.0, self.facing)
            elif self._lunge_state == 2:
                self._lunge_t -= 1
                for p in candidates:
                    if p not in self._lunge_hit_set:
                        if abs(p.rect.centerx - self.rect.centerx) < B_LUNGE_RANGE:
                            self._lunge_hit_set.add(p)
                            p.take_damage(B_LUNGE_DMG)
                if self._lunge_t == 0:
                    self._lunge_state = 0
                    self.vx = 0.0

        # Ground Slam (triggers below 25% HP)
        if self.hp < self.max_hp // 4 and self._charge_timer == 0 and self._lunge_state == 0:
            if self._slam_state == 0:
                if self._slam_cd > 0:
                    self._slam_cd -= 1
                elif self.on_ground and self.hurt_timer == 0:
                    self._slam_state = 1
                    self.vy = B_SLAM_VY
                    self._slam_cd = B_SLAM_CD
                    self._slam_hit_set.clear()
            elif self._slam_state == 1:
                if self.on_ground and self.vy == 0.0:
                    # Just landed — apply shockwave
                    for p in candidates:
                        if p not in self._slam_hit_set:
                            if abs(p.rect.centerx - self.rect.centerx) < B_SLAM_RANGE:
                                self._slam_hit_set.add(p)
                                p.take_damage(B_SLAM_DMG)
                    self._slam_state = 0

        if self._charge_timer <= 0 and self._lunge_state != 2:
            if self.hurt_timer <= 0 and self._lunge_state == 0:
                if abs(dx) > self.ATK_RANGE + 15:
                    speed = self.SPEED * (1.7 if self.phase2 else 1.1)
                    self.vx = math.copysign(speed, dx)
                    self.facing = 1 if dx > 0 else -1
                    self._walk_t += 1
                else:
                    # In attack range: strafe slowly to stay threatening
                    if self.phase2:
                        self.vx = math.copysign(self.SPEED * 0.4, dx) if abs(dx) > 20 else 0.0
                    else:
                        self.vx = 0.0
                    self.facing = 1 if dx >= 0 else -1
            elif self.hurt_timer > 0:
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

        # Lunge telegraph: yellow glow during windup
        if self._lunge_state == 1:
            glow_alpha = int(180 * (1 - self._lunge_t / B_LUNGE_WINDUP))
            glow = pygame.Surface((self.W + 20, self.H + 10), pygame.SRCALPHA)
            glow.fill((255, 220, 0, glow_alpha))
            surface.blit(glow, (sx - 10, sy - 5))

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


# ---------------------------------------------------------------------------
# Thrower — ranged axe-tosser; retreats from melee, throws axes from range
# ---------------------------------------------------------------------------

class Thrower(Grunt):
    W, H      = E_W, E_H
    SPEED     = TR_SPEED
    HP_MAX    = TR_HP
    ATK_DMG   = TR_ATK_DMG
    ATK_RANGE = TR_ATK_RANGE
    ATK_CD    = TR_THROW_CD
    HURT_DUR  = E_HURT_DUR
    SCORE     = TR_SCORE
    DEATH_COL = THROWER_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self._projectiles = []   # [world_x, world_y, vx, alive]
        self.pending_hits  = []  # game.py reads this each frame to deal damage

    def can_attack(self, players):
        """Launch a projectile when in range and cooldown ready."""
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        if abs(dx) <= self.ATK_RANGE:
            vx = math.copysign(TR_PROJ_SPD, dx)
            self._projectiles.append([
                float(self.rect.centerx), float(self.rect.centery), vx, True
            ])
            self.atk_cd = self.ATK_CD
            self.facing = 1 if dx > 0 else -1
        return False, None  # damage flows through pending_hits

    def update(self, players):
        self.pending_hits = []

        # Advance projectiles and test player collisions
        for proj in self._projectiles:
            if not proj[3]:
                continue
            proj[0] += proj[2]
            if proj[0] < 0 or proj[0] > WORLD_W:
                proj[3] = False
                continue
            pr = pygame.Rect(int(proj[0]) - 7, int(proj[1]) - 5, 14, 10)
            cands = _nearest_player(players)
            if cands:
                for player in cands:
                    if pr.colliderect(player.rect):
                        self.pending_hits.append((player, self.ATK_DMG))
                        proj[3] = False
                        break
        self._projectiles = [p for p in self._projectiles if p[3]]

        # Die animation handled by parent
        if self.dead:
            Grunt.update(self, players)
            return

        # AI: retreat when too close; hold at throw range; advance if too far
        candidates = _nearest_player(players)
        if candidates and self.hurt_timer <= 0:
            target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
            dx = target.rect.centerx - self.rect.centerx
            if abs(dx) < TR_RETREAT:
                self.vx = -math.copysign(self.SPEED, dx)
                self._walk_t += 1
            elif abs(dx) > self.ATK_RANGE:
                self.vx = math.copysign(self.SPEED * 0.7, dx)
                self._walk_t += 1
            else:
                self.vx = 0.0
            self.facing = 1 if dx >= 0 else -1
        elif self.hurt_timer > 0:
            self.vx *= 0.75

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y; self.vy = 0.0; self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def draw(self, surface, cam_x):
        # Draw in-flight axes first
        for proj in self._projectiles:
            if not proj[3]:
                continue
            sx = int(proj[0]) - cam_x
            sy = int(proj[1])
            if -20 <= sx <= SCREEN_W + 20:
                pygame.draw.ellipse(surface, AXE_BLADE,  (sx - 8, sy - 4, 16, 8))
                pygame.draw.rect(surface,   AXE_HANDLE, (sx - 2, sy - 5,  3, 10))
        super().draw(surface, cam_x)

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t
        leg_swing = int(math.sin(t * 0.28) * 8) if self.vx != 0 else 0
        leg_y = sy + self.H - 20
        pygame.draw.rect(surface, THROWER_BODY, (sx + 3,           leg_y + leg_swing,  13, 20))
        pygame.draw.rect(surface, THROWER_BODY, (sx + self.W - 16, leg_y - leg_swing,  13, 20))
        pygame.draw.rect(surface, THROWER_BODY, (sx + 2, sy + 20, self.W - 4, self.H - 38))
        pygame.draw.rect(surface, (120, 95, 25), (sx + 2, sy + self.H - 38, self.W - 4, 8))

        cx = sx + self.W // 2
        cy = sy + 12
        pygame.draw.circle(surface, THROWER_HEAD, (cx, cy), 14)
        pygame.draw.arc(surface, (120, 95, 25),
                        pygame.Rect(cx - 14, cy - 14, 28, 22), 0, math.pi, 7)
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, BLACK, (ex, cy + 2), 3)
        pygame.draw.circle(surface, WHITE, (ex + self.facing, cy + 1), 1)

        # Sling/pouch instead of axe
        hx = sx + self.W - 2 if self.facing == 1 else sx - 5
        pygame.draw.rect(surface, (120, 95, 25), (hx, sy + 24, 4, 26))
        pygame.draw.circle(surface, AXE_BLADE,
                           (hx + (8 if self.facing == 1 else -8), sy + 24), 6)


# ---------------------------------------------------------------------------
# Jumper — acrobatic leaper; smaller hitbox while airborne
# ---------------------------------------------------------------------------

class Jumper(Grunt):
    W, H      = E_W, E_H
    SPEED     = JP_SPEED
    HP_MAX    = JP_HP
    ATK_DMG   = JP_ATK_DMG
    ATK_RANGE = JP_ATK_RANGE
    ATK_CD    = 68
    HURT_DUR  = E_HURT_DUR
    SCORE     = JP_SCORE
    DEATH_COL = JUMPER_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self._leap_cd    = JP_LEAP_CD // 2
        self._is_leaping = False

    @property
    def rect(self):
        """Reduced hitbox mid-air — harder to hit."""
        if not self.on_ground:
            w = int(self.W * 0.65)
            h = int(self.H * 0.65)
            return pygame.Rect(
                int(self.x) + (self.W - w) // 2,
                int(self.y) + (self.H - h),
                w, h,
            )
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, players):
        if self.dead:
            Grunt.update(self, players)
            return

        if self._leap_cd > 0:
            self._leap_cd -= 1

        # Land detection
        if self.on_ground and self._is_leaping:
            self._is_leaping = False
            self.atk_cd = 0  # strike immediately on landing

        candidates = _nearest_player(players)
        if candidates and self.hurt_timer <= 0:
            target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
            dx = target.rect.centerx - self.rect.centerx
            if self.on_ground and self._leap_cd == 0 and abs(dx) > 90:
                self.vy = JP_LEAP_VY
                self.vx = math.copysign(self.SPEED * 2.8, dx)
                self.on_ground = False
                self._leap_cd = JP_LEAP_CD
                self._is_leaping = True
            elif abs(dx) > self.ATK_RANGE + 10:
                self.vx = math.copysign(self.SPEED, dx)
                self._walk_t += 1
            else:
                self.vx = 0.0
            self.facing = 1 if dx >= 0 else -1
        elif self.hurt_timer > 0:
            self.vx *= 0.75
            self._is_leaping = False

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y; self.vy = 0.0; self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t
        leg_swing = 14 if self._is_leaping else (int(math.sin(t * 0.32) * 10) if self.vx != 0 else 0)
        leg_y = sy + self.H - 18
        pygame.draw.rect(surface, JUMPER_BODY, (sx + 3,           leg_y + leg_swing,  13, 18))
        pygame.draw.rect(surface, JUMPER_BODY, (sx + self.W - 16, leg_y - leg_swing,  13, 18))
        pygame.draw.rect(surface, JUMPER_BODY, (sx + 2, sy + 18, self.W - 4, self.H - 36))
        pygame.draw.rect(surface, (90, 55, 120), (sx + 2, sy + self.H - 36, self.W - 4, 6))

        cx = sx + self.W // 2
        cy = sy + 12
        pygame.draw.circle(surface, JUMPER_HEAD, (cx, cy), 13)
        pygame.draw.line(surface, (90, 55, 120), (cx - 12, cy - 4), (cx + 12, cy - 4), 3)
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, BLACK, (ex, cy + 2), 3)
        pygame.draw.circle(surface, WHITE, (ex + self.facing, cy + 1), 1)

        # Katar punch blade
        wx = sx + self.W if self.facing == 1 else sx - 10
        pygame.draw.rect(surface, AXE_BLADE, (wx, sy + 28, 10, 5))
        pygame.draw.rect(surface, JUMPER_BODY,
                         (wx + (3 if self.facing == 1 else 0), sy + 24, 4, 10))


# ---------------------------------------------------------------------------
# Healer — support enemy; flees players, heals nearby wounded allies
# ---------------------------------------------------------------------------

class Healer(Grunt):
    W, H      = E_W, E_H
    SPEED     = HL_SPEED
    HP_MAX    = HL_HP
    ATK_DMG   = 0
    ATK_RANGE = 0
    ATK_CD    = 9999
    HURT_DUR  = E_HURT_DUR
    SCORE     = HL_SCORE
    DEATH_COL = HEALER_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self._heal_cd = HL_HEAL_CD // 2

    def can_attack(self, players):
        return False, None

    def update(self, players):
        if self.dead:
            Grunt.update(self, players)
            return

        if self._heal_cd > 0:
            self._heal_cd -= 1

        candidates = _nearest_player(players)
        if candidates and self.hurt_timer <= 0:
            target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
            dx = target.rect.centerx - self.rect.centerx
            if abs(dx) < HL_RETREAT:
                self.vx = -math.copysign(self.SPEED, dx)
                self.facing = 1 if dx > 0 else -1
                self._walk_t += 1
            else:
                self.vx = 0.0
                self.facing = 1 if dx >= 0 else -1
        elif self.hurt_timer > 0:
            self.vx *= 0.75
        else:
            self.vx = 0.0

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y; self.vy = 0.0; self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t
        # Long robe
        pygame.draw.rect(surface, HEALER_ROBE, (sx + 1, sy + 18, self.W - 2, self.H - 18))
        robe_sw = int(math.sin(t * 0.22) * 3) if self.vx != 0 else 0
        pygame.draw.rect(surface, HEALER_ROBE,
                         (sx + 1 + robe_sw, sy + self.H - 18, self.W - 2, 18))
        pygame.draw.rect(surface, HEALER_BODY, (sx + 3, sy + 20, self.W - 6, self.H - 30), 1)

        cx = sx + self.W // 2
        cy = sy + 12
        pygame.draw.circle(surface, HEALER_HEAD, (cx, cy), 13)
        pygame.draw.arc(surface, HEALER_ROBE,
                        pygame.Rect(cx - 15, cy - 14, 30, 24), 0, math.pi, 9)
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, BLACK, (ex, cy + 2), 2)
        pygame.draw.circle(surface, WHITE, (ex + self.facing, cy + 1), 1)

        # Glowing staff — crystal pulses as heal_cd counts down
        hx = sx + self.W if self.facing == 1 else sx - 4
        pygame.draw.rect(surface, (120, 95, 40), (hx, sy + 14, 4, 48))
        gc = int(80 + (1.0 - self._heal_cd / max(1, HL_HEAL_CD)) * 150)
        pygame.draw.circle(surface, (80, gc, 80), (hx + 2, sy + 12), 7)
        pygame.draw.circle(surface, WHITE, (hx + 2, sy + 12), 3)


# ---------------------------------------------------------------------------
# TeacherBoss — Level 2 boss: ruler sweep + chalk throw + reinforcements
# ---------------------------------------------------------------------------

class TeacherBoss(Boss):
    W, H       = TB_W, TB_H
    SPEED      = TB_SPEED
    HP_MAX     = TB_HP
    ATK_DMG    = TB_ATK_DMG
    ATK_RANGE  = TB_ATK_RANGE
    ATK_CD_VAL = TB_ATK_CD
    SCORE      = TB_SCORE
    DEATH_COL  = TB_BODY

    # Disable charge
    CHARGE_SPEED = 0
    CHARGE_DUR   = 0
    CHARGE_CD    = 9999
    CHARGE_DMG   = 0

    def __init__(self, x, y):
        super().__init__(x, y)
        self._chalk = []          # [wx, wy, vx, alive]
        self.pending_hits = []    # processed by game.py
        self._chalk_cd = TB_CHALK_CD // 2
        self._rein_cd  = TB_REIN_CD
        self.pending_spawns = []  # list of world_x values for grunt spawns
        self.swing_text = ''      # 'SILENCE!' — read once by game.py

    def can_attack(self, players):
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        dy = abs(target.rect.centery - self.rect.centery)
        if abs(dx) <= self.ATK_RANGE and dy < self.H:
            self.atk_cd = self.ATK_CD_VAL
            self.swing_text = 'SILENCE!'
            return True, target
        return False, None

    def update(self, players):
        if self.dead:
            # simple death fall (no Boss charge/lunge machinery)
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

        self.pending_hits = []
        self._eye_t += 1

        # Enter phase 2
        if not self._phase2 and self.phase2:
            self._phase2 = True

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx

        # Chalk throw
        if self._chalk_cd > 0:
            self._chalk_cd -= 1
        elif self.hurt_timer == 0 and abs(dx) > 80:
            vx = math.copysign(TB_CHALK_SPD, dx)
            self._chalk.append([float(self.rect.centerx), float(self.rect.centery - 10), vx, True])
            self._chalk_cd = TB_CHALK_CD
            self.facing = 1 if dx > 0 else -1

        # Advance chalk projectiles
        for proj in self._chalk:
            if not proj[3]:
                continue
            proj[0] += proj[2]
            if proj[0] < 0 or proj[0] > WORLD_W:
                proj[3] = False
                continue
            pr = pygame.Rect(int(proj[0]) - 6, int(proj[1]) - 4, 12, 8)
            for p in (candidates or []):
                if pr.colliderect(p.rect):
                    self.pending_hits.append((p, TB_CHALK_DMG))
                    proj[3] = False
                    break
        self._chalk = [c for c in self._chalk if c[3]]

        # Phase 2 reinforcement spawns
        if self._phase2:
            if self._rein_cd > 0:
                self._rein_cd -= 1
            else:
                self._rein_cd = TB_REIN_CD
                cx = self.rect.centerx
                self.pending_spawns += [cx - 120, cx + 120]

        # Movement: circle player, keeping ruler range
        if self.hurt_timer <= 0:
            if abs(dx) > self.ATK_RANGE + 20:
                self.vx = math.copysign(self.SPEED, dx)
                self._walk_t += 1
            elif abs(dx) < 90:
                self.vx = -math.copysign(self.SPEED * 0.6, dx)
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
            self.y = ground_y; self.vy = 0.0; self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        self.hp = max(0, self.hp - dmg)
        self.hurt_timer = max(10, stun // 3)
        self.vx = kb_dir * 1.2
        self.vy = -0.8
        if self.hp == 0:
            self.dead = True
            self._die_timer = 50
            self._die_vx = kb_dir * 2.5
            self._die_vy = -6.0
        return True

    def draw(self, surface, cam_x):
        if self.dead and self._die_timer <= 0:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 20 <= sx <= SCREEN_W + self.W + 20):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        dying = self.dead and self._die_timer > 0
        if dying:
            alpha = int(255 * self._die_timer / 50)
            tmp = pygame.Surface((self.W + 40, self.H + 20), pygame.SRCALPHA)
            self._draw_body(tmp, 20, 10)
            angle = (50 - self._die_timer) * (6 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        self._draw_body(surface, sx, sy)
        # Chalk projectiles
        for proj in self._chalk:
            px = int(proj[0]) - cam_x
            py = int(proj[1])
            if -20 <= px <= SCREEN_W + 20:
                pygame.draw.rect(surface, WHITE,   (px - 5, py - 3, 10, 6))
                pygame.draw.rect(surface, (200, 200, 180), (px - 4, py - 2, 8, 4))
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX,
                self.W + 22, 9, boss=True)

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t
        cx = sx + self.W // 2
        cy = sy + 18

        # Legs in gray trousers
        leg_sw = int(math.sin(t * 0.22) * 8) if self.vx != 0 else 0
        leg_y = sy + self.H - 26
        pygame.draw.rect(surface, TB_SUIT, (sx + 7,           leg_y + leg_sw,  16, 26))
        pygame.draw.rect(surface, TB_SUIT, (sx + self.W - 23, leg_y - leg_sw,  16, 26))
        # Shoes
        pygame.draw.rect(surface, (30, 25, 20), (sx + 5,           leg_y + leg_sw  + 20,  20, 6))
        pygame.draw.rect(surface, (30, 25, 20), (sx + self.W - 25, leg_y - leg_sw  + 20,  20, 6))

        # Suit jacket
        pygame.draw.rect(surface, TB_SUIT, (sx + 4, sy + 34, self.W - 8, self.H - 58))
        # White shirt front
        pygame.draw.rect(surface, (230, 230, 230), (cx - 8, sy + 36, 16, self.H - 68))
        # Tie (red)
        pygame.draw.rect(surface, (190, 30, 30), (cx - 3, sy + 38, 6, self.H - 72))
        # Lapels
        pygame.draw.polygon(surface, (65, 65, 75),
                            [(cx - 8, sy + 34), (cx - 16, sy + 44), (cx, sy + 50)])
        pygame.draw.polygon(surface, (65, 65, 75),
                            [(cx + 8, sy + 34), (cx + 16, sy + 44), (cx, sy + 50)])

        # Head
        pygame.draw.circle(surface, TB_HEAD, (cx, cy), 18)
        # Hair (dark)
        pygame.draw.arc(surface, (40, 30, 20),
                        pygame.Rect(cx - 17, cy - 18, 34, 24), 0, math.pi, 8)
        # Glasses
        gl_y = cy + 2
        pygame.draw.rect(surface, (30, 30, 30), (cx - 16, gl_y - 4, 30, 2))  # frame bridge
        pygame.draw.rect(surface, (30, 30, 30), (cx - 16, gl_y - 4, 12, 10), 1)  # left lens
        pygame.draw.rect(surface, (30, 30, 30), (cx + 3,  gl_y - 4, 12, 10), 1)  # right lens
        # Eyes through glasses
        ex = cx + self.facing * 6
        pygame.draw.circle(surface, (80, 60, 40), (ex, gl_y + 1), 2)

        # Ruler weapon
        rx = sx + self.W + 2 if self.facing == 1 else sx - 36
        pygame.draw.rect(surface, (200, 170, 80), (rx, sy + 36, 34, 8))
        pygame.draw.rect(surface, (220, 195, 110), (rx, sy + 36, 34, 3))
        for tick in range(rx + 4, rx + 32, 6):
            pygame.draw.line(surface, (160, 130, 50), (tick, sy + 36), (tick, sy + 40), 1)


# ---------------------------------------------------------------------------
# RollerBoss — Level 3 boss: skate dash + spin attack
# ---------------------------------------------------------------------------

class RollerBoss(Boss):
    W, H       = RB_W, RB_H
    SPEED      = RB_SPEED
    HP_MAX     = RB_HP
    ATK_DMG    = RB_ATK_DMG
    ATK_RANGE  = RB_ATK_RANGE
    ATK_CD_VAL = RB_ATK_CD
    SCORE      = RB_SCORE
    DEATH_COL  = RB_BODY

    CHARGE_SPEED = RB_DASH_SPD
    CHARGE_DUR   = 55
    CHARGE_CD    = RB_DASH_CD
    CHARGE_DMG   = RB_DASH_DMG

    def __init__(self, x, y):
        super().__init__(x, y)
        self._spin_t    = 0   # spin attack timer
        self._spin_cd   = 60
        self._spin_angle = 0.0

    def update(self, players):
        if self.dead:
            return
        self._eye_t += 1
        self._spin_angle += 0.18 * (2 if self._spin_t > 0 else 1)

        if not self._phase2 and self.phase2:
            self._phase2 = True
            self._charge_cd = 30

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx

        # Skate Dash (charge) — reuse Boss charge machinery
        if self.phase2 or self.hp < self.max_hp * 0.6:
            if self._charge_cd > 0:
                self._charge_cd -= 1
            if self._charge_timer > 0:
                self._charge_timer -= 1
                for p in candidates:
                    if self.rect.colliderect(p.rect):
                        p.take_damage(self.CHARGE_DMG)
                if self._charge_timer == 0:
                    self.vx = 0.0
                    self._charge_cd = self.CHARGE_CD
            elif self._charge_cd == 0 and self.hurt_timer <= 0:
                self._charge_timer = self.CHARGE_DUR
                self.vx = math.copysign(self.CHARGE_SPEED, dx)
                self.facing = 1 if dx > 0 else -1

        # Spin attack
        if self._spin_cd > 0:
            self._spin_cd -= 1
        if self._spin_t > 0:
            self._spin_t -= 1
            for p in candidates:
                if abs(p.rect.centerx - self.rect.centerx) < RB_SPIN_RAD:
                    p.take_damage(RB_SPIN_DMG)
        elif self._spin_cd == 0 and self._charge_timer == 0 and self.hurt_timer == 0:
            self._spin_t  = 25
            self._spin_cd = 90

        if self._charge_timer <= 0:
            if self.hurt_timer <= 0:
                if abs(dx) > self.ATK_RANGE + 10:
                    speed = self.SPEED * (1.3 if self.phase2 else 1.0)
                    self.vx = math.copysign(speed, dx)
                    self.facing = 1 if dx > 0 else -1
                    self._walk_t += 1
                else:
                    self.vx = 0.0
                    self.facing = 1 if dx >= 0 else -1
            else:
                self.vx *= 0.85

        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        ground_y = float(GROUND_Y - self.H)
        if self.y >= ground_y:
            self.y = ground_y; self.vy = 0.0; self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        if self._charge_timer > 0:
            dmg = dmg // 2
        self.hp = max(0, self.hp - dmg)
        if self._charge_timer <= 0:
            self.hurt_timer = max(10, stun // 3)
            self.vx = kb_dir * 1.8
            self.vy = -1.2
        if self.hp == 0:
            self.dead = True
            self._die_timer = 50
            self._die_vx = kb_dir * 3.0
            self._die_vy = -5.5
        return True

    def draw(self, surface, cam_x):
        if self.dead and self._die_timer <= 0:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 20 <= sx <= SCREEN_W + self.W + 20):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        dying = self.dead and self._die_timer > 0
        if dying:
            alpha = int(255 * self._die_timer / 50)
            tmp = pygame.Surface((self.W + 40, self.H + 20), pygame.SRCALPHA)
            self._draw_body(tmp, 20, 10)
            angle = (50 - self._die_timer) * (8 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        # Charge streak
        if self._charge_timer > 0:
            for i in range(1, 5):
                sxs = sx - self.facing * i * 12
                fade = max(0, 180 - i * 40)
                streak = pygame.Surface((self.W, self.H - 30), pygame.SRCALPHA)
                streak.fill((*RB_BODY, fade))
                surface.blit(streak, (sxs, sy + 15))

        # Spin glow
        if self._spin_t > 0:
            spin_surf = pygame.Surface((RB_SPIN_RAD * 2, RB_SPIN_RAD * 2), pygame.SRCALPHA)
            pygame.draw.circle(spin_surf, (100, 200, 255, 60),
                               (RB_SPIN_RAD, RB_SPIN_RAD), RB_SPIN_RAD)
            surface.blit(spin_surf, (sx + self.W // 2 - RB_SPIN_RAD,
                                     sy + self.H // 2 - RB_SPIN_RAD))

        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX,
                self.W + 22, 9, boss=True)

    def _draw_body(self, surface, sx, sy):
        t   = self._walk_t
        cx  = sx + self.W // 2
        cy  = sy + 16
        p2  = self.phase2
        bc  = (min(255, RB_BODY[0] + (30 if p2 else 0)), RB_BODY[1], RB_BODY[2])

        # Legs with skate boot look
        leg_sw = int(math.sin(t * 0.30) * 10) if (self.vx != 0 and self._charge_timer == 0) else 0
        leg_y  = sy + self.H - 30
        pygame.draw.rect(surface, bc,     (sx + 5,           leg_y + leg_sw,  16, 22))
        pygame.draw.rect(surface, (20, 20, 20), (sx + 4,    leg_y + leg_sw + 14, 18, 8))   # boot
        pygame.draw.rect(surface, bc,     (sx + self.W - 21, leg_y - leg_sw,  16, 22))
        pygame.draw.rect(surface, (20, 20, 20), (sx + self.W - 22, leg_y - leg_sw + 14, 18, 8))
        # Wheels (4 small circles)
        for wx_off, wy_off in ((sx + 5, leg_y + leg_sw + 22),
                               (sx + 16, leg_y + leg_sw + 22),
                               (sx + self.W - 21, leg_y - leg_sw + 22),
                               (sx + self.W - 10, leg_y - leg_sw + 22)):
            pygame.draw.circle(surface, (200, 200, 200), (wx_off + 3, wy_off + 3), 4)
            pygame.draw.circle(surface, (80, 80, 80), (wx_off + 3, wy_off + 3), 2)

        # Body
        pygame.draw.rect(surface, bc, (sx + 4, sy + 30, self.W - 8, self.H - 58))
        # Chest stripe
        pygame.draw.rect(surface, (255, 255, 255), (sx + 4, sy + 36, self.W - 8, 5))

        # Shoulder pads
        pygame.draw.rect(surface, (20, 80, 140), (sx - 5, sy + 28, 16, 18))
        pygame.draw.rect(surface, (20, 80, 140), (sx + self.W - 11, sy + 28, 16, 18))

        # Helmet
        pygame.draw.circle(surface, RB_HEAD, (cx, cy), 20)
        pygame.draw.arc(surface, (20, 80, 140),
                        pygame.Rect(cx - 19, cy - 18, 38, 28), 0, math.pi, 9)
        # Visor
        pygame.draw.rect(surface, (30, 30, 30), (cx - 16, cy - 1, 32, 8))
        # Eye glow
        eye_col = (80, 220, 255) if not p2 else (255, 80, 80)
        ex = cx + self.facing * 6
        pygame.draw.circle(surface, eye_col, (ex, cy + 3), 4)
        pygame.draw.circle(surface, WHITE,   (ex, cy + 3), 2)

        # Spinning blade (replaces axe during spin, else static)
        ang = self._spin_angle if self._spin_t > 0 else 0.0
        bx = sx + self.W + 2 if self.facing == 1 else sx - 18
        for k in range(4):
            a = ang + k * math.pi / 2
            ox = int(math.cos(a) * 10)
            oy = int(math.sin(a) * 10)
            pygame.draw.line(surface, AXE_BLADE,
                             (bx + 8, sy + 36), (bx + 8 + ox, sy + 36 + oy), 4)
