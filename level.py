import random
import math
import pygame
from settings import *
from enemy import Grunt, Heavy, Boss, Thrower, Jumper, Healer, Bomber, TeacherBoss, RollerBoss, FlyingEye, RocketBoss, DoriBoss


class Level:
    """Manages the background scenery and enemy spawn triggers."""

    def __init__(self, level_num=1, num_players=1):
        self.level_num    = level_num
        self.num_players  = num_players
        self.swarm_active = False   # set True when swarm triggers; game.py reads + resets
        if level_num == 1:
            spawns = SPAWNS
        elif level_num == 2:
            spawns = SPAWNS_L2
        elif level_num == 3:
            spawns = SPAWNS_L3
        elif level_num == 4:
            spawns = SPAWNS_L4
        else:
            spawns = SPAWNS_L5
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
        elif level_num == 3:
            self.pits      = list(PITS_L3)
            self.platforms = list(PLATFORMS_L3)
            self.lava      = list(LAVA_L3)
        elif level_num == 4:
            self.pits      = list(PITS_L4)
            self.platforms = list(PLATFORMS_L4)
            self.lava      = list(LAVA_L4)
        else:
            self.pits      = list(PITS_L5)
            self.platforms = list(PLATFORMS_L5)
            self.lava      = list(LAVA_L5)

        rng = random.Random(42 + level_num)

        if level_num == 5:
            # Dori's Nursery — soft pastel room
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(NURSERY_SKY_TOP[0] + (NURSERY_SKY_BOT[0] - NURSERY_SKY_TOP[0]) * t)
                g = int(NURSERY_SKY_TOP[1] + (NURSERY_SKY_BOT[1] - NURSERY_SKY_TOP[1]) * t)
                b = int(NURSERY_SKY_TOP[2] + (NURSERY_SKY_BOT[2] - NURSERY_SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))
            bg_range_n = int(WORLD_W * 0.80 + SCREEN_W)
            # Toy blocks scattered on background wall
            self._bg_blocks = [
                (rng.randint(0, bg_range_n),
                 rng.randint(80, GROUND_Y - 80),   # y position on wall
                 rng.randint(0, 3),                 # color index
                 rng.randint(28, 52))               # size
                for _ in range(60)
            ]
            # Stars on the wall
            self._bg_stars = [
                (rng.randint(0, bg_range_n), rng.randint(30, 180))
                for _ in range(80)
            ]
            _rng3 = random.Random(146)
            self._far_shelves = [
                (_rng3.randint(0, int(WORLD_W * 0.12 + SCREEN_W)),
                 _rng3.randint(100, 220),
                 _rng3.randint(50, 110))
                for _ in range(20)
            ]
        elif level_num == 4:
            # Lava inferno cave
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(INFERNO_SKY_TOP[0] + (INFERNO_SKY_BOT[0] - INFERNO_SKY_TOP[0]) * t)
                g = int(INFERNO_SKY_TOP[1] + (INFERNO_SKY_BOT[1] - INFERNO_SKY_TOP[1]) * t)
                b = int(INFERNO_SKY_TOP[2] + (INFERNO_SKY_BOT[2] - INFERNO_SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))
            # Pre-bake heat shimmer gradient (orange glow rising from the lava floor)
            _heat_h = 130
            self._heat_surf = pygame.Surface((SCREEN_W, _heat_h))
            self._heat_surf.fill((0, 0, 0))
            for _hy in range(_heat_h):
                _tf = (1.0 - _hy / _heat_h) ** 2
                pygame.draw.line(self._heat_surf, (int(90 * _tf), int(22 * _tf), 0),
                                 (0, _hy), (SCREEN_W - 1, _hy))
            bg_range_s = int(WORLD_W * 0.70 + SCREEN_W)
            self._stalactites = [
                (rng.randint(0, bg_range_s), rng.randint(15, 80))
                for _ in range(130)
            ]
            self._lava_pools = [
                (rng.randint(0, int(WORLD_W * 0.90)), rng.randint(30, 90))
                for _ in range(60)
            ]
            _rng3 = random.Random(145)
            self._bg_formations = [
                (_rng3.randint(0, int(WORLD_W * 0.22 + SCREEN_W)),
                 _rng3.randint(40, 90),
                 _rng3.randint(60, 150))
                for _ in range(35)
            ]
        elif level_num == 3:
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
            _rng3 = random.Random(144)
            self._far_skyline = [
                (_rng3.randint(0, int(WORLD_W * 0.15 + SCREEN_W)),
                 _rng3.randint(50, 140),
                 _rng3.randint(30, 75))
                for _ in range(50)
            ]
            # Tsunami state — world-x of the right edge of the advancing wave
            self.tsunami_world_x = 0.0
            self.tsunami_active  = False
            self._tsunami_delay  = TSUNAMI_DELAY
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
            _rng3 = random.Random(142)
            self._foothills = [
                (_rng3.randint(0, int(WORLD_W * 0.38 + SCREEN_W)),
                 _rng3.randint(30, 62),
                 _rng3.randint(80, 180))
                for _ in range(40)
            ]
            # Sky gradient
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * t)
                g = int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * t)
                b = int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))
            # Pre-bake sunbeam surfaces (screen-space atmospheric shafts)
            self._beams = []
            _lean = 52
            for _bx, _bw, _ba in [(95, 68, 20), (275, 48, 15), (495, 72, 20),
                                   (690, 52, 16), (840, 62, 18)]:
                _bh = GROUND_Y
                _bs = pygame.Surface((_bw + _lean + 4, _bh), pygame.SRCALPHA)
                _bs.fill((0, 0, 0, 0))
                _outer = [(2, 0), (_bw + 2, 0), (_bw + _lean + 2, _bh), (_lean + 2, _bh)]
                pygame.draw.polygon(_bs, (255, 245, 180, _ba), _outer)
                _im = _bw // 4
                _inner = [(_im + 2, 0), (_bw - _im + 2, 0),
                          (_bw - _im + _lean + 2, _bh), (_im + _lean + 2, _bh)]
                pygame.draw.polygon(_bs, (255, 250, 210, _ba + 8), _inner)
                self._beams.append((_bx, _bs))
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
            _rng3 = random.Random(143)
            self._far_cave = [
                (_rng3.randint(0, int(WORLD_W * 0.25 + SCREEN_W)),
                 _rng3.randint(30, 65),
                 _rng3.randint(50, 100))
                for _ in range(28)
            ]
            self._sky = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                r = int(CAVE_SKY_TOP[0] + (CAVE_SKY_BOT[0] - CAVE_SKY_TOP[0]) * t)
                g = int(CAVE_SKY_TOP[1] + (CAVE_SKY_BOT[1] - CAVE_SKY_TOP[1]) * t)
                b = int(CAVE_SKY_TOP[2] + (CAVE_SKY_BOT[2] - CAVE_SKY_TOP[2]) * t)
                pygame.draw.line(self._sky, (r, g, b), (0, y), (SCREEN_W, y))

        # Per-level color grade overlay (pre-baked once)
        _grade_cols = {1: (255, 245, 200, 18), 3: (200, 220, 255, 22), 5: (240, 220, 255, 16)}
        if level_num in _grade_cols:
            self._grade_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            self._grade_surf.fill(_grade_cols[level_num])
        else:
            self._grade_surf = None

        self._torch_t = 0  # flicker timer
        self._prng = random.Random(242 + level_num)
        self._init_particles(self._prng)

    # ------------------------------------------------------------------ spawn
    def update(self, camera_x, freeze_tsunami=False):
        """Return a list of new Enemy instances whose trigger has been passed."""
        # Tsunami advance (level 3 only) — paused while no player is in control
        if self.level_num == 3 and not freeze_tsunami:
            if not self.tsunami_active:
                self._tsunami_delay -= 1
                if self._tsunami_delay <= 0:
                    self.tsunami_active = True
            else:
                self.tsunami_world_x += TSUNAMI_SPEED

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
                    elif kind == 'bomber':
                        new_enemies.append(Bomber(wx, GROUND_Y - Bomber.H))
                        has_regular = True
                    elif kind == 'swarm':
                        new_enemies += self._build_swarm(wx, camera_x)
                        self.swarm_active = True
                    elif kind == 'eye':
                        new_enemies.append(FlyingEye(wx, GROUND_Y - FlyingEye.H))
                        has_regular = True
                    elif kind == 'boss':
                        if self.level_num == 2:
                            new_enemies.append(TeacherBoss(wx, GROUND_Y - TeacherBoss.H))
                        elif self.level_num == 3:
                            new_enemies.append(RollerBoss(wx, GROUND_Y - RollerBoss.H))
                        elif self.level_num == 4:
                            new_enemies.append(RocketBoss(wx, GROUND_Y - RocketBoss.H))
                        elif self.level_num == 5:
                            new_enemies.append(DoriBoss(wx, GROUND_Y - DoriBoss.H))
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
                    if self.num_players >= 2:
                        flank_x3 = max(0, camera_x - random.randint(240, 380))
                        new_enemies.append(Heavy(flank_x3, GROUND_Y - Heavy.H))
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
        elif self.level_num == 3:
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
        elif self.level_num == 4:
            # Level 4: 4 left + 9 right — maximum chaos, FlyingEyes overhead
            return [
                # Left flank
                Bomber(lx,        GROUND_Y - Bomber.H),
                Jumper(lx + 70,   GROUND_Y - Jumper.H),
                Heavy(lx + 140,   GROUND_Y - Heavy.H),
                Bomber(lx + 210,  GROUND_Y - Bomber.H),
                # Right flank (ground)
                Heavy(wx,         GROUND_Y - Heavy.H),
                Thrower(wx + 65,  GROUND_Y - Thrower.H),
                Jumper(wx + 130,  GROUND_Y - Jumper.H),
                Bomber(wx + 195,  GROUND_Y - Bomber.H),
                Heavy(wx + 260,   GROUND_Y - Heavy.H),
                Jumper(wx + 325,  GROUND_Y - Jumper.H),
                Thrower(wx + 390, GROUND_Y - Thrower.H),
                Bomber(wx + 455,  GROUND_Y - Bomber.H),
                # Aerial
                FlyingEye(wx + 90,  GROUND_Y - FlyingEye.H),
                FlyingEye(wx + 280, GROUND_Y - FlyingEye.H),
            ]
        else:
            # Level 5: everything at once — hardest swarm
            return [
                # Left flank
                Heavy(lx,         GROUND_Y - Heavy.H),
                Bomber(lx + 65,   GROUND_Y - Bomber.H),
                FlyingEye(lx + 130, GROUND_Y - FlyingEye.H),
                Heavy(lx + 195,   GROUND_Y - Heavy.H),
                Thrower(lx + 260, GROUND_Y - Thrower.H),
                # Right flank (ground)
                Heavy(wx,         GROUND_Y - Heavy.H),
                Jumper(wx + 65,   GROUND_Y - Jumper.H),
                Bomber(wx + 130,  GROUND_Y - Bomber.H),
                Thrower(wx + 195, GROUND_Y - Thrower.H),
                Heavy(wx + 260,   GROUND_Y - Heavy.H),
                Jumper(wx + 325,  GROUND_Y - Jumper.H),
                Bomber(wx + 390,  GROUND_Y - Bomber.H),
                Thrower(wx + 455, GROUND_Y - Thrower.H),
                Heavy(wx + 520,   GROUND_Y - Heavy.H),
                # Aerial
                FlyingEye(wx + 80,  GROUND_Y - FlyingEye.H),
                FlyingEye(wx + 230, GROUND_Y - FlyingEye.H),
                FlyingEye(wx + 380, GROUND_Y - FlyingEye.H),
            ]

    # ------------------------------------------------------------------ draw
    def draw_background(self, surface, camera_x):
        self._torch_t += 1
        surface.blit(self._sky, (0, 0))

        if self.level_num == 1:
            self._draw_bg_l1(surface, camera_x)
        elif self.level_num == 2:
            self._draw_bg_l2(surface, camera_x)
        elif self.level_num == 3:
            self._draw_bg_l3(surface, camera_x)
        elif self.level_num == 4:
            self._draw_bg_l4(surface, camera_x)
        else:
            self._draw_bg_l5(surface, camera_x)

        self._draw_lava(surface, camera_x)
        self._draw_platforms(surface, camera_x)
        self._draw_pits(surface, camera_x)
        if self.level_num == 3:
            self._draw_tsunami(surface, camera_x)
        self._update_draw_particles(surface, camera_x)

    def _draw_bg_l1(self, surface, camera_x):
        # Sunbeams — gentle screen-space sway, drawn behind mountains
        t = self._torch_t
        for i, (bx, bs) in enumerate(self._beams):
            sx = bx + int(math.sin(t * 0.008 + i * 1.4) * 11)
            surface.blit(bs, (sx, 0))

        for bg_x, peak_y, mw in self._mountains:
            sx = bg_x - int(camera_x * 0.22)
            if -mw <= sx <= SCREEN_W + mw:
                pts = [(sx,        GROUND_Y - 15),
                       (sx + mw//2, peak_y),
                       (sx + mw,   GROUND_Y - 15)]
                pygame.draw.polygon(surface, MOUNTAIN, pts)

        # Mid-ground foothills (parallax 0.38)
        for bg_x, fh, fw in self._foothills:
            sx = bg_x - int(camera_x * 0.38)
            if -fw <= sx <= SCREEN_W + fw:
                pts = [(sx, GROUND_Y - 12), (sx + fw//2, GROUND_Y - fh), (sx + fw, GROUND_Y - 12)]
                pygame.draw.polygon(surface, (34, 88, 22), pts)

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
        # Grass tufts
        _off = int(camera_x) % 14
        for _gx in range(-_off, SCREEN_W + 14, 14):
            pygame.draw.line(surface, (48, 148, 28), (_gx, GROUND_Y), (_gx - 3, GROUND_Y - 7), 1)
            pygame.draw.line(surface, (48, 148, 28), (_gx, GROUND_Y), (_gx + 3, GROUND_Y - 7), 1)

    def _draw_platforms(self, surface, camera_x):
        if self.level_num == 1:
            stone, top, bot, col = (90,80,65), (120,110,90), (60,52,42), (80,70,55)
        elif self.level_num == 4:
            stone, top, bot, col = (75,28,12), (100,40,15), (50,18,8), (65,24,10)
        elif self.level_num == 5:
            stone, top, bot, col = (200,180,220), (225,205,238), (170,150,195), (210,190,228)
        else:
            stone, top, bot, col = (58,48,72), (78,65,95), (40,32,52), (50,40,62)
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

    def _draw_bg_l4(self, surface, camera_x):
        t = self._torch_t
        # Distant volcanic rock formations (parallax 0.22)
        for bg_x, fh, fw in self._bg_formations:
            sx = bg_x - int(camera_x * 0.22)
            if sx + fw < 0 or sx > SCREEN_W:
                continue
            pts = [(sx, GROUND_Y - 6), (sx + fw//2, GROUND_Y - fh), (sx + fw, GROUND_Y - 6)]
            pygame.draw.polygon(surface, (44, 14, 6), pts)
        # Ceiling rock
        pygame.draw.rect(surface, INFERNO_CEILING, (0, 0, SCREEN_W, 22))
        # Stalactites — bright orange glowing tips (parallax 0.65)
        for bg_x, drop in self._stalactites:
            sx = bg_x - int(camera_x * 0.65)
            if -20 <= sx <= SCREEN_W + 20:
                w = 8
                pts = [(sx - w//2, 0), (sx + w//2, 0), (sx, drop)]
                pygame.draw.polygon(surface, INFERNO_ROCK, pts)
                # Glowing lava drip tip
                flicker = int(abs(math.sin(t * 0.14 + bg_x * 0.03)) * 3)
                pygame.draw.circle(surface, (255, 120 + flicker * 10, 20),
                                   (sx, drop - 2), 3 + flicker)

        # Background lava rivulets on cave walls (parallax 0.35)
        for bg_x, pool_w in self._lava_pools:
            sx = bg_x - int(camera_x * 0.35)
            if sx + pool_w < 0 or sx > SCREEN_W:
                continue
            flicker2 = int(abs(math.sin(t * 0.11 + bg_x * 0.02)) * 4)
            pygame.draw.rect(surface, (180, 50 + flicker2 * 5, 5),
                             (sx, GROUND_Y - 50, pool_w, 6))
            pygame.draw.rect(surface, (240, 100 + flicker2 * 8, 20),
                             (sx, GROUND_Y - 52, pool_w, 3))

        # Wall pillars (parallax 0.50)
        for i in range(0, int(WORLD_W * 0.50 + SCREEN_W), 240):
            sx = i - int(camera_x * 0.50)
            if -40 <= sx <= SCREEN_W + 40:
                pygame.draw.rect(surface, INFERNO_ROCK, (sx - 14, GROUND_Y - 90, 28, 90))

        # Ground
        pygame.draw.rect(surface, INFERNO_GROUND,
                         (0, GROUND_Y + 10, SCREEN_W, SCREEN_H - GROUND_Y - 10))
        pygame.draw.rect(surface, INFERNO_ROCK, (0, GROUND_Y, SCREEN_W, 14))
        # Glowing crack lines on ground
        for gx in range(0, SCREEN_W + 80, 80):
            off = int(camera_x * 1.0) % 80
            cx2 = gx - off
            glow_int = int(abs(math.sin(t * 0.09 + cx2 * 0.01)) * 60)
            pygame.draw.line(surface, (200 + glow_int // 2, 60, 5),
                             (cx2, GROUND_Y + 2), (cx2 + 40, GROUND_Y + 12), 1)
        # Ground rubble chunks
        _off2 = int(camera_x) % 26
        for _i in range(-_off2, SCREEN_W + 26, 26):
            pygame.draw.rect(surface, (60, 20, 8), (_i, GROUND_Y + 3, 9, 5))
            pygame.draw.rect(surface, (74, 26, 10), (_i + 13, GROUND_Y + 5, 7, 4))
        # Heat shimmer rising from lava floor
        _hbob = int(abs(math.sin(t * 0.07)) * 5)
        surface.blit(self._heat_surf, (0, GROUND_Y - 115 + _hbob),
                     special_flags=pygame.BLEND_RGB_ADD)

    def _draw_bg_l5(self, surface, camera_x):
        t = self._torch_t
        _BLOCK_COLS = [NURSERY_BLOCK_R, NURSERY_BLOCK_B, NURSERY_BLOCK_Y, NURSERY_BLOCK_G]

        # Wall background (lavender)
        pygame.draw.rect(surface, NURSERY_WALL, (0, 0, SCREEN_W, GROUND_Y))

        # Distant shelves on wall (parallax 0.12)
        for bg_x, by, bw in self._far_shelves:
            sx = bg_x - int(camera_x * 0.12)
            if sx + bw < 0 or sx > SCREEN_W:
                continue
            pygame.draw.rect(surface, (158, 138, 176), (sx, by, bw, 8))
            pygame.draw.rect(surface, (146, 126, 162), (sx, by + 8, 7, 44))
            pygame.draw.rect(surface, (146, 126, 162), (sx + bw - 7, by + 8, 7, 44))

        # Stars on the wall (parallax 0.20)
        for bg_x, star_y in self._bg_stars:
            sx = bg_x - int(camera_x * 0.20)
            if -15 <= sx <= SCREEN_W + 15:
                twinkle = int(abs(math.sin(t * 0.08 + bg_x * 0.05)) * 30)
                col = (NURSERY_STAR[0], NURSERY_STAR[1], NURSERY_STAR[2] - twinkle)
                # 5-pointed star shortcut: draw two crossing rects
                pygame.draw.rect(surface, col, (sx - 5, star_y - 1, 10, 3))
                pygame.draw.rect(surface, col, (sx - 1, star_y - 5, 3, 10))
                pygame.draw.circle(surface, col, (sx, star_y), 3)

        # Moon on the wall (parallax 0.08)
        moon_x = 900 - int(camera_x * 0.08)
        moon_y = 70
        if -30 <= moon_x <= SCREEN_W + 30:
            pygame.draw.circle(surface, NURSERY_MOON, (moon_x, moon_y), 28)
            pygame.draw.circle(surface, NURSERY_WALL, (moon_x + 16, moon_y - 8), 22)

        # Big toy blocks on wall background (parallax 0.30)
        for bg_x, by, col_idx, size in self._bg_blocks:
            sx = bg_x - int(camera_x * 0.30)
            if sx + size < 0 or sx > SCREEN_W:
                continue
            col = _BLOCK_COLS[col_idx]
            darker = tuple(max(0, c - 45) for c in col)
            lighter = tuple(min(255, c + 30) for c in col)
            pygame.draw.rect(surface, col, (sx, by, size, size))
            pygame.draw.rect(surface, lighter, (sx, by, size, 5))         # top highlight
            pygame.draw.rect(surface, lighter, (sx, by, 5, size))         # left highlight
            pygame.draw.rect(surface, darker,  (sx, by + size - 4, size, 4))   # bottom shadow
            pygame.draw.rect(surface, darker,  (sx + size - 4, by, 4, size))   # right shadow

        # Carpet stripes on ground
        pygame.draw.rect(surface, NURSERY_CARPET,
                         (0, GROUND_Y + 10, SCREEN_W, SCREEN_H - GROUND_Y - 10))
        pygame.draw.rect(surface, NURSERY_CARPET, (0, GROUND_Y, SCREEN_W, 14))
        # Carpet stripe pattern
        for i in range(0, SCREEN_W + 40, 40):
            off = int(camera_x * 1.0) % 40
            pygame.draw.rect(surface, NURSERY_CARPET2, (i - off, GROUND_Y, 20, 14))

    def _draw_tsunami(self, surface, camera_x):
        if not self.tsunami_active:
            return
        t  = self._torch_t
        # sx: screen-x of the right (leading) edge of the wave
        sx = int(self.tsunami_world_x - camera_x)
        draw_w = min(sx, SCREEN_W)
        if draw_w <= 0:
            return

        # Translucent water body
        wave_surf = pygame.Surface((draw_w, SCREEN_H), pygame.SRCALPHA)
        wave_surf.fill((20, 70, 200, 150))
        surface.blit(wave_surf, (0, 0))

        # Animated foam at the wave's right edge
        for y in range(0, SCREEN_H, 3):
            wobble = int(math.sin(t * 0.18 + y * 0.06) * 10)
            ex = sx + wobble
            if 0 <= ex < SCREEN_W:
                pygame.draw.circle(surface, (180, 225, 255, 200), (ex, y + 1), 3)

        # Bright crest line
        for y in range(0, SCREEN_H, 2):
            wobble2 = int(math.sin(t * 0.18 + y * 0.06) * 10)
            ex2 = sx + wobble2
            if 0 <= ex2 < SCREEN_W:
                pygame.draw.rect(surface, (220, 245, 255), (ex2 - 1, y, 3, 2))

    def _draw_bg_l3(self, surface, camera_x):
        # Distant city skyline silhouette (parallax 0.15)
        for bg_x, fh, fw in self._far_skyline:
            sx = bg_x - int(camera_x * 0.15)
            if sx + fw < 0 or sx > SCREEN_W:
                continue
            pygame.draw.rect(surface, (95, 105, 118), (sx, GROUND_Y - fh, fw, fh))

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
        # Sidewalk expansion joints
        _off2 = int(camera_x) % 48
        for _i in range(-_off2, SCREEN_W + 48, 48):
            pygame.draw.line(surface, (72, 70, 65), (_i, GROUND_Y), (_i, GROUND_Y + 14), 1)

    def _draw_bg_l2(self, surface, camera_x):
        # Far cave wall formations (parallax 0.25)
        for bg_x, fh, fw in self._far_cave:
            sx = bg_x - int(camera_x * 0.25)
            if sx + fw < 0 or sx > SCREEN_W:
                continue
            pygame.draw.ellipse(surface, (20, 14, 32), (sx - fw//2, 0, fw, fh))

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
        # Cobblestone detail
        _off = int(camera_x) % 30
        for _i in range(-_off, SCREEN_W + 30, 30):
            _even = (_i // 30) % 2 == 0
            pygame.draw.rect(surface, (50, 42, 64) if _even else (38, 32, 52), (_i, GROUND_Y + 2, 28, 5))
            pygame.draw.rect(surface, (38, 32, 52) if _even else (50, 42, 64), (_i + 15, GROUND_Y + 7, 28, 5))

    # ------------------------------------------------------------------ particles
    def _init_particles(self, prng):
        n = 120
        ln = self.level_num
        self._particles = []
        for _ in range(n):
            wx = prng.randint(0, int(WORLD_W + SCREEN_W))
            if ln == 4:
                y = prng.uniform(GROUND_Y - 110, GROUND_Y - 5)
            elif ln in (1, 5):
                y = prng.uniform(-30, GROUND_Y - 30)
            else:
                y = prng.uniform(15, GROUND_Y - 15)
            vx, vy, ml = self._rand_pv(prng)
            self._particles.append([float(wx), float(y), vx, vy, ml, ml])

    def _rand_pv(self, prng):
        ln = self.level_num
        if ln == 1:
            vx = prng.uniform(-0.5, -0.05)
            vy = prng.uniform(0.25, 0.8)
            ml = prng.randint(90, 250)
        elif ln == 2:
            vx = prng.uniform(-0.12, 0.12)
            vy = prng.uniform(-0.06, 0.06)
            ml = prng.randint(160, 400)
        elif ln == 3:
            vx = prng.uniform(-1.0, -0.15)
            vy = prng.uniform(-0.25, 0.35)
            ml = prng.randint(60, 170)
        elif ln == 4:
            vx = prng.uniform(-0.2, 0.2)
            vy = prng.uniform(-1.6, -0.4)
            ml = prng.randint(30, 85)
        else:
            vx = prng.uniform(-0.25, 0.25)
            vy = prng.uniform(0.15, 0.5)
            ml = prng.randint(90, 210)
        return vx, vy, ml

    def _update_draw_particles(self, surface, camera_x):
        prng = self._prng
        ln   = self.level_num
        t    = self._torch_t
        _SPARKLE = [(255, 150, 150), (150, 255, 150), (150, 150, 255), (255, 255, 130), (255, 180, 255)]

        for p in self._particles:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0 or p[1] < -30 or p[1] > GROUND_Y + 20:
                p[0] = float(prng.randint(0, int(WORLD_W + SCREEN_W)))
                if ln == 4:
                    p[1] = float(prng.uniform(GROUND_Y - 80, GROUND_Y - 5))
                elif ln in (1, 5):
                    p[1] = float(prng.randint(-20, 5))
                else:
                    p[1] = float(prng.randint(5, GROUND_Y - 15))
                vx, vy, ml = self._rand_pv(prng)
                p[2], p[3], p[4], p[5] = vx, vy, ml, ml

            sx = int(p[0]) - int(camera_x * 0.85)
            if not (-20 <= sx <= SCREEN_W + 20):
                continue
            sy = int(p[1])
            lf = p[4] / max(1, p[5])

            if ln == 1:   # falling leaf — diamond shape
                dim = max(30, int(255 * min(1.0, lf * 3)))
                green = int(p[0]) % 3 < 2
                base = (52, 128, 26) if green else (102, 68, 20)
                col = (base[0] * dim // 255, base[1] * dim // 255, base[2] * dim // 255)
                wobble = int(math.sin(t * 0.1 + p[0] * 0.01) * 2)
                pts = [(sx, sy - 4 + wobble), (sx + 3, sy), (sx, sy + 3), (sx - 3, sy)]
                pygame.draw.polygon(surface, col, pts)
            elif ln == 2:  # cave dust mote — tiny circle
                r = 2 if int(p[0]) % 3 < 2 else 1
                dim = max(50, int(155 * lf))
                pygame.draw.circle(surface, (dim, max(0, dim - 10), min(255, dim + 20)), (sx, sy), r)
            elif ln == 3:  # city paper scrap — tiny rect
                dim = max(80, int(220 * lf))
                pygame.draw.rect(surface, (dim, max(0, dim - 12), max(0, dim - 22)), (sx - 2, sy - 1, 5, 3))
            elif ln == 4:  # ember — bright orange rising dot
                sz = 2 if lf > 0.4 else 1
                flick = int(math.sin(t * 0.22 + p[0] * 0.03) * 25)
                g = min(255, 65 + flick + int(105 * lf))
                pygame.draw.circle(surface, (255, g, 8), (sx, sy), sz)
            else:           # nursery sparkle — cross
                col = _SPARKLE[int(p[0]) % len(_SPARKLE)]
                s = max(1, int(3 * lf))
                pygame.draw.line(surface, col, (sx - s, sy), (sx + s, sy), 1)
                pygame.draw.line(surface, col, (sx, sy - s), (sx, sy + s), 1)

    def draw_color_grade(self, surface):
        """Blit a pre-baked subtle color tint over the fully-drawn scene."""
        if self._grade_surf:
            surface.blit(self._grade_surf, (0, 0))
