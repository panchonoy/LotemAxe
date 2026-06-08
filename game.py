import sys
import os
import random
import pygame

from settings import *
from player import Player, P1_KEYS, P2_KEYS
from enemy import Boss
from particles import spawn_hit, spawn_magic, spawn_death
from level import Level
import ui
import sfx
import sprites

# Game states
MENU         = 'menu'
COLOR_SELECT = 'color_select'
PLAYING      = 'playing'
GAME_OVER    = 'game_over'
VICTORY      = 'victory'
CREDITS      = 'credits'

HISCORE_FILE = os.path.join(os.path.dirname(__file__), 'highscore.txt')


def _load_hiscore():
    try:
        with open(HISCORE_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _save_hiscore(score):
    try:
        with open(HISCORE_FILE, 'w') as f:
            f.write(str(score))
    except Exception:
        pass


class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        sfx.init()
        sprites.init()
        pygame.joystick.init()
        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self._joysticks.append(j)

        self._init_fonts()
        self.hiscore     = _load_hiscore()
        self.num_players = 1
        self.current_level = 1
        self.state       = MENU
        self._new_game()

    # ------------------------------------------------------------------ setup
    def _init_fonts(self):
        self.font_title = pygame.font.SysFont('Arial', 76, bold=True)
        self.font_big   = pygame.font.SysFont('Arial', 58, bold=True)
        self.font_med   = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 19)
        self.font_hint  = pygame.font.SysFont('Arial', 14)

    def _new_game(self, level_num=1):
        self.current_level = level_num
        joy2 = self._joysticks[0] if self._joysticks else None

        c1 = getattr(self, 'p1_color', 'asaf'  if sprites.is_ready() else 'blue')
        c2 = getattr(self, 'p2_color', 'lotem' if sprites.is_ready() else 'red')

        _SPRITE_CHARS = {'asaf', 'lotem', 'gal', 'nitay'}

        def _make_player(x, pid, keys, color, joy=None):
            if color in _SPRITE_CHARS:
                return Player(x, GROUND_Y - P_H, player_id=pid,
                              key_bindings=keys, joystick=joy,
                              sprite_char=color)
            return Player(x, GROUND_Y - P_H, player_id=pid,
                          key_bindings=keys, joystick=joy, color=color)

        self.players = [_make_player(150, 1, P1_KEYS, c1)]
        if self.num_players == 2:
            self.players.append(_make_player(260, 2, P2_KEYS, c2, joy=joy2))

        self.enemies   = []
        self.particles = []
        self.camera_x  = 0.0
        self.score     = 0
        self.level     = Level(level_num)

        self._hit_stop     = 0
        self._shake        = 0.0
        self._magic_flash  = 0
        self._victory_wait = 0

    # ----------------------------------------------------------- color select
    # sprite chars use the sprite sheet; the rest are knight color palettes
    _COLOR_OPTIONS = ['asaf', 'lotem', 'gal', 'nitay', 'blue', 'red', 'green', 'gold']
    _COLOR_MAP = {
        'blue':  ((45, 85, 195),  (65, 108, 218),  (28, 50, 155)),
        'red':   ((195, 65, 45),  (218, 90, 65),   (155, 28, 28)),
        'green': ((40, 160, 60),  (65, 195, 85),   (22, 105, 38)),
        'gold':  ((200, 165, 30), (225, 195, 60),  (155, 120, 15)),
        # Sprite chars get a representative "swatch" color for the UI circle
        'asaf':  ((60, 45, 25),   (80, 60, 35),    (35, 25, 12)),
        'lotem': ((220, 175, 130),(245, 200, 160),  (180, 140, 100)),
        'gal':   ((40, 35, 55),   (60, 55, 75),    (25, 20, 38)),
        'nitay': ((35, 30, 50),   (55, 50, 70),    (20, 15, 33)),
    }

    def _handle_color_select(self, key):
        opts = self._COLOR_OPTIONS
        if key in (pygame.K_LEFT, pygame.K_a):
            self._color_cursor[0] = (self._color_cursor[0] - 1) % len(opts)
            self.p1_color = opts[self._color_cursor[0]]
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._color_cursor[0] = (self._color_cursor[0] + 1) % len(opts)
            self.p1_color = opts[self._color_cursor[0]]
        elif self.num_players == 2:
            if key == pygame.K_j:
                self._color_cursor[1] = (self._color_cursor[1] - 1) % len(opts)
                self.p2_color = opts[self._color_cursor[1]]
            elif key == pygame.K_l:
                self._color_cursor[1] = (self._color_cursor[1] + 1) % len(opts)
                self.p2_color = opts[self._color_cursor[1]]
        if key == pygame.K_RETURN:
            self._new_game()
            self.state = PLAYING

    # ------------------------------------------------------------------ run
    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            if self.state == PLAYING:
                self._update()
            self._draw()

    # ------------------------------------------------------------------ events
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if self.state == MENU:
                    if event.key == pygame.K_1:
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self.state = COLOR_SELECT
                    elif event.key in (pygame.K_2, pygame.K_RETURN):
                        self.num_players = 1 if event.key == pygame.K_RETURN else 2
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self.state = COLOR_SELECT

                elif self.state == COLOR_SELECT:
                    self._handle_color_select(event.key)

                elif self.state == VICTORY:
                    if event.key == pygame.K_RETURN:
                        self._new_game(level_num=2)
                        self.state = PLAYING
                elif self.state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self._new_game()
                        self.state = MENU
                elif self.state == CREDITS:
                    if event.key == pygame.K_RETURN:
                        self._new_game()
                        self.state = MENU

            # Joystick start button
            if event.type == pygame.JOYBUTTONDOWN:
                if self.state == MENU and event.button == 9:  # Start
                    self.num_players = 1
                    self._new_game()
                    self.state = PLAYING
                elif self.state == VICTORY and event.button == 9:
                    self._new_game(level_num=2)
                    self.state = PLAYING
                elif self.state in (GAME_OVER, CREDITS) and event.button == 9:
                    self._new_game()
                    self.state = MENU

    # ------------------------------------------------------------------ update
    def _update(self):
        if self._hit_stop > 0:
            self._hit_stop -= 1
            return

        all_keys = pygame.key.get_pressed()

        # --- Player input ---
        for player in self.players:
            player.handle_input(all_keys)
            player.update(int(self.camera_x))
            if player.magic_just_used:
                player.magic_just_used = False
                self._do_magic(player)

        # --- Camera: follow the leading living player ---
        living = [p for p in self.players if not p.out_of_lives and not p.dead]
        if not living:
            living = self.players  # fallback if all dead (game-over handled below)
        lead_x = max(p.x for p in living)
        target_x = lead_x - CAM_LEAD
        self.camera_x += (target_x - self.camera_x) * 0.14
        self.camera_x = max(0.0, min(self.camera_x, float(WORLD_W - SCREEN_W)))

        # --- Spawn new enemies ---
        new_spawns = self.level.update(int(self.camera_x))
        for e in new_spawns:
            if isinstance(e, Boss):
                sfx.play('boss_roar', 1.0)
        self.enemies.extend(new_spawns)

        # --- Enemy update + combat ---
        dead_this_frame = []
        for enemy in self.enemies:
            enemy.update(self.players)
            hit, target_player = enemy.can_attack(self.players)
            if hit and target_player:
                if target_player.take_damage(enemy.atk_dmg):
                    self._shake = max(self._shake, 6.0)
            # Boss charge area-hit shake
            if hasattr(enemy, '_charge_timer') and enemy._charge_timer > 0:
                self._shake = max(self._shake, 5.0)

        # Player swords vs enemies
        for player in self.players:
            if player.dead or player.out_of_lives:
                continue
            atk = player.atk_rect
            if atk and player.atk_timer == player.current_atk_dur - 1:
                sfx.play('swing', 0.6)
            if not atk:
                continue
            for enemy in self.enemies:
                if enemy in player._hit_set:
                    continue
                if atk.colliderect(enemy.rect):
                    player._hit_set.add(enemy)
                    kb_dir = 1 if enemy.rect.centerx >= player.rect.centerx else -1
                    dmg   = player.current_atk_dmg
                    stun  = player.current_atk_stun
                    if enemy.take_damage(dmg, kb_dir, stun):
                        scr_x = atk.centerx - int(self.camera_x)
                        spawn_hit(self.particles, scr_x, atk.centery)
                        self._hit_stop = max(self._hit_stop, 3)
                        sfx.play('hit', 0.7)
                        if enemy.dead:
                            self.score += enemy.score_value
                            dead_this_frame.append(enemy)
                            sfx.play('death', 0.5)

        for e in dead_this_frame:
            scr_x = e.rect.centerx - int(self.camera_x)
            spawn_death(self.particles, scr_x, e.rect.centery, e.death_color)

        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        # --- Particles ---
        self.particles = [p for p in self.particles if p.update()]

        # --- Decay ---
        self._shake       = max(0.0, self._shake - 0.4)
        if self._magic_flash > 0: self._magic_flash -= 1

        # --- Win/Lose ---
        boss_dead = self.level.boss_triggered and not any(isinstance(e, Boss) for e in self.enemies if not e.dead)
        if boss_dead:
            self._victory_wait += 1
            if self._victory_wait > 100:
                if self.score > self.hiscore:
                    self.hiscore = self.score
                    _save_hiscore(self.hiscore)
                if self.current_level == 1:
                    self.state = VICTORY   # brief victory then → level 2
                else:
                    self.state = CREDITS

        all_out = all(p.out_of_lives for p in self.players)
        if all_out:
            self.state = GAME_OVER

    # ------------------------------------------------------------------ magic
    def _do_magic(self, caster):
        cx = int(caster.x) + P_W // 2
        cy = int(caster.y) + P_H // 2
        for enemy in self.enemies:
            dx = abs(enemy.rect.centerx - cx)
            if dx < P_MAGIC_RAD:
                kb_dir = 1 if enemy.rect.centerx >= cx else -1
                if enemy.take_damage(P_MAGIC_DMG, kb_dir, 0):
                    if enemy.dead:
                        self.score += enemy.score_value
                        scr_x = enemy.rect.centerx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        scr_cx = cx - int(self.camera_x)
        spawn_magic(self.particles, scr_cx, cy, P_MAGIC_RAD)
        self._shake       = 12.0
        self._magic_flash = 18
        sfx.play('magic', 0.8)

    # ------------------------------------------------------------------ draw
    def _draw(self):
        shake_ox = random.randint(-int(self._shake), int(self._shake)) if self._shake > 1 else 0
        shake_oy = random.randint(-int(self._shake), int(self._shake)) if self._shake > 1 else 0
        cam_x = int(self.camera_x) + shake_ox

        if self.state == MENU:
            self._draw_menu()
        elif self.state == COLOR_SELECT:
            self._draw_color_select()
        elif self.state == CREDITS:
            self._draw_credits()
        else:
            self._draw_world(cam_x)
            if self.state == GAME_OVER:
                self._draw_overlay('GAME OVER', (210, 45, 45), 'Press ENTER to return to Menu')
            elif self.state == VICTORY:
                hi = '  NEW HI-SCORE!' if self.score >= self.hiscore else f'  Hi: {self.hiscore:,}'
                self._draw_overlay('VICTORY!', SCORE_COL,
                                   f'Score: {self.score:,}{hi}   — Press ENTER for Level 2!')
        pygame.display.flip()

    def _draw_world(self, cam_x):
        self.level.draw_background(self.screen, int(self.camera_x))

        for p in self.particles:
            p.draw(self.screen, 0)   # particles already in screen-space

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        for player in self.players:
            player.draw(self.screen, cam_x)
            player.draw_respawn_countdown(self.screen, cam_x)

        if self._magic_flash > 0:
            alpha = int(110 * self._magic_flash / 18)
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((50, 80, 220, alpha))
            self.screen.blit(flash, (0, 0))

        ui.draw_hud(self.screen, self.players, self.score, self.enemies)

    def _draw_menu(self):
        self.screen.fill(SKY_TOP)
        pygame.draw.rect(self.screen, SKY_BOT,   (0, SCREEN_H // 2, SCREEN_W, SCREEN_H // 2))
        pygame.draw.rect(self.screen, GRASS_COL, (0, SCREEN_H - 75, SCREEN_W, 75))
        pygame.draw.rect(self.screen, GROUND_COL,(0, SCREEN_H - 50, SCREEN_W, 50))

        # Title
        title  = self.font_title.render('LotemAxe', True, SCORE_COL)
        shadow = self.font_title.render('LotemAxe', True, (70, 55, 0))
        tr = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3))
        self.screen.blit(shadow, (tr.x + 4, tr.y + 4))
        self.screen.blit(title,  tr)

        sub = self.font_med.render('A Golden Axe Adventure', True, WHITE)
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3 + 88)))

        # Hi-score
        if self.hiscore > 0:
            hi = self.font_small.render(f'Hi-Score: {self.hiscore:,}', True, SCORE_COL)
            self.screen.blit(hi, hi.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3 + 122)))

        # Controls
        lines = [
            ('P1  Arrows/WASD : Move   Space : Jump   Ins : Attack   Del : Magic', WHITE),
            ('P2  J / L : Move   I : Jump   , : Attack   . : Magic',            (200, 220, 255)),
        ]
        for i, (text, col) in enumerate(lines):
            t = self.font_hint.render(text, True, col)
            self.screen.blit(t, t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 18 + i * 22)))

        # Start options
        opts = [
            'Press  1  for 1 Player',
            'Press  2  for 2 Players Co-op',
            'Press  ENTER  for 1 Player',
        ]
        blink = (pygame.time.get_ticks() // 520) % 2 == 0
        for i, text in enumerate(opts):
            col = WHITE if (i < 2 or blink) else (100, 100, 100)
            t = self.font_small.render(text, True, col)
            self.screen.blit(t, t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 80 + i * 28)))

    def _draw_color_select(self):
        self.screen.fill(SKY_TOP)
        pygame.draw.rect(self.screen, GROUND_COL, (0, SCREEN_H - 80, SCREEN_W, 80))
        pygame.draw.rect(self.screen, GRASS_COL,  (0, SCREEN_H - 80, SCREEN_W, 14))

        title = self.font_big.render('Choose Your Character', True, SCORE_COL)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 65)))

        opts   = self._COLOR_OPTIONS
        cmap   = self._COLOR_MAP
        num_p  = self.num_players
        cx_arr = getattr(self, '_color_cursor', [0, 0])
        _SPRITE_CHARS = {'asaf', 'lotem', 'gal', 'nitay'}
        spr_tick = pygame.time.get_ticks() // (sprites.ANIM_SPEED.get('idle', 12) * 1000 // 60)

        n_opts  = len(opts)
        # Available width per player; derive spacing and circle radius to always fit
        avail_w  = SCREEN_W if num_p == 1 else SCREEN_W // 2
        spacing  = min(90, (avail_w - 60) // n_opts)
        r        = min(30, spacing // 2 - 2)

        for pi in range(num_p):
            label  = f'P{pi + 1}  ←/→' if pi == 0 else 'P2  J/L'
            # Center in the player's available zone
            if num_p == 1:
                base_x = SCREEN_W // 2
            else:
                base_x = SCREEN_W // 4 + pi * SCREEN_W // 2
            lbl = self.font_med.render(label, True, WHITE)
            self.screen.blit(lbl, lbl.get_rect(center=(base_x, 130)))

            sel    = cx_arr[pi]
            for i, name in enumerate(opts):
                bx = base_x - (n_opts // 2) * spacing + i * spacing + spacing // 2
                by = 220
                is_sel = (i == sel)

                if name in _SPRITE_CHARS and sprites.is_ready():
                    # Show sprite idle frame as thumbnail
                    n_frames = sprites.frame_count(name, 'idle')
                    fidx = spr_tick % max(1, n_frames)
                    thumb = sprites.get_frame(name, 'idle', fidx, r * 2)
                    if thumb:
                        tw = thumb.get_width()
                        self.screen.blit(thumb, (bx - tw // 2, by - r))
                    else:
                        body, _, _ = cmap[name]
                        pygame.draw.circle(self.screen, body, (bx, by), r)
                else:
                    body, _, _ = cmap[name]
                    pygame.draw.circle(self.screen, body, (bx, by), r)

                if is_sel:
                    pygame.draw.circle(self.screen, WHITE, (bx, by), r + 5, 3)
                    n_surf = self.font_small.render(name.upper(), True, WHITE)
                    self.screen.blit(n_surf, n_surf.get_rect(center=(bx, by + r + 18)))

        hint = self.font_small.render('Press ENTER to start', True, WHITE)
        blink = (pygame.time.get_ticks() // 520) % 2 == 0
        if blink:
            self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 110)))

    def _draw_credits(self):
        self.screen.fill((8, 5, 18))

        title = self.font_title.render('YOU WIN!', True, SCORE_COL)
        sh    = self.font_title.render('YOU WIN!', True, (70, 55, 0))
        tr = title.get_rect(center=(SCREEN_W // 2, 85))
        self.screen.blit(sh,    (tr.x + 4, tr.y + 4))
        self.screen.blit(title, tr)

        hi_new = self.score >= self.hiscore
        score_col = (255, 220, 50) if hi_new else WHITE
        score_lbl = ('★ NEW HI-SCORE! ★' if hi_new else 'Final Score')
        s = self.font_med.render(f'{score_lbl}  {self.score:,}', True, score_col)
        self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, 170)))
        hi = self.font_small.render(f'All-time best: {self.hiscore:,}', True, (180, 180, 180))
        self.screen.blit(hi, hi.get_rect(center=(SCREEN_W // 2, 210)))

        lines = [
            ('Game Design & Code', WHITE),
            ('Lotem & Asaf', SCORE_COL),
            ('', WHITE),
            ('Art Assets', WHITE),
            ('KayKit — Kay Lousberg (CC0)', (180, 200, 255)),
            ('', WHITE),
            ('Engine', WHITE),
            ('Python + Pygame', (180, 200, 255)),
            ('', WHITE),
            ('Thanks for playing LotemAxe!', (220, 180, 255)),
        ]
        y = 270
        for text, col in lines:
            if text:
                t = self.font_small.render(text, True, col)
                self.screen.blit(t, t.get_rect(center=(SCREEN_W // 2, y)))
            y += 26

        blink = (pygame.time.get_ticks() // 600) % 2 == 0
        if blink:
            back = self.font_med.render('Press ENTER to return to Menu', True, WHITE)
            self.screen.blit(back, back.get_rect(center=(SCREEN_W // 2, SCREEN_H - 50)))

    def _draw_overlay(self, title, color, subtitle):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        t      = self.font_big.render(title, True, color)
        shadow = self.font_big.render(title, True, BLACK)
        tr = t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 55))
        self.screen.blit(shadow, (tr.x + 3, tr.y + 3))
        self.screen.blit(t, tr)

        s = self.font_med.render(subtitle, True, WHITE)
        self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))
