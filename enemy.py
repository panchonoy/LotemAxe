import math
import random
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
        self._hit_flash = 5
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
            if abs(dx) > self.ATK_RANGE:
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
        self._die_vx    = 0.0
        self._die_vy    = 0.0

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

        # Mid-fight minion waves
        self.pending_wave_spawns = []   # [(world_x, kind), ...]
        self._wave_spawned       = set()

    def _emit_wave(self, wave_num):
        """Level 1 Boss — spawn grunt waves from screen edges at HP thresholds."""
        bx = int(self.x)
        # Spawn from both sides: 300px left and right of boss
        left_x  = max(50,         bx - 320)
        right_x = min(WORLD_W - 50, bx + 320)
        if wave_num == 1:
            self.pending_wave_spawns = [(left_x, 'grunt'), (right_x, 'grunt')]
        elif wave_num == 2:
            self.pending_wave_spawns = [(left_x, 'grunt'), (right_x, 'grunt'),
                                        (bx - 160, 'heavy')]
        else:
            self.pending_wave_spawns = [(left_x, 'grunt'), (right_x, 'grunt'),
                                        (left_x + 60, 'grunt'), (bx, 'heavy')]

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
            self._die_timer = 50
            self._die_vx    = kb_dir * 2.5
            self._die_vy    = -6.0
        self._hit_flash = 5
        return True

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
        self._eye_t += 1

        # --- Mid-fight minion waves (HP thresholds) ---
        hp_pct = self.hp / self.HP_MAX
        if 'w1' not in self._wave_spawned and hp_pct <= 0.75:
            self._wave_spawned.add('w1')
            self._emit_wave(1)
        if 'w2' not in self._wave_spawned and hp_pct <= 0.50:
            self._wave_spawned.add('w2')
            self._emit_wave(2)
        if 'w3' not in self._wave_spawned and hp_pct <= 0.25:
            self._wave_spawned.add('w3')
            self._emit_wave(3)

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

        p2 = self.phase2

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

        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 22, 9, boss=True)

    def _draw_body(self, surface, sx, sy):
        t  = self._walk_t
        p2 = self.phase2
        body_col  = (min(255, BOSS_BODY[0]  + (40 if p2 else 0)), BOSS_BODY[1],  BOSS_BODY[2])
        armor_col = (min(255, BOSS_ARMOR[0] + (30 if p2 else 0)), BOSS_ARMOR[1], BOSS_ARMOR[2])

        # Legs
        leg_swing = int(math.sin(t * 0.25) * 11) if self.vx != 0 else 0
        leg_y = sy + self.H - 26
        pygame.draw.rect(surface, body_col,  (sx + 6,           leg_y + leg_swing,  16, 26))
        pygame.draw.rect(surface, armor_col, (sx + 6,           leg_y + leg_swing,  16,  9))
        pygame.draw.rect(surface, body_col,  (sx + self.W - 22, leg_y - leg_swing,  16, 26))
        pygame.draw.rect(surface, armor_col, (sx + self.W - 22, leg_y - leg_swing,  16,  9))

        # Torso
        pygame.draw.rect(surface, body_col,  (sx + 3, sy + 28, self.W - 6, self.H - 52))
        pygame.draw.rect(surface, armor_col, (sx + 3, sy + 28, self.W - 6, 22))

        # Shoulder pauldrons
        pygame.draw.rect(surface, armor_col, (sx - 7,           sy + 26, 18, 22))
        pygame.draw.rect(surface, armor_col, (sx + self.W - 11, sy + 26, 18, 22))
        pygame.draw.circle(surface, BOSS_CROWN, (sx - 2,            sy + 26), 5)
        pygame.draw.circle(surface, BOSS_CROWN, (sx + self.W + 2,   sy + 26), 5)

        # Head
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

        # Pulsing evil eyes
        pulse = int(abs(math.sin(self._eye_t * (0.18 if p2 else 0.08))) * 80)
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
        pygame.draw.polygon(surface, WHITE, blade, 1)


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
# Cannoneer — artillery lobber; fires arcing cannonballs that explode on landing
# ---------------------------------------------------------------------------

