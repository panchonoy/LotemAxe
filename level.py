import random
import math
import pygame
from settings import *
from enemy import Grunt, Heavy, Boss


class Level:
    """Manages the background scenery and enemy spawn triggers."""

    def __init__(self, level_num=1):
        self.level_num = level_num
        spawns = SPAWNS if level_num == 1 else SPAWNS_L2
        self._pending = list(spawns)
        self.boss_triggered = False

        rng = random.Random(42 + level_num)

        if level_num == 1:
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
                for wx, kind in spawn_list:
                    if kind == 'grunt':
                        new_enemies.append(Grunt(wx, GROUND_Y - Grunt.H))
                    elif kind == 'heavy':
                        new_enemies.append(Heavy(wx, GROUND_Y - Heavy.H))
                    elif kind == 'boss':
                        new_enemies.append(Boss(wx, GROUND_Y - Boss.H))
                        self.boss_triggered = True
            else:
                remaining.append((trigger_x, spawn_list))
        self._pending = remaining
        return new_enemies

    # ------------------------------------------------------------------ draw
    def draw_background(self, surface, camera_x):
        self._torch_t += 1
        surface.blit(self._sky, (0, 0))

        if self.level_num == 1:
            self._draw_bg_l1(surface, camera_x)
        else:
            self._draw_bg_l2(surface, camera_x)

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
