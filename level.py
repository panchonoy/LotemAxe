import random
import math
import pygame
from settings import *
from enemy import Grunt, Heavy, Boss, Thrower, Jumper, Healer, TeacherBoss, RollerBoss


class Level:
    """Manages the background scenery and enemy spawn triggers."""

    def __init__(self, level_num=1):
        self.level_num    = level_num
        self.swarm_active = False   # set True when swarm triggers; game.py reads + resets
        if level_num == 1:
            spawns = SPAWNS
        elif level_num == 2:
            spawns = SPAWNS_L2
        else:
            spawns = SPAWNS_L3
        self._pending = list(spawns)
        self.boss_triggered = False

        if level_num == 1:
            self.pits      = list(PITS_L1)
            self.platforms = list(PLATFORMS_L1)
            self.lava      = list(LAVA_L1)
        elif level_num == 2:
            self.pits      = list(PITS_L2)
            self.platforms = list(PLATFORMS_L2)
            self.lava      = list(LAVA_L2)
        else:
            self.pits      = list(PITS_L3)
            self.platforms = list(PLATFORMS_L3)
            self.lava      = list(LAVA_L3)

        rng = random.Random(42 + level_num)

        if level_num == 3:
            # City/skate park sky
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(CITY_SKY_TOP[0] + (CITY_SKY_BOT[0] - CITY_SKY_TOP[0]) * t)
                g = int(CITY_SKY_TOP[1] + (CITY_SKY_BOT[1] - CITY_SKY_TOP[1]) * t)
                b = int(CITY_SKY_TOP[2] + (CITY_SKY_BOT[2] - CITY_SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))
            bg_range_b = int(WORLD_W * 0.70 + SCREEN_W)
            self._buildings = [
                (rng.randint(0, bg_range_b),
                 rng.randint(80, 240),    # height
                 rng.randint(50, 120),    # width
                 rng.randint(0, 40))      # window rows
                for _ in range(60)
            ]
        elif level_num == 1:
            # Mountains
            bg_range_m = int(WORLD_W * 0.22 + SCREEN_W)
            self._mountains = [
                (rng.randint(0, bg_range_m),
                 rng.randint(180, 310),
                 rng.randint(100, 220))
                for _ in range(50)
            ]
            # Trees
            bg_range_t = int(WORLD_W * 0.60 + SCREEN_W)
            self._trees = [
                (rng.randint(0, bg_range_t), rng.randint(55, 105))
                for _ in range(80)
            ]
            # Sky gradient
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
                g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
                b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))
        else:
            # Cave: stalactites + torches
            bg_range_s = int(WORLD_W * 0.70 + SCREEN_W)
            self._stalactites = [
                (rng.randint(0, bg_range_s),
                 rng.randint(20, 90))   # drop length
                for _ in range(120)
            ]
            bg_range_tor = int(WORLD_W * 0.80 + SCREEN_W)
            self._torches = [
                rng.randint(0, bg_range_tor)
                for _ in range(40)
            ]
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(CAVE_SKY_TOP[0] + (CAVE_SKY_BOT[0] - CAVE_SKY_TOP[0]) * t)
                g = int(CAVE_SKY_TOP[1] + (CAVE_SKY_BOT[1] - CAVE_SKY_TOP[1]) * t)
                b = int(CAVE_SKY_TOP[2] + (CAVE_SKY_BOT[2] - CAVE_SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))

        self._torch_t = 0  # flicker timer

    # ------------------------------------------------------------------ spawn
    def update(self, camera_x):
        """Return a list of new Enemy instances whose trigger has been passed."""
        new_enemies = []
        remaining = []
        for trigger_x, spawn_list in self._pending:
            if camera_x >= trigger_x:
                has_regular = False
                for wx, kind in spawn_list:
                    if kind == 'grunt':
                        new_enemies.append(Grunt(wx, GROUND_Y - Grunt.H))
                        has_regular = True
                    elif kind == 'heavy':
                        new_enemies.append(Heavy(wx, GROUND_Y - Heavy.H))
                        has_regular = True
                    elif kind == 'thrower':
                        new_enemies.append(Thrower(wx, GROUND_Y - Thrower.H))
                        has_regular = True
                    elif kind == 'jumper':
                        new_enemies.append(Jumper(wx, GROUND_Y - Jumper.H))
                        has_regular = True
                    elif kind == 'healer':
                        new_enemies.append(Healer(wx, GROUND_Y - Healer.H))
                        has_regular = True
                    elif kind == 'swarm':
                        new_enemies += self._build_swarm(wx, camera_x)
                        self.swarm_active = True
                    elif kind == 'boss':
                        if self.level_num == 2:
                            new_enemies.append(TeacherBoss(wx, GROUND_Y - TeacherBoss.H))
                        elif self.level_num == 3:
                            new_enemies.append(RollerBoss(wx, GROUND_Y - RollerBoss.H))
                        else:
                            new_enemies.append(Boss(wx, GROUND_Y - Boss.H))
                        self.boss_triggered = True

                # Rear flank: spawn 1–2 enemies from behind for regular groups
                if has_regular:
                    flank_x = max(0, camera_x - random.randint(80, 200))
                    new_enemies.append(Grunt(flank_x, GROUND_Y - Grunt.H))
                    if self.level_num >= 2:
                        flank_x2 = max(0, camera_x - random.randint(160, 300))
                        flank_cls = Heavy if self.level_num == 2 else Jumper
                        new_enemies.append(flank_cls(flank_x2, GROUND_Y - flank_cls.H))
            else:
                remaining.append((trigger_x, spawn_list))
        self._pending = remaining
        return new_enemies

    def spawn_grunt(self, wx):
        """Spawn a single grunt — used by TeacherBoss reinforcements."""
        return Grunt(wx, GROUND_Y - Grunt.H)

    def _build_swarm(self, wx, camera_x=0):
        """Build the swarm wave — enemies from BOTH sides (left flank + right)."""
        # Left-flank enemies spawn behind the camera and approach from the left
        lx = max(0, camera_x - 220)

        if self.level_num == 1:
            # 5 left-flank + 7 right = 12 enemies
            return [
                # Left flank (behind player)
                Grunt(lx,        GROUND_Y - Grunt.H),
                Grunt(lx + 55,   GROUND_Y - Grunt.H),
                Heavy(lx + 110,  GROUND_Y - Heavy.H),
                Grunt(lx + 165,  GROUND_Y - Grunt.H),
                Grunt(lx + 220,  GROUND_Y - Grunt.H),
                # Right flank (ahead of player)
                Grunt(wx,        GROUND_Y - Grunt.H),
                Heavy(wx + 60,   GROUND_Y - Heavy.H),
                Grunt(wx + 125,  GROUND_Y - Grunt.H),
                Jumper(wx + 185, GROUND_Y - Jumper.H),
                Grunt(wx + 250,  GROUND_Y - Grunt.H),
                Heavy(wx + 315,  GROUND_Y - Heavy.H),
                Grunt(wx + 380,  GROUND_Y - Grunt.H),
            ]
        elif self.level_num == 2:
            # 6 left-flank + 9 right = 15 enemies — even more for L2!
            return [
                # Left flank
                Jumper(lx,        GROUND_Y - Jumper.H),
                Heavy(lx + 65,    GROUND_Y - Heavy.H),
                Grunt(lx + 130,   GROUND_Y - Grunt.H),
                Healer(lx + 195,  GROUND_Y - Healer.H),
                Jumper(lx + 260,  GROUND_Y - Jumper.H),
                Heavy(lx + 325,   GROUND_Y - Heavy.H),
                # Right flank
                Heavy(wx,         GROUND_Y - Heavy.H),
                Jumper(wx + 65,   GROUND_Y - Jumper.H),
                Thrower(wx + 135, GROUND_Y - Thrower.H),
                Heavy(wx + 205,   GROUND_Y - Heavy.H),
                Grunt(wx + 270,   GROUND_Y - Grunt.H),
                Jumper(wx + 335,  GROUND_Y - Jumper.H),
                Heavy(wx + 400,   GROUND_Y - Heavy.H),
                Thrower(wx + 465, GROUND_Y - Thrower.H),
                Jumper(wx + 530,  GROUND_Y - Jumper.H),
            ]
        else:
            # 5 left-flank + 8 right = 13 enemies — chaotic mix
            return [
                # Left flank
                Thrower(lx,        GROUND_Y - Thrower.H),
                Jumper(lx + 65,    GROUND_Y - Jumper.H),
                Heavy(lx + 130,    GROUND_Y - Heavy.H),
                Thrower(lx + 195,  GROUND_Y - Thrower.H),
                Jumper(lx + 260,   GROUND_Y - Jumper.H),
                # Right flank
                Jumper(wx,         GROUND_Y - Jumper.H),
                Thrower(wx + 60,   GROUND_Y - Thrower.H),
                Heavy(wx + 125,    GROUND_Y - Heavy.H),
                Jumper(wx + 190,   GROUND_Y - Jumper.H),
                Thrower(wx + 255,  GROUND_Y - Thrower.H),
                Heavy(wx + 320,    GROUND_Y - Heavy.H),
                Jumper(wx + 385,   GROUND_Y - Jumper.H),
                Grunt(wx + 450,    GROUND_Y - Grunt.H),
            ]

    # ------------------------------------------------------------------ draw
    def draw_background(self, surface, camera_x):
        self._torch_t += 1
        surface.blit(self._sky, (0, 0))

        if self.level_num == 1:
            self._draw_bg_l1(surface, camera_x)
        elif self.level_num == 2:
            self._draw_bg_l2(surface, camera_x)
        else:
            self._draw_bg_l3(surface, camera_x)

        self._draw_lava(surface, camera_x)
        self._draw_platforms(surface, camera_x)
        self._draw_pits(surface, camera_x)

    def _draw_bg_l1(self, surface, camera_x):
        for bg_x, peak_y, mw in self._mountains:
            sx = bg_x - int(camera_x * 0.22)
            if -mw <= sx <= SCREEN_W + mw:
                pts = [(sx,        GROUND_Y - 15),
                       (sx + mw//2, peak_y),
                       (sx + mw,   GROUND_Y - 15)]
                pygame.draw.polygon(surface, MOUNTAIN, pts)

        for bg_x, th in self._trees:
            sx = bg_x - int(camera_x * 0.60)
            if -60 <= sx <= SCREEN_W + 60:
                pygame.draw.rect(surface, TRUNK_COL, (sx - 5, GROUND_Y - th, 10, th))
                pygame.draw.circle(surface, TREE_COL, (sx, GROUND_Y - th - 10), 22)
                pygame.draw.circle(surface, TREE_COL, (sx, GROUND_Y - th - 24), 16)

        pygame.draw.rect(surface, GROUND_COL,
                         (0, GROUND_Y + 10, SCREEN_W, SCREEN_H - GROUND_Y - 10))
        pygame.draw.rect(surface, GRASS_COL, (0, GROUND_Y, SCREEN_W, 14))
        pygame.draw.rect(surface, (60, 130, 44), (0, GROUND_Y, SCREEN_W, 4))

    def _draw_platforms(self, surface, camera_x):
        stone = (90, 80, 65) if self.level_num == 1 else (58, 48, 72)
        top   = (120, 110, 90) if self.level_num == 1 else (78, 65, 95)
        bot   = (60,  52,  42) if self.level_num == 1 else (40, 32, 52)
        col   = (80,  70,  55) if self.level_num == 1 else (50, 40, 62)
        for wx, wy, pw in self.platforms:
            sx = wx - camera_x
            if sx + pw < 0 or sx > SCREEN_W:
                continue
            pygame.draw.rect(surface, stone, (sx,     wy,      pw, 18))
            pygame.draw.rect(surface, top,   (sx,     wy,      pw,  5))
            pygame.draw.rect(surface, bot,   (sx,     wy + 14, pw,  4))
            # Support column
            cx2 = sx + pw // 2 - 8
            pygame.draw.rect(surface, col, (cx2, wy + 18, 16, GROUND_Y - wy - 18))

    def _draw_lava(self, surface, camera_x):
        t = self._torch_t
        for lx1, lx2 in self.lava:
            sx1 = lx1 - camera_x
            sx2 = lx2 - camera_x
            if sx2 <= 0 or sx1 >= SCREEN_W:
                continue
            x1c = max(0, sx1)
            x2c = min(SCREEN_W, sx2)
            w   = x2c - x1c
            # Base lava slab
            pygame.draw.rect(surface, (200, 60, 5),   (x1c, GROUND_Y - 2, w, 16))
            pygame.draw.rect(surface, (240, 100, 20),  (x1c, GROUND_Y - 2, w,  6))
            # Animated bubbles
            flicker = int(abs(math.sin(t * 0.13)) * 5)
            for bx in range(x1c + 8, x2c - 4, 20):
                bh = 5 + flicker + int(abs(math.sin(t * 0.09 + bx * 0.05)) * 4)
                pygame.draw.ellipse(surface, (255, 160, 40),
                                    (bx - 6, GROUND_Y - 3 - bh, 12, bh + 4))
            # Glowing edge at top
            pygame.draw.rect(surface, (255, 200, 60), (x1c, GROUND_Y - 3, w, 2))
            # Yellow warning stripe on left/right approach
            for ex in (sx1 - 8, sx2 + 2):
                if 0 <= ex <= SCREEN_W - 6:
                    for iy in range(GROUND_Y - 8, GROUND_Y + 14, 6):
                        stripe_col = (255, 220, 0) if (iy // 6) % 2 == 0 else (40, 40, 40)
                        pygame.draw.rect(surface, stripe_col, (ex, iy, 6, 6))

    def _draw_pits(self, surface, camera_x):
        for pit_x1, pit_x2 in self.pits:
            sx1 = pit_x1 - camera_x
            sx2 = pit_x2 - camera_x
            if sx2 <= 0 or sx1 >= SCREEN_W:
                continue
            x1c = max(0, sx1)
            x2c = min(SCREEN_W, sx2)
            # Dark abyss overpaints the ground strip
            pygame.draw.rect(surface, (12, 8, 4),
                             (x1c, GROUND_Y, x2c - x1c, SCREEN_H - GROUND_Y))
            pygame.draw.line(surface, (100, 65, 20), (sx1, GROUND_Y), (sx1, SCREEN_H), 3)
            pygame.draw.line(surface, (100, 65, 20), (sx2, GROUND_Y), (sx2, SCREEN_H), 3)

    def _draw_bg_l3(self, surface, camera_x):
        # Buildings (parallax 0.40)
        for bg_x, bh, bw, _ in self._buildings:
            sx = bg_x - int(camera_x * 0.40)
            if sx + bw < 0 or sx > SCREEN_W:
                continue
            pygame.draw.rect(surface, CITY_BUILDING, (sx, GROUND_Y - bh, bw, bh))
            # Windows
            for wy in range(GROUND_Y - bh + 8, GROUND_Y - 10, 18):
                for wx2 in range(sx + 6, sx + bw - 6, 14):
                    pygame.draw.rect(surface, CITY_WINDOW, (wx2, wy, 8, 10))

        # Concrete ground
        pygame.draw.rect(surface, CITY_GROUND,
                         (0, GROUND_Y + 10, SCREEN_W, SCREEN_H - GROUND_Y - 10))
        pygame.draw.rect(surface, (90, 88, 82), (0, GROUND_Y, SCREEN_W, 14))
        # Road markings (dashed center line)
        for i in range(0, SCREEN_W + 60, 60):
            off = int(camera_x * 1.0) % 60
            pygame.draw.rect(surface, CITY_ROAD_LINE,
                             (i - off, GROUND_Y + 4, 30, 3))

    def _draw_bg_l2(self, surface, camera_x):
        # Ceiling rock
        pygame.draw.rect(surface, CAVE_STALA, (0, 0, SCREEN_W, 18))

        # Stalactites (parallax 0.70)
        for bg_x, drop in self._stalactites:
            sx = bg_x - int(camera_x * 0.70)
            if -20 <= sx <= SCREEN_W + 20:
                w = 10
                pts = [(sx - w//2, 0), (sx + w//2, 0), (sx, drop)]
                pygame.draw.polygon(surface, CAVE_STALA, pts)

        # Wall pillars (parallax 0.50)
        for i in range(0, int(WORLD_W * 0.50 + SCREEN_W), 220):
            sx = i - int(camera_x * 0.50)
            if -40 <= sx <= SCREEN_W + 40:
                pygame.draw.rect(surface, CAVE_WALL,
                                 (sx - 12, GROUND_Y - 80, 24, 80))

        # Torches (parallax 0.80)
        flicker = int(abs(math.sin(self._torch_t * 0.18)) * 8)
        for bg_x in self._torches:
            sx = bg_x - int(camera_x * 0.80)
            if -20 <= sx <= SCREEN_W + 20:
                ty = GROUND_Y - 85
                pygame.draw.rect(surface, CAVE_WALL, (sx - 3, ty, 6, 20))
                pygame.draw.circle(surface, TORCH_GLOW,
                                   (sx, ty - 2), 6 + flicker // 3)
                pygame.draw.circle(surface, TORCH_COL,
                                   (sx, ty - 2), 4 + flicker // 4)

        # Ground
        pygame.draw.rect(surface, CAVE_GROUND,
                         (0, GROUND_Y + 10, SCREEN_W, SCREEN_H - GROUND_Y - 10))
        pygame.draw.rect(surface, CAVE_GRASS, (0, GROUND_Y, SCREEN_W, 14))
        pygame.draw.rect(surface, CAVE_WALL,  (0, GROUND_Y, SCREEN_W, 4))