class Cannoneer(Grunt):
    W, H      = E_W, E_H
    SPEED     = CN_SPEED
    HP_MAX    = CN_HP
    ATK_DMG   = 0
    ATK_RANGE = CN_RETREAT
    ATK_CD    = CN_FIRE_CD
    HURT_DUR  = E_HURT_DUR
    SCORE     = CN_SCORE
    DEATH_COL = CN_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self._cannonballs  = []
        self.pending_hits  = []
        self.pending_blasts = []
        self._fire_cd = random.randint(CN_FIRE_CD // 2, CN_FIRE_CD)
        self._ball_shadow = pygame.Surface((40, 10), pygame.SRCALPHA)  # reused each frame

    def can_attack(self, players):
        return False, None   # damage via pending_hits only

    def update(self, players):
        self.pending_hits   = []
        self.pending_blasts = []

        # Advance cannonballs (even while dead so in-flight balls finish)
        live = []
        for ball in self._cannonballs:
            ball[3] += GRAVITY
            ball[0] += ball[2]
            ball[1] += ball[3]
            if ball[0] < 0 or ball[0] > WORLD_W:
                continue
            landed = ball[1] >= GROUND_Y - CN_PROJ_SIZE
            consumed = False
            if not landed:
                # Direct hit while airborne
                br = pygame.Rect(int(ball[0]) - CN_PROJ_SIZE, int(ball[1]) - CN_PROJ_SIZE,
                                 CN_PROJ_SIZE * 2, CN_PROJ_SIZE * 2)
                for p in players:
                    if not p.dead and br.colliderect(p.rect):
                        self.pending_hits.append((p, CN_PROJ_DMG))
                        consumed = True
                        break
            else:
                # Landing blast
                self.pending_blasts.append((ball[0], float(GROUND_Y)))
                for p in players:
                    if not p.dead and abs(p.rect.centerx - ball[0]) < CN_BLAST_RAD:
                        self.pending_hits.append((p, CN_PROJ_DMG))
                consumed = True
            if not consumed:
                live.append(ball)
        self._cannonballs = live

        if self.dead:
            Grunt.update(self, players)
            return

        candidates = _nearest_player(players)
        if candidates and self.hurt_timer <= 0:
            target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
            dx = target.rect.centerx - self.rect.centerx
            adx = abs(dx)

            if adx < CN_RETREAT:
                self.vx = -math.copysign(self.SPEED, dx)
                self._walk_t += 1
            elif adx > CN_FIRE_MAX:
                self.vx = math.copysign(self.SPEED * 0.7, dx)
                self._walk_t += 1
            else:
                self.vx = 0.0
            self.facing = 1 if dx >= 0 else -1

            # Fire
            if self._fire_cd > 0:
                self._fire_cd -= 1
            elif CN_FIRE_MIN <= adx <= CN_FIRE_MAX:
                T = 2.0 * CN_LAUNCH_VY / GRAVITY
                # Lead the target slightly based on its current velocity
                lead = getattr(target, 'vx', 0.0) * T * 0.25
                vx_proj = (dx + lead) / T
                self._cannonballs.append([
                    float(self.rect.centerx), float(self.rect.centery - 8),
                    vx_proj, -CN_LAUNCH_VY
                ])
                self._fire_cd = random.randint(int(CN_FIRE_CD * 0.75),
                                               int(CN_FIRE_CD * 1.30))
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
        # Draw cannonballs and landing shadows first (behind enemy)
        for ball in self._cannonballs:
            bx = int(ball[0]) - cam_x
            by = int(ball[1])
            # Ground shadow at predicted landing x
            vy_b, vx_b = ball[3], ball[2]
            disc = vy_b * vy_b + 2.0 * GRAVITY * (GROUND_Y - ball[1] - CN_PROJ_SIZE)
            if disc >= 0:
                t_land = (-vy_b + math.sqrt(disc)) / GRAVITY
                shadow_x = bx + int(vx_b * t_land)
                alpha = max(30, min(180, int(180 * (1.0 - t_land / 60.0))))
                self._ball_shadow.fill((0, 0, 0, 0))
                pygame.draw.ellipse(self._ball_shadow, (30, 10, 60, alpha), (0, 0, 40, 10))
                surface.blit(self._ball_shadow, (shadow_x - 20, GROUND_Y - 6))
            if -CN_PROJ_SIZE - 5 <= bx <= SCREEN_W + CN_PROJ_SIZE + 5:
                pygame.draw.circle(surface, (25, 15, 45), (bx, by), CN_PROJ_SIZE)
                pygame.draw.circle(surface, (65, 45, 90), (bx, by), CN_PROJ_SIZE - 2)
                pygame.draw.circle(surface, (110, 90, 135),
                                   (bx - CN_PROJ_SIZE // 3, by - CN_PROJ_SIZE // 3), 2)

        if self.dead and self._die_timer <= 0:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        dying = self.dead and self._die_timer > 0
        if dying:
            alpha = int(255 * self._die_timer / 36)
            tmp = pygame.Surface((self.W + 20, self.H + 10), pygame.SRCALPHA)
            self._draw_body(tmp, 10, 5)
            angle = (36 - self._die_timer) * (8 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 10, 6)

    def _draw_body(self, surface, sx, sy):
        t  = self._walk_t
        cx = sx + self.W // 2
        cy = sy + self.H // 5

        # Legs
        leg_swing = int(math.sin(t * 0.28) * 8) if self.vx != 0 else 0
        leg_y = sy + self.H - 20
        pygame.draw.rect(surface, CN_BODY, (sx + 3,           leg_y + leg_swing, 14, 20))
        pygame.draw.rect(surface, CN_BODY, (sx + self.W - 17, leg_y - leg_swing, 14, 20))

        # Stocky body
        pygame.draw.rect(surface, CN_BODY, (sx + 3, sy + self.H // 3, self.W - 6, self.H // 2))

        # Head
        pygame.draw.circle(surface, CN_HEAD, (cx, cy), 13)
        # Helmet stripe
        pygame.draw.arc(surface, CN_ARM, pygame.Rect(cx - 12, cy - 12, 24, 18), 0, math.pi, 5)
        # Eye
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, WHITE, (ex, cy + 2), 3)
        pygame.draw.circle(surface, (20, 10, 40), (ex + self.facing, cy + 2), 2)

        # Mortar tube — angled ~45° upward toward facing direction
        tube_base_x = cx + self.facing * 4
        tube_base_y = sy + self.H // 3 + 4
        tube_end_x  = tube_base_x + self.facing * 13
        tube_end_y  = tube_base_y - 13
        pygame.draw.line(surface, CN_ARM, (tube_base_x, tube_base_y),
                         (tube_end_x, tube_end_y), 6)
        pygame.draw.circle(surface, (40, 25, 70), (tube_end_x, tube_end_y), 5)


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
                if self.on_ground:  # preserve air velocity from pit-avoidance jumps
                    self.vx = math.copysign(self.SPEED, dx)
                self._walk_t += 1
            else:
                if self.on_ground:
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
# Bomber — explodes a short time after dying, damaging nearby players
# ---------------------------------------------------------------------------

class Bomber(Grunt):
    W, H      = E_W, E_H
    SPEED     = BOMBER_SPEED
    HP_MAX    = BOMBER_HP
    ATK_DMG   = BOMBER_ATK_DMG
    ATK_RANGE = BOMBER_RANGE
    ATK_CD    = 68
    HURT_DUR  = E_HURT_DUR
    SCORE     = BOMBER_SCORE
    DEATH_COL = BOMBER_BODY

    def __init__(self, x, y):
        super().__init__(x, y)
        self._fuse = 0
        self.pending_explosion = False

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        self.hp = max(0, self.hp - dmg)
        self.hurt_timer = max(self.HURT_DUR, stun)
        self.vx = kb_dir * 4.0
        self.vy = -2.5
        if self.hp == 0:
            self.dead = True
            self._fuse = BOMBER_FUSE
            self._die_timer = BOMBER_FUSE + 36   # fuse burns then death anim
            self._die_vx    = kb_dir * 1.5
            self._die_vy    = -2.0
        self._hit_flash = 5
        return True

    def update(self, players):
        if self.dead:
            if self._fuse > 0:
                self._fuse -= 1
                self._die_timer -= 1
                self._die_vx *= 0.94
                self.x += self._die_vx
                self.y = float(GROUND_Y - self.H)   # stay grounded while fuse burns
                self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
                if self._fuse == 0:
                    self.pending_explosion = True
                    self._die_vy = -5.5
                    self._die_vx = self._die_vx * 0.5
            elif self._die_timer > 0:
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
        Grunt.update(self, players)

    def draw(self, surface, cam_x):
        if self.dead:
            sx = int(self.x) - cam_x
            sy = int(self.y)
            if self._fuse > 0:
                if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
                    return
                self._draw_body(surface, sx, sy)
                # Red flashing glow — intensifies as fuse shortens
                if (self._fuse // 3) % 2 == 0:
                    intensity = int(60 + (1.0 - self._fuse / BOMBER_FUSE) * 160)
                    glow = pygame.Surface((self.W + 10, self.H + 6), pygame.SRCALPHA)
                    glow.fill((255, 40, 0, intensity))
                    surface.blit(glow, (sx - 5, sy - 3))
                return
            if self._die_timer <= 0:
                return
            if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
                return
            alpha = int(255 * self._die_timer / 36)
            tmp = pygame.Surface((self.W + 40, self.H + 20), pygame.SRCALPHA)
            self._draw_body(tmp, 20, 10)
            angle = (36 - self._die_timer) * (8 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return
        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 10, 6)

    def _draw_body(self, surface, sx, sy):
        t = self._walk_t
        leg_swing = int(math.sin(t * 0.28) * 8) if self.vx != 0 else 0
        leg_y = sy + self.H - 20
        pygame.draw.rect(surface, BOMBER_BODY, (sx + 3,           leg_y + leg_swing,  13, 20))
        pygame.draw.rect(surface, BOMBER_BODY, (sx + self.W - 16, leg_y - leg_swing,  13, 20))
        pygame.draw.rect(surface, BOMBER_BODY, (sx + 2, sy + 20, self.W - 4, self.H - 38))
        pygame.draw.rect(surface, (50, 105, 25), (sx + 2, sy + self.H - 38, self.W - 4, 8))

        # Barrel strapped to back
        bx = sx + self.W - 4 if self.facing == 1 else sx - 12
        pygame.draw.rect(surface, (40, 115, 20), (bx, sy + 22, 12, 26))
        pygame.draw.rect(surface, (60, 150, 30), (bx, sy + 22, 12,  5))
        pygame.draw.rect(surface, (60, 150, 30), (bx, sy + 42, 12,  5))
        # Fuse on top of barrel
        fuse_lit = (self._fuse // 4) % 2 == 0 if self._fuse > 0 else True
        fuse_col = (255, 200, 50) if fuse_lit else (180, 100, 20)
        pygame.draw.line(surface, fuse_col, (bx + 6, sy + 22), (bx + 6, sy + 14), 2)

        cx = sx + self.W // 2
        cy = sy + 12
        pygame.draw.circle(surface, BOMBER_HEAD, (cx, cy), 13)
        pygame.draw.arc(surface, (50, 130, 30),
                        pygame.Rect(cx - 13, cy - 13, 26, 20), 0, math.pi, 6)
        ex = cx + self.facing * 5
        pygame.draw.circle(surface, BLACK, (ex, cy + 2), 3)
        pygame.draw.circle(surface, WHITE, (ex + self.facing, cy + 1), 1)


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
        self._chalk_cd = TB_CHALK_CD
        self._rein_cd  = TB_REIN_CD
        self.pending_spawns = []  # list of world_x values for grunt spawns
        self.swing_text = ''      # 'SILENCE!' — read once by game.py

    def _emit_wave(self, wave_num):
        pass  # TeacherBoss uses pending_spawns for its own reinforcement mechanic

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
            sx = float(self.rect.centerx)
            self._chalk.append([sx, float(self.rect.centery - 10), vx, True, sx])
            self._chalk_cd = TB_CHALK_CD
            self.facing = 1 if dx > 0 else -1

        # Advance chalk projectiles  [wx, wy, vx, alive, spawn_x]
        for proj in self._chalk:
            if not proj[3]:
                continue
            proj[0] += proj[2]
            if abs(proj[0] - proj[4]) > TB_CHALK_RANGE or proj[0] < 0 or proj[0] > WORLD_W:
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
        self._hit_flash = 5
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
        self._spin_t    = 0
        self._spin_cd   = 60
        self._spin_angle = 0.0
        self._streak_surf = pygame.Surface((self.W, self.H - 30), pygame.SRCALPHA)
        self._spin_surf   = pygame.Surface((RB_SPIN_RAD * 2, RB_SPIN_RAD * 2), pygame.SRCALPHA)
        pygame.draw.circle(self._spin_surf, (100, 200, 255, 60),
                           (RB_SPIN_RAD, RB_SPIN_RAD), RB_SPIN_RAD)

    def _emit_wave(self, wave_num):
        pass  # RollerBoss relies on charge + spin; no minion waves

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
        self._hit_flash = 5
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
                self._streak_surf.fill((*RB_BODY, fade))
                surface.blit(self._streak_surf, (sxs, sy + 15))

        # Spin glow
        if self._spin_t > 0:
            surface.blit(self._spin_surf, (sx + self.W // 2 - RB_SPIN_RAD,
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


# ---------------------------------------------------------------------------
# FlyingEye — aerial minion; hovers above ground, swoops to melee-attack;
# immune to pits and lava (checked in game.py)
# ---------------------------------------------------------------------------

class FlyingEye(Grunt):
    W, H      = FE_W, FE_H
    SPEED     = FE_SPEED
    HP_MAX    = FE_HP
    ATK_DMG   = FE_ATK_DMG
    ATK_RANGE = FE_ATK_RANGE
    ATK_CD    = FE_ATK_CD
    HURT_DUR  = FE_HURT_DUR
    SCORE     = FE_SCORE
    DEATH_COL = FE_EYE_COL

    FLOAT_Y = FE_FLOAT_Y

    def __init__(self, x, y):
        super().__init__(x, y)
        self.y         = float(self.FLOAT_Y)
        self._wing_t   = 0
        self.on_ground = False
        self._spit_cd  = random.randint(FE_SPIT_CD // 2, FE_SPIT_CD)
        self._spits    = []   # [world_x, world_y, vx, vy, alive]
        self.pending_hits = []

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def can_attack(self, players):
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        dy = abs(target.rect.centery - self.rect.centery)
        if abs(dx) <= self.ATK_RANGE and dy < self.H + 40:
            self.atk_cd = self.ATK_CD
            return True, target
        return False, None

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        self.hp = max(0, self.hp - dmg)
        self.hurt_timer = max(self.HURT_DUR, stun)
        self.vx = kb_dir * 3.0
        self.vy = -3.5
        if self.hp == 0:
            self.dead = True
            self._die_timer = 36
            self._die_vx    = kb_dir * 3.5
            self._die_vy    = -5.0
        self._hit_flash = 5
        return True

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
                    self._die_vy *= -0.1
                self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
            return

        self._wing_t += 1
        self.pending_hits = []

        # Advance spits and check player collisions (always, even if no target)
        for s in self._spits:
            if not s[4]:
                continue
            s[0] += s[2]; s[1] += s[3]
            if s[0] < 0 or s[0] > WORLD_W or s[1] > GROUND_Y + 20:
                s[4] = False
                continue
            sr = pygame.Rect(int(s[0]) - 5, int(s[1]) - 5, 10, 10)
            for player in players:
                if not player.dead and sr.colliderect(player.rect):
                    self.pending_hits.append((player, FE_SPIT_DMG))
                    s[4] = False
                    break
        self._spits = [s for s in self._spits if s[4]]

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx

        if self.hurt_timer <= 0:
            if abs(dx) > self.ATK_RANGE + 10:
                self.vx = math.copysign(self.SPEED, dx)
                self.facing = 1 if dx > 0 else -1
            else:
                self.vx = 0.0
                self.facing = 1 if dx >= 0 else -1
            # Hover height: swoop toward player when close in x
            if abs(dx) <= self.ATK_RANGE * 2:
                target_y = float(target.rect.top - self.H // 2)
            else:
                target_y = float(self.FLOAT_Y)
            self.vy = (target_y - self.y) * 0.14

            # Spit projectile toward player
            if self._spit_cd > 0:
                self._spit_cd -= 1
            elif abs(dx) < FE_SPIT_RANGE:
                fx = float(self.rect.centerx)
                fy = float(self.rect.centery)
                tx = float(target.rect.centerx)
                ty = float(target.rect.centery)
                dist = math.hypot(tx - fx, ty - fy)
                if dist > 0:
                    ratio = FE_SPIT_SPD / dist
                    svx = (tx - fx) * ratio
                    svy = (ty - fy) * ratio
                else:
                    svx, svy = FE_SPIT_SPD * self.facing, 0.0
                self._spits.append([fx, fy, svx, svy, True])
                self._spit_cd = random.randint(int(FE_SPIT_CD * 0.70),
                                               int(FE_SPIT_CD * 1.35))
        else:
            self.vx *= 0.75
            self.vy *= 0.80

        self.x += self.vx
        self.y += self.vy
        self.y = max(20.0, min(self.y, float(GROUND_Y - self.H)))
        self.x = max(0.0, min(self.x, float(WORLD_W - self.W)))
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.atk_cd     > 0: self.atk_cd     -= 1

    def draw(self, surface, cam_x):
        if self.dead and self._die_timer <= 0:
            return
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if not (-self.W - 10 <= sx <= SCREEN_W + self.W + 10):
            return
        if self.hurt_timer > 0 and (self.hurt_timer // 3) % 2 == 1:
            return

        dying = self.dead and self._die_timer > 0
        if dying:
            alpha = int(255 * self._die_timer / 36)
            tmp = pygame.Surface((self.W + 20, self.H + 10), pygame.SRCALPHA)
            self._draw_body(tmp, 10, 5)
            angle = (36 - self._die_timer) * 10
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        # Draw spit blobs
        for s in self._spits:
            bx = int(s[0]) - cam_x
            by = int(s[1])
            if -10 <= bx <= SCREEN_W + 10:
                pygame.draw.circle(surface, (160, 255, 50), (bx, by), 6)
                pygame.draw.circle(surface, (50,  180, 20), (bx, by), 3)

        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX, self.W + 8, 5)

    def _draw_body(self, surface, sx, sy):
        t  = self._wing_t
        cx = sx + self.W // 2
        cy = sy + self.H // 2
        flap = int(math.sin(t * 0.35) * 14)

        # Wings
        pygame.draw.polygon(surface, FE_WING_COL, [
            (cx - 3, cy + 2), (cx - self.W, cy - 6 + flap), (cx - self.W + 5, cy + 8 + flap // 2)])
        pygame.draw.polygon(surface, FE_WING_COL, [
            (cx + 3, cy + 2), (cx + self.W, cy - 6 + flap), (cx + self.W - 5, cy + 8 + flap // 2)])
        pygame.draw.line(surface, (65, 35, 15),
                         (cx - 3, cy + 2), (cx - self.W + 5, cy - 2 + flap), 1)
        pygame.draw.line(surface, (65, 35, 15),
                         (cx + 3, cy + 2), (cx + self.W - 5, cy - 2 + flap), 1)

        # Body cluster
        pygame.draw.circle(surface, FE_EYE_COL, (cx, cy + 4), self.W // 5)

        # Giant eyeball
        pygame.draw.circle(surface, (245, 245, 255), (cx, cy - 3), self.W // 3)
        pygame.draw.circle(surface, (185, 40, 18),   (cx, cy - 3), self.W // 4)
        pygame.draw.circle(surface, BLACK,            (cx, cy - 3), self.W // 6)
        pygame.draw.circle(surface, WHITE,            (cx + 3, cy - 6), 3)

        # Dangling tentacles
        for i, ox in enumerate((-9, -3, 3, 9)):
            leg_len = 7 + int(abs(math.sin(t * 0.22 + i * 0.9)) * 5)
            base_y  = cy + self.H // 4
            pygame.draw.line(surface, FE_WING_COL,
                             (cx + ox, base_y), (cx + ox, base_y + leg_len), 1)


# ---------------------------------------------------------------------------
# Rocket — projectile fired by RocketBoss; consumed by game.py
# ---------------------------------------------------------------------------

class Rocket:
    W, H = 30, 10

    def __init__(self, x, y, vx, vy, dmg):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = float(vx)
        self.vy     = float(vy)
        self.dmg    = dmg
        self.alive  = True
        self._t     = 0
        self.facing = 1 if vx >= 0 else -1

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 15, int(self.y) - 8, 30, 16)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self._t += 1
        if self.x < -300 or self.x > WORLD_W + 300 or self.y > GROUND_Y + 60:
            self.alive = False

    def draw(self, surface, cam_x):
        if not self.alive:
            return
        sx = int(self.x) - cam_x
        if not (-80 <= sx <= SCREEN_W + 80):
            return
        sy = int(self.y)

        # Draw rocket pointing right on a temp surface, then rotate to match velocity
        tmp = pygame.Surface((54, 28), pygame.SRCALPHA)
        my = 14   # vertical center
        bx = 10   # body left edge (leaves room for tail fins)
        flame_r = 4 + int(abs(math.sin(self._t * 0.42)) * 4)
        pygame.draw.circle(tmp, (255, 200, 60), (bx, my), flame_r)
        pygame.draw.circle(tmp, (200, 80, 10),  (bx, my), max(1, flame_r - 2))
        pygame.draw.rect(tmp, (220, 80, 20), (bx, my - 5, 30, 10), border_radius=3)
        pygame.draw.polygon(tmp, (180, 55, 12), [(bx, my - 5), (bx - 6, my - 11), (bx, my)])
        pygame.draw.polygon(tmp, (180, 55, 12), [(bx, my + 5), (bx - 6, my + 11), (bx, my)])
        pygame.draw.polygon(tmp, (255, 150, 50), [(bx + 30, my - 5), (bx + 42, my), (bx + 30, my + 5)])

        angle_deg = -math.degrees(math.atan2(self.vy, self.vx))
        rotated = pygame.transform.rotate(tmp, angle_deg)
        surface.blit(rotated, rotated.get_rect(center=(sx, sy)))


# ---------------------------------------------------------------------------
# RocketBoss — Level 4 boss: rocket launcher (double volley in phase 2)
# ---------------------------------------------------------------------------

class RocketBoss(Boss):
    W, H       = ROKB_W, ROKB_H
    SPEED      = ROKB_SPEED
    HP_MAX     = ROKB_HP
    ATK_DMG    = ROKB_ATK_DMG
    ATK_RANGE  = ROKB_ATK_RANGE
    ATK_CD_VAL = ROKB_ATK_CD
    SCORE      = ROKB_SCORE
    DEATH_COL  = ROKB_BODY

    # No charge — boss keeps distance and uses rockets
    CHARGE_SPEED = 0
    CHARGE_DUR   = 0
    CHARGE_CD    = 9999
    CHARGE_DMG   = 0

    def __init__(self, x, y):
        super().__init__(x, y)
        self.pending_rockets = []      # consumed by game.py each frame
        self._rocket_cd      = random.randint(ROKB_ROCKET_CD // 3, ROKB_ROCKET_CD // 2)
        self.fire_text       = ''      # 'INCOMING!' — read once by game.py

    def _emit_wave(self, wave_num):
        pass  # RocketBoss uses rockets; no ground minion waves

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
            return True, target
        return False, None

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
            self._die_vx    = kb_dir * 2.5
            self._die_vy    = -6.0
        self._hit_flash = 5
        return True

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

        self.pending_rockets = []
        self.fire_text = ''
        self._eye_t += 1

        if not self._phase2 and self.phase2:
            self._phase2 = True

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx

        # Rocket volley — aim directly at target player
        if self._rocket_cd > 0:
            self._rocket_cd -= 1
        elif self.hurt_timer == 0 and abs(dx) > 70:
            self.facing = 1 if dx > 0 else -1
            fx = float(self.rect.centerx)
            fy = float(self.rect.centery - 10)
            tdx = float(target.rect.centerx) - fx
            tdy = float(target.rect.centery) - fy
            dist = math.hypot(tdx, tdy)
            if dist > 0:
                vx_r = tdx / dist * ROKB_ROCKET_SPD
                vy_r = tdy / dist * ROKB_ROCKET_SPD
            else:
                vx_r = float(self.facing) * ROKB_ROCKET_SPD
                vy_r = 0.0
            self.pending_rockets.append(Rocket(fx, fy, vx_r, vy_r, ROKB_ROCKET_DMG))
            if self.phase2:
                self.pending_rockets.append(Rocket(fx, fy + 16, vx_r, vy_r, ROKB_ROCKET_DMG))
            base = ROKB_ROCKET_CD if not self.phase2 else ROKB_ROCKET_CD // 2
            self._rocket_cd = random.randint(int(base * 0.65), int(base * 1.40))
            self.fire_text  = 'INCOMING!'

        # Keep medium-range standoff; retreat if player is too close
        if self.hurt_timer <= 0:
            if abs(dx) > self.ATK_RANGE * 2.5:
                speed = self.SPEED * (1.4 if self.phase2 else 1.0)
                self.vx = math.copysign(speed, dx)
                self.facing = 1 if dx > 0 else -1
                self._walk_t += 1
            elif abs(dx) < 110:
                self.vx = -math.copysign(self.SPEED * 0.8, dx)
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
        _hp_bar(surface, sx + self.W // 2, sy, self.hp, self.HP_MAX,
                self.W + 22, 9, boss=True)

    def _draw_body(self, surface, sx, sy):
        t  = self._walk_t
        cx = sx + self.W // 2
        cy = sy + 18
        p2 = self.phase2
        bc = (min(255, ROKB_BODY[0] + (40 if p2 else 0)), ROKB_BODY[1], ROKB_BODY[2])
        ac = ROKB_ARMOR

        # Legs
        leg_sw = int(math.sin(t * 0.22) * 10) if self.vx != 0 else 0
        leg_y  = sy + self.H - 28
        pygame.draw.rect(surface, bc, (sx + 6,           leg_y + leg_sw, 18, 28))
        pygame.draw.rect(surface, ac, (sx + 6,           leg_y + leg_sw, 18, 10))
        pygame.draw.rect(surface, bc, (sx + self.W - 24, leg_y - leg_sw, 18, 28))
        pygame.draw.rect(surface, ac, (sx + self.W - 24, leg_y - leg_sw, 18, 10))

        # Torso
        pygame.draw.rect(surface, bc, (sx + 3, sy + 30, self.W - 6, self.H - 56))
        pygame.draw.rect(surface, ac, (sx + 3, sy + 30, self.W - 6, 24))

        # Shoulder pauldrons
        pygame.draw.rect(surface, ac, (sx - 8,           sy + 28, 20, 26))
        pygame.draw.rect(surface, ac, (sx + self.W - 12, sy + 28, 20, 26))

        # Rocket launcher on firing shoulder
        lx = sx + self.W - 2 if self.facing == 1 else sx - 24
        pygame.draw.rect(surface, ROKB_LAUNCHER_COL, (lx, sy + 20, 24, 14))
        # Barrel mouth glow
        mouth_x = lx + 24 if self.facing == 1 else lx
        mouth_glow = (255, 140, 40) if p2 else (180, 100, 30)
        pygame.draw.circle(surface, mouth_glow, (mouth_x, sy + 27), 5)
        pygame.draw.circle(surface, (40, 40, 50), (mouth_x, sy + 27), 3)
        # Scope
        pygame.draw.rect(surface, (75, 75, 85), (lx + 5, sy + 14, 10, 6))

        # Head
        pygame.draw.circle(surface, ROKB_HEAD, (cx, cy), 19)
        # Helmet dome
        pygame.draw.arc(surface, ac, pygame.Rect(cx - 18, cy - 18, 36, 28), 0, math.pi, 9)
        # Visor
        visor_col = (255, 60, 20) if p2 else (200, 100, 30)
        pygame.draw.rect(surface, visor_col, (cx - 14, cy - 5, 28, 10))
        pygame.draw.rect(surface, (25, 15, 8), (cx - 14, cy - 5, 28, 10), 1)
        # Eyes
        pulse = int(abs(math.sin(self._eye_t * (0.16 if p2 else 0.08))) * 80)
        eye_col = (220 + pulse // 3, 60, 10)
        pygame.draw.circle(surface, eye_col, (cx - 6, cy + 1), 4)
        pygame.draw.circle(surface, eye_col, (cx + 6, cy + 1), 4)


# ---------------------------------------------------------------------------
# ToyBlock — projectile thrown by DoriBoss
# ---------------------------------------------------------------------------

class ToyBlock:
    W, H = 22, 22
    _COLS = [NURSERY_BLOCK_R, NURSERY_BLOCK_B, NURSERY_BLOCK_Y, NURSERY_BLOCK_G]

    def __init__(self, x, y, facing, speed, dmg, vy=0.0):
        self.x      = float(x)
        self.y      = float(y)
        self.facing = facing
        self.speed  = float(speed)
        self.dmg    = dmg
        self.alive  = True
        self._t     = 0
        self._col   = self._COLS[int(x) % len(self._COLS)]
        self._vy    = vy
        # Pre-build base surface; cache rotated frames by angle index (9° steps → 40 angles)
        _base = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(_base, self._col, (0, 0, self.W, self.H))
        darker = tuple(max(0, c - 50) for c in self._col)
        pygame.draw.rect(_base, darker, (0, 0, self.W, self.H), 3)
        self._rot_frames = [pygame.transform.rotate(_base, a * 9) for a in range(40)]

    @property
    def rect(self):
        rx = int(self.x) if self.facing > 0 else int(self.x) - self.W
        return pygame.Rect(rx, int(self.y), self.W, self.H)

    def update(self):
        self.x += self.speed * self.facing
        self.y += self._vy
        self._vy += GRAVITY * 0.45   # gentle arc
        self._t += 1
        if not (0 <= self.x <= WORLD_W) or self.y > GROUND_Y + 40:
            self.alive = False

    def draw(self, surface, cam_x):
        sx = int(self.x) - cam_x
        if not (-50 <= sx <= SCREEN_W + 50):
            return
        ry = int(self.y)
        rotated = self._rot_frames[self._t % 40]
        rr = rotated.get_rect(center=(sx, ry + self.H // 2))
        surface.blit(rotated, rr)


# ---------------------------------------------------------------------------
# DoriBoss — Level 5 final boss: giant, powerful, blonde baby
# ---------------------------------------------------------------------------

class DoriBoss(Boss):
    W, H       = DORI_W, DORI_H
    SPEED      = DORI_SPEED
    HP_MAX     = DORI_HP
    ATK_DMG    = DORI_ATK_DMG
    ATK_RANGE  = DORI_ATK_RANGE
    ATK_CD_VAL = DORI_ATK_CD
    SCORE      = DORI_SCORE
    DEATH_COL  = DORI_SKIN

    # Disable parent charge — Dori uses own tantrum charge
    CHARGE_SPEED = 0
    CHARGE_DUR   = 0
    CHARGE_CD    = 9999
    CHARGE_DMG   = 0

    def __init__(self, x, y):
        super().__init__(x, y)
        self.pending_blocks = []   # consumed by game.py
        self.pending_hits   = []   # consumed by game.py
        self.block_text     = ''
        self._block_cd      = DORI_BLOCK_CD // 2
        self._pound_cd      = DORI_POUND_CD // 2
        self._pounding      = False
        self._tantrum_cd    = DORI_CHARGE_CD // 2
        self._tantrum_t     = 0    # frames remaining in current charge
        self._tantrum_dir   = 0

    def _emit_wave(self, wave_num):
        bx = int(self.x)
        left_x  = max(50,           bx - 340)
        right_x = min(WORLD_W - 50, bx + 340)
        if wave_num == 1:
            self.pending_wave_spawns = [(left_x, 'grunt'), (right_x, 'grunt')]
        elif wave_num == 2:
            # Dori summons her flying minions at half HP
            self.pending_wave_spawns = [(left_x, 'eye'), (right_x, 'eye'),
                                        (bx - 60, 'eye')]
        else:
            self.pending_wave_spawns = [(left_x, 'grunt'), (right_x, 'grunt'),
                                        (left_x + 60, 'eye'), (bx, 'grunt')]

    def can_attack(self, players):
        if self.dead or self.hurt_timer > 0 or self.atk_cd > 0:
            return False, None
        if self._tantrum_t > 0:
            return False, None
        candidates = _nearest_player(players)
        if not candidates:
            return False, None
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        if abs(dx) <= self.ATK_RANGE and abs(target.rect.centery - self.rect.centery) < self.H:
            self.atk_cd = self.ATK_CD_VAL
            return True, target
        return False, None

    def take_damage(self, dmg, kb_dir=1, stun=0):
        if self.dead:
            return False
        self.hp = max(0, self.hp - dmg)
        if self._tantrum_t <= 0:
            self.hurt_timer = max(10, stun // 3)
            self.vx = kb_dir * 1.0
            self.vy = -0.6
        if self.hp == 0:
            self.dead = True
            self._die_timer = 60
            self._die_vx    = kb_dir * 2.0
            self._die_vy    = -7.0
        self._hit_flash = 5
        return True

    def update(self, players):
        if self.dead:
            if self._die_timer > 0:
                self._die_timer -= 1
                self._die_vx *= 0.90
                self._die_vy += GRAVITY
                self.x += self._die_vx
                self.y += self._die_vy
                ground_y = float(GROUND_Y - self.H)
                if self.y >= ground_y:
                    self.y = ground_y
                    self._die_vy *= -0.15
            return

        self.pending_blocks = []
        self.pending_hits   = []
        self.block_text = ''
        self._eye_t += 1

        # --- Mid-fight minion waves ---
        hp_pct = self.hp / self.HP_MAX
        if 'w1' not in self._wave_spawned and hp_pct <= 0.75:
            self._wave_spawned.add('w1'); self._emit_wave(1)
        if 'w2' not in self._wave_spawned and hp_pct <= 0.50:
            self._wave_spawned.add('w2'); self._emit_wave(2)
        if 'w3' not in self._wave_spawned and hp_pct <= 0.25:
            self._wave_spawned.add('w3'); self._emit_wave(3)

        if not self._phase2 and self.phase2:
            self._phase2 = True

        candidates = _nearest_player(players)
        if not candidates:
            return
        target = min(candidates, key=lambda p: abs(p.rect.centerx - self.rect.centerx))
        dx = target.rect.centerx - self.rect.centerx
        phase2 = self.phase2

        # --- Timers ---
        if self._block_cd   > 0: self._block_cd   -= 1
        if self._pound_cd   > 0: self._pound_cd   -= 1
        if self._tantrum_cd > 0: self._tantrum_cd -= 1
        if self.hurt_timer  > 0: self.hurt_timer  -= 1
        if self.atk_cd      > 0: self.atk_cd      -= 1

        prev_on_ground = self.on_ground

        # --- Tantrum charge (phase 2) ---
        if self._tantrum_t > 0:
            self._tantrum_t -= 1
            self.vx = self._tantrum_dir * DORI_CHARGE_SPD
            self.facing = self._tantrum_dir
            self._walk_t += 1
            if self._tantrum_t == 0:
                self.vx = 0.0
        elif self.hurt_timer <= 0:
            # --- Block throw ---
            if self._block_cd == 0 and abs(dx) < 550:
                self._block_cd = DORI_BLOCK_CD2 if phase2 else DORI_BLOCK_CD
                f  = 1 if dx > 0 else -1
                bx = float(self.rect.centerx)
                by = float(self.y + self.H * 0.6)   # waist height — hits player level
                self.pending_blocks.append(
                    ToyBlock(bx, by, f, DORI_BLOCK_SPD, DORI_BLOCK_DMG,
                             vy=random.uniform(-2.0, 0.5)))
                if phase2:
                    self.pending_blocks.append(
                        ToyBlock(bx, by, f, DORI_BLOCK_SPD + 1, DORI_BLOCK_DMG,
                                 vy=random.uniform(-3.0, -0.5)))
                    self.pending_blocks.append(
                        ToyBlock(bx, by, f, DORI_BLOCK_SPD - 1, DORI_BLOCK_DMG,
                                 vy=random.uniform(-1.0, 1.5)))
                self.block_text = 'WAAAH!!' if phase2 else 'WAAAH!'

            # --- Ground pound ---
            if self._pound_cd == 0 and self.on_ground and abs(dx) < 350:
                self._pound_cd = DORI_POUND_CD
                self.vy = -13.0
                self.on_ground = False
                self._pounding = True

            # --- Phase 2 tantrum charge ---
            if phase2 and self._tantrum_cd == 0 and self.on_ground:
                self._tantrum_cd = DORI_CHARGE_CD
                self._tantrum_dir = 1 if dx > 0 else -1
                self._tantrum_t = DORI_CHARGE_DUR

            # --- Movement AI ---
            standoff = 120
            if abs(dx) > standoff + 10:
                spd = self.SPEED * (1.3 if phase2 else 1.0)
                self.vx = math.copysign(spd, dx)
                self.facing = 1 if dx > 0 else -1
                self._walk_t += 1
            elif abs(dx) < standoff - 10:
                self.vx = -math.copysign(self.SPEED * 0.5, dx)
                self._walk_t += 1
            else:
                self.vx = 0.0
                self.facing = 1 if dx >= 0 else -1
        else:
            self.vx *= 0.75

        # --- Physics ---
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

        # --- Ground pound landing shockwave ---
        if self._pounding and not prev_on_ground and self.on_ground:
            self._pounding = False
            self._pound_cd = DORI_POUND_CD
            scx = self.rect.centerx
            for p in candidates:
                if abs(p.rect.centerx - scx) < 160:
                    self.pending_hits.append((p, DORI_POUND_DMG))

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
            alpha = int(255 * self._die_timer / 60)
            tmp = pygame.Surface((self.W + 60, self.H + 30), pygame.SRCALPHA)
            self._draw_body(tmp, 30, 15)
            angle = (60 - self._die_timer) * (5 * (1 if self._die_vx >= 0 else -1))
            rotated = pygame.transform.rotate(tmp, -angle)
            rr = rotated.get_rect(center=(sx + self.W // 2, sy + self.H // 2))
            rotated.set_alpha(alpha)
            surface.blit(rotated, rr)
            return

        self._draw_body(surface, sx, sy)
        _hp_bar(surface, sx + self.W // 2, sy - 10, self.hp, self.HP_MAX,
                self.W + 28, 11, boss=True)

    def _draw_body(self, surface, sx, sy):
        t   = self._walk_t
        cx  = sx + self.W // 2
        p2  = self.phase2
        sk  = DORI_SKIN
        skd = DORI_SKIN_DARK
        anger = p2  # face is angrier in phase 2

        # --- Legs (chubby stumps) ---
        leg_sw = int(math.sin(t * 0.22) * 8) if self.vx != 0 else 0
        leg_y  = sy + self.H - 32
        # left leg
        pygame.draw.rect(surface, sk,  (sx + 10, leg_y + leg_sw,  26, 32))
        pygame.draw.rect(surface, skd, (sx + 10, leg_y + leg_sw,  26, 8), 0)
        # right leg
        pygame.draw.rect(surface, sk,  (sx + self.W - 36, leg_y - leg_sw, 26, 32))
        pygame.draw.rect(surface, skd, (sx + self.W - 36, leg_y - leg_sw, 26, 8), 0)
        # tiny feet
        pygame.draw.ellipse(surface, sk,  (sx + 6,  leg_y + leg_sw  + 24, 34, 14))
        pygame.draw.ellipse(surface, sk,  (sx + self.W - 40, leg_y - leg_sw + 24, 34, 14))

        # --- Diaper ---
        diaper_y = sy + self.H - 52
        pygame.draw.rect(surface, DORI_DIAPER, (sx + 4, diaper_y, self.W - 8, 30))
        # diaper wrinkle lines
        pygame.draw.line(surface, (200, 200, 215), (cx, diaper_y + 4), (cx, diaper_y + 26), 2)
        # safety pin
        pygame.draw.circle(surface, DORI_PIN, (cx - 10, diaper_y + 8), 4)
        pygame.draw.circle(surface, (100, 80, 130), (cx - 10, diaper_y + 8), 2)

        # --- Torso (chubby round belly) ---
        torso_y = sy + self.H - 88
        pygame.draw.ellipse(surface, sk, (sx + 2, torso_y, self.W - 4, 50))
        # belly button
        pygame.draw.circle(surface, skd, (cx, torso_y + 30), 4)

        # --- Arms (stumpy, sticking out) ---
        arm_y = torso_y + 12
        arm_swing = int(math.sin(t * 0.28) * 10)
        # left arm
        pygame.draw.ellipse(surface, sk,  (sx - 18, arm_y + arm_swing, 24, 34))
        # right arm
        pygame.draw.ellipse(surface, sk,  (sx + self.W - 6, arm_y - arm_swing, 24, 34))
        # fists
        pygame.draw.circle(surface, skd, (sx - 6,           arm_y + arm_swing + 30), 10)
        pygame.draw.circle(surface, skd, (sx + self.W + 6,  arm_y - arm_swing + 30), 10)

        # --- Neck ---
        pygame.draw.rect(surface, sk, (cx - 12, torso_y - 14, 24, 18))

        # --- Head (large round) ---
        head_r = 33
        head_cy = sy + 42
        head_col = (min(255, sk[0] + (20 if anger else 0)), sk[1], sk[2]) if not anger else (
            min(255, sk[0] + 30), max(0, sk[1] - 30), max(0, sk[2] - 20))
        pygame.draw.circle(surface, head_col, (cx, head_cy), head_r)
        # chin bulge
        pygame.draw.ellipse(surface, head_col, (cx - 20, head_cy + 20, 40, 20))

        # --- Blush ---
        blush_a = 140 if not anger else 200
        blush_surf = pygame.Surface((28, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(blush_surf, (*DORI_BLUSH, blush_a), (0, 0, 28, 14))
        surface.blit(blush_surf, (cx - 34, head_cy + 8))
        surface.blit(blush_surf, (cx + 6,  head_cy + 8))

        # --- Eyes ---
        eye_lx = cx - 14
        eye_rx = cx + 14
        eye_y  = head_cy - 4
        # whites
        pygame.draw.ellipse(surface, (255, 255, 255), (eye_lx - 9, eye_y - 9, 18, 18))
        pygame.draw.ellipse(surface, (255, 255, 255), (eye_rx - 9, eye_y - 9, 18, 18))
        # iris
        iris_col = DORI_EYE_IRIS if not anger else (200, 60, 30)
        pygame.draw.circle(surface, iris_col, (eye_lx, eye_y), 7)
        pygame.draw.circle(surface, iris_col, (eye_rx, eye_y), 7)
        # pupil
        pygame.draw.circle(surface, (10, 10, 20), (eye_lx, eye_y), 4)
        pygame.draw.circle(surface, (10, 10, 20), (eye_rx, eye_y), 4)
        # shine
        pygame.draw.circle(surface, (255, 255, 255), (eye_lx - 2, eye_y - 2), 2)
        pygame.draw.circle(surface, (255, 255, 255), (eye_rx - 2, eye_y - 2), 2)
        # eyebrows (angry in p2)
        brow_dy = -4 if not anger else -8
        inner_dy = 0 if not anger else 5
        pygame.draw.line(surface, (80, 55, 20),
                         (eye_lx - 8, eye_y + brow_dy - inner_dy),
                         (eye_lx + 8, eye_y + brow_dy), 3)
        pygame.draw.line(surface, (80, 55, 20),
                         (eye_rx - 8, eye_y + brow_dy),
                         (eye_rx + 8, eye_y + brow_dy - inner_dy), 3)

        # --- Mouth ---
        if not anger:
            # open baby smile
            pygame.draw.arc(surface, (180, 60, 70),
                            pygame.Rect(cx - 14, head_cy + 8, 28, 18),
                            math.pi, 2 * math.pi, 3)
        else:
            # crying/screaming open mouth
            pygame.draw.ellipse(surface, (180, 50, 60), (cx - 14, head_cy + 8, 28, 18))
            pygame.draw.ellipse(surface, (50, 10, 10),  (cx - 10, head_cy + 12, 20, 12))
            # tears
            tear_t = self._eye_t % 30
            tear_y = eye_y + 10 + (tear_t * 2 % 22)
            pygame.draw.ellipse(surface, (100, 160, 255), (eye_lx - 3, tear_y, 6, 9))
            pygame.draw.ellipse(surface, (100, 160, 255), (eye_rx - 3, tear_y, 6, 9))

        # --- Hair (blonde wisps) ---
        hair_col = DORI_HAIR
        # central tuft
        pygame.draw.polygon(surface, hair_col, [
            (cx,      head_cy - head_r + 2),
            (cx - 8,  head_cy - head_r - 14),
            (cx + 8,  head_cy - head_r - 14),
        ])
        # left wisp
        pygame.draw.polygon(surface, hair_col, [
            (cx - 14, head_cy - head_r + 4),
            (cx - 24, head_cy - head_r - 10),
            (cx - 8,  head_cy - head_r - 8),
        ])
        # right wisp
        pygame.draw.polygon(surface, hair_col, [
            (cx + 14, head_cy - head_r + 4),
            (cx + 24, head_cy - head_r - 10),
            (cx + 8,  head_cy - head_r - 8),
        ])
        # curl tip circles
        pygame.draw.circle(surface, hair_col, (cx,      head_cy - head_r - 14), 5)
        pygame.draw.circle(surface, hair_col, (cx - 16, head_cy - head_r - 10), 4)
        pygame.draw.circle(surface, hair_col, (cx + 16, head_cy - head_r - 10), 4)

        # --- Ground pound glow effect ---
        if self._pounding:
            glow_a = int(abs(math.sin(self._eye_t * 0.3)) * 160 + 60)
            glow = pygame.Surface((self.W + 40, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 180, 50, glow_a), (0, 0, self.W + 40, 20))
            surface.blit(glow, (sx - 20, sy + self.H - 10))
