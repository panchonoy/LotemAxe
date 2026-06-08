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
