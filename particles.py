import pygame
import math
import random
from settings import HIT_COL, SPARK_COL, MAGIC_FX, WHITE


class Particle:
    def __init__(self, x, y, vx, vy, life, color, radius=4, gravity=0.28):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = life
        self.max_life = life
        self.color = color
        self.radius = radius
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.96
        self.life -= 1
        return self.life > 0

    def draw(self, surface, cam_x):
        r = max(1, int(self.radius * self.life / self.max_life))
        sx = int(self.x) - cam_x
        sy = int(self.y)
        if -r <= sx <= 1040 + r and -r <= sy <= 600 + r:
            pygame.draw.circle(surface, self.color, (sx, sy), r)


class RingParticle:
    """Expanding shockwave ring that fades as it grows."""
    def __init__(self, x, y, max_radius, color, life=22):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surface, cam_x):
        t = 1.0 - self.life / self.max_life
        radius = max(2, int(self.max_radius * t))
        alpha  = self.life / self.max_life
        col    = tuple(int(c * alpha) for c in self.color)
        width  = max(1, int(5 * alpha))
        sx = int(self.x) - cam_x
        sy = int(self.y)
        pygame.draw.circle(surface, col, (sx, sy), radius, width)


def spawn_hit(particles, x, y):
    for _ in range(9):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)
        col = random.choice([HIT_COL, SPARK_COL, WHITE])
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 2,
            random.randint(8, 18),
            col,
            random.randint(3, 6),
        ))


def spawn_magic(particles, x, y, radius):
    # Expanding shockwave rings
    particles.append(RingParticle(x, y, radius,        (100, 160, 255), life=22))
    particles.append(RingParticle(x, y, radius * 0.65, (180, 210, 255), life=16))

    # Radial sparks
    for _ in range(40):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(0, radius)
        speed = random.uniform(3, 9)
        col = random.choice([MAGIC_FX, WHITE, (120, 160, 255)])
        particles.append(Particle(
            x + math.cos(angle) * dist,
            y + math.sin(angle) * dist,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 3,
            random.randint(14, 28),
            col,
            random.randint(4, 8),
            gravity=0.1,
        ))


def spawn_death(particles, x, y, color):
    for _ in range(16):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 5)
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 3,
            random.randint(18, 30),
            color,
            random.randint(4, 7),
        ))


def spawn_pee(particles, x, y, facing):
    """Yellow forward stream — Lotem's magic."""
    for _ in range(26):
        angle = random.uniform(-0.45, 0.45)
        speed = random.uniform(4, 9)
        vx = math.cos(angle) * speed * facing
        vy = math.sin(angle) * speed - 1.5
        col = random.choice([(255, 230, 50), (240, 210, 30), (210, 200, 40)])
        particles.append(Particle(
            x, y, vx, vy,
            random.randint(14, 22), col,
            random.randint(3, 6), gravity=0.18,
        ))
    # Extended reach droplets
    for _ in range(10):
        dist = random.uniform(20, 110)
        angle = random.uniform(-0.12, 0.12)
        particles.append(Particle(
            x + math.cos(angle) * dist * facing,
            y + math.sin(angle) * dist,
            math.cos(angle) * 1.5 * facing,
            math.sin(angle) * 0.8,
            random.randint(10, 18), (255, 240, 60),
            random.randint(3, 5), gravity=0.12,
        ))


def spawn_tornado(particles, x, y):
    """Swirling green tornado — Gal's magic."""
    particles.append(RingParticle(x, y, 150, (60, 200,  80), life=24))
    particles.append(RingParticle(x, y, 100, (80, 230, 100), life=18))
    for _ in range(50):
        angle = random.uniform(0, math.pi * 2)
        dist  = random.uniform(0, 150)
        speed = random.uniform(2, 8)
        col   = random.choice([(60, 200, 80), (80, 230, 100), (40, 160, 60), WHITE])
        # Tangential velocity for spin effect
        particles.append(Particle(
            x + math.cos(angle) * dist,
            y + math.sin(angle) * dist,
            math.cos(angle + math.pi / 2) * speed,
            math.sin(angle + math.pi / 2) * speed - 4,
            random.randint(16, 28), col,
            random.randint(3, 7), gravity=0.05,
        ))


def spawn_explosion(particles, x, y):
    """Orange/red blast for Bomber detonation."""
    particles.append(RingParticle(x, y, 90,  (255, 140,  0), life=20))
    particles.append(RingParticle(x, y, 60,  (255,  80,  0), life=14))
    for _ in range(35):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3, 10)
        col = random.choice([(255, 120, 0), (255, 60, 0), (255, 200, 50), (220, 220, 200)])
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 4,
            random.randint(16, 30), col,
            random.randint(4, 8), gravity=0.2,
        ))
    for _ in range(10):   # smoke puffs
        particles.append(Particle(
            x + random.randint(-20, 20),
            y + random.randint(-10, 10),
            random.uniform(-1.5, 1.5),
            random.uniform(-3, -1),
            random.randint(20, 35),
            (80, 80, 80),
            random.randint(5, 10),
            gravity=0.02,
        ))


class LightningBolt:
    """Flickering zigzag bolt between two screen-space points."""
    def __init__(self, x1, y1, x2, y2, life=18):
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        self.life     = life
        self.max_life = life

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surface, cam_x):
        alpha = self.life / self.max_life
        core_col = (int(200 + 55 * alpha), int(200 + 55 * alpha), 255)
        glow_col = (int(80 * alpha),  int(120 * alpha), int(255 * alpha))
        width    = max(1, int(3 * alpha))

        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        length   = max(1.0, math.hypot(dx, dy))
        num_segs = max(3, int(length / 22))

        pts = [(int(self.x1), int(self.y1))]
        for i in range(1, num_segs):
            t    = i / num_segs
            jitter = 14 * math.sin(t * math.pi)   # bigger wobble in middle
            mx   = self.x1 + dx * t + random.uniform(-jitter, jitter)
            my   = self.y1 + dy * t + random.uniform(-jitter, jitter)
            pts.append((int(mx), int(my)))
        pts.append((int(self.x2), int(self.y2)))

        if len(pts) >= 2:
            pygame.draw.lines(surface, glow_col, False, pts, width + 3)
            pygame.draw.lines(surface, core_col, False, pts, width)


def spawn_lightning_chain(particles, points):
    """
    points — list of (sx, sy) screen-space coords: [caster, enemy0, enemy1, ...]
    Draws a bolt between each consecutive pair plus electric sparks at each node.
    """
    for i in range(len(points) - 1):
        particles.append(LightningBolt(
            points[i][0], points[i][1],
            points[i+1][0], points[i+1][1],
            life=random.randint(14, 20),
        ))
    # Electric sparks at each hit node (skip the caster origin)
    for sx, sy in points[1:]:
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            col   = random.choice([(255, 255, 180), (180, 200, 255), WHITE])
            particles.append(Particle(
                sx, sy,
                math.cos(angle) * speed,
                math.sin(angle) * speed - 2,
                random.randint(8, 16), col,
                random.randint(2, 4), gravity=0.15,
            ))


def spawn_heal(particles, x, y):
    """Green sparkles — Healer casting a heal."""
    for _ in range(14):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 4)
        col = random.choice([(80, 220, 80), (120, 255, 120), (60, 200, 100)])
        particles.append(Particle(
            x, y,
            math.cos(angle) * speed,
            math.sin(angle) * speed - 3,
            random.randint(18, 30), col,
            random.randint(3, 5), gravity=0.05,
        ))
    particles.append(RingParticle(x, y, 60, (80, 200, 80), life=16))
