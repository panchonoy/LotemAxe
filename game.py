import sys
import os
import math
import random
import pygame

from settings import *
from player import Player, P1_KEYS, P2_KEYS
from enemy import Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, Grunt, Heavy, Healer, Thrower, Jumper, Bomber, FlyingEye
from particles import spawn_hit, spawn_magic, spawn_death, spawn_pee, spawn_tornado, spawn_heal, spawn_explosion, spawn_lightning_chain
from level import Level
from pickups import Pickup
import ui
import sfx
import sprites
from touch import VirtualPad

# Game states
MENU         = 'menu'
COLOR_SELECT = 'color_select'
PLAYING      = 'playing'
GAME_OVER    = 'game_over'
VICTORY      = 'victory'
CREDITS      = 'credits'

HISCORE_FILE  = os.path.join(os.path.dirname(__file__), 'highscore.txt')

_yael_session = False   # True only after F6 or beating all 5 levels this session


def _is_yael_unlocked():
    return _yael_session


def _unlock_yael():
    global _yael_session
    _yael_session = True


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
        self._vpad       = VirtualPad()
        self._go_to_menu()

    # ------------------------------------------------------------------ setup
    def _init_fonts(self):
        self.font_title    = pygame.font.SysFont('Arial', 76, bold=True)
        self.font_big      = pygame.font.SysFont('Arial', 58, bold=True)
        self.font_med      = pygame.font.SysFont('Arial', 30, bold=True)
        self.font_small    = pygame.font.SysFont('Arial', 19)
        self.font_hint     = pygame.font.SysFont('Arial', 14)
        self.font_float    = pygame.font.SysFont('Arial', 16, bold=True)
        self.font_gameover = pygame.font.SysFont('Arial', 28, bold=True)

    def _new_game(self, level_num=1):
        # Preserve crystal counts when advancing levels (not on fresh start)
        _saved_crystals = [p.crystals for p in getattr(self, 'players', [])] if level_num > 1 else []

        self.current_level = level_num
        joy2 = self._joysticks[0] if self._joysticks else None

        c1 = getattr(self, 'p1_color', 'asaf'  if sprites.is_ready() else 'blue')
        c2 = getattr(self, 'p2_color', 'lotem' if sprites.is_ready() else 'red')

        _SPRITE_CHARS = {'asaf', 'lotem', 'gal', 'nitay', 'yael'}

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

        # Restore crystal counts from previous level
        for i, p in enumerate(self.players):
            if i < len(_saved_crystals):
                p.crystals = _saved_crystals[i]

        self.enemies   = []
        self.particles = []
        self.camera_x  = 0.0
        self.score     = 0
        self.level     = Level(level_num, num_players=self.num_players)

        if level_num == 1:
            pickup_data = PICKUPS_L1
        elif level_num == 2:
            pickup_data = PICKUPS_L2
        elif level_num == 3:
            pickup_data = PICKUPS_L3
        elif level_num == 4:
            pickup_data = PICKUPS_L4
        else:
            pickup_data = PICKUPS_L5
        self.pickups = [Pickup(wx, kind) for wx, kind in pickup_data]
        self._float_texts = []   # [(screen_x, screen_y, text, color, frames_left)]

        self._hit_stop          = 0
        self._shake             = 0.0
        self._magic_flash       = 0
        self._victory_wait      = 0
        self._gameover_line_idx = random.randint(0, len(self._GAMEOVER_LINES) - 1)
        self._twin_assists      = []  # [[world_x, direction, frames_left, hit_set]]
        self._lava_timers       = {}  # {player_index: frames_in_lava}
        self._tsunami_timers    = {}  # {player_index: frames_in_tsunami}

        # Falling hazards (active during boss fights from level 2+)
        self._hazards   = []  # [[world_x, y, vy, warn_t, type_idx]]
        self._hazard_cd = random.randint(FALL_HAZARD_MIN_CD, FALL_HAZARD_MAX_CD)
        self.rockets    = []  # live Rocket objects from RocketBoss
        self.blocks     = []  # live ToyBlock objects from DoriBoss

        # Background music — look for music/level{n}.mp3 / .ogg / .wav
        music_dir = os.path.join(os.path.dirname(__file__), 'music')
        sfx.stop_music()
        for ext in ('mp3', 'ogg', 'wav'):
            music_path = os.path.join(music_dir, f'level{level_num}.{ext}')
            if os.path.exists(music_path):
                sfx.play_music(music_path)
                break

    def _go_to_menu(self):
        """Reset game state, play entry music, switch to MENU."""
        self._new_game()
        sfx.stop_music()
        music_dir = os.path.join(os.path.dirname(__file__), 'music')
        for ext in ('mp3', 'ogg', 'wav'):
            p = os.path.join(music_dir, f'entry.{ext}')
            if os.path.exists(p):
                sfx.play_music(p)
                break
        self.state = MENU

    # ----------------------------------------------------------- color select
    # sprite chars use the sprite sheet; the rest are knight color palettes
    _COLOR_OPTIONS_BASE = ['asaf', 'lotem', 'gal', 'nitay', 'blue', 'red', 'green', 'gold']
    _COLOR_OPTIONS_YAEL = ['asaf', 'lotem', 'gal', 'nitay', 'yael', 'blue', 'red', 'green', 'gold']
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
        'yael':  (YAEL_BODY,      YAEL_HEAD,       YAEL_CAPE),
    }

    @property
    def _COLOR_OPTIONS(self):
        return self._COLOR_OPTIONS_YAEL if _is_yael_unlocked() else self._COLOR_OPTIONS_BASE

    def _handle_color_select(self, key):
        opts = self._COLOR_OPTIONS
        n = len(opts)
        ready = getattr(self, '_p_ready', [False, False])

        def _advance(idx, direction, other_idx):
            idx = (idx + direction) % n
            if self.num_players == 2 and idx == other_idx:
                idx = (idx + direction) % n
            return idx

        # P1: arrow keys only — unready if they change selection
        if key == pygame.K_LEFT:
            if not ready[0]:
                self._color_cursor[0] = _advance(self._color_cursor[0], -1, self._color_cursor[1])
                self.p1_color = opts[self._color_cursor[0]]
        elif key == pygame.K_RIGHT:
            if not ready[0]:
                self._color_cursor[0] = _advance(self._color_cursor[0], +1, self._color_cursor[1])
                self.p1_color = opts[self._color_cursor[0]]

        # P2: A/D keys only
        elif self.num_players == 2 and key == pygame.K_a:
            if not ready[1]:
                self._color_cursor[1] = _advance(self._color_cursor[1], -1, self._color_cursor[0])
                self.p2_color = opts[self._color_cursor[1]]
        elif self.num_players == 2 and key == pygame.K_d:
            if not ready[1]:
                self._color_cursor[1] = _advance(self._color_cursor[1], +1, self._color_cursor[0])
                self.p2_color = opts[self._color_cursor[1]]

        # F6 Yael unlock (secret)
        if key == pygame.K_F6:
            _unlock_yael()
            opts = self._COLOR_OPTIONS
            n = len(opts)
            if 'yael' in opts:
                yi = opts.index('yael')
                self._color_cursor[0] = yi
                self.p1_color = 'yael'
                ready[0] = False
                if self.num_players == 2 and self._color_cursor[1] == yi:
                    self._color_cursor[1] = (yi + 1) % n
                    self.p2_color = opts[self._color_cursor[1]]

        # Confirm: P1 = ENTER, P2 = W
        if key == pygame.K_RETURN:
            ready[0] = True
        if self.num_players == 2 and key == pygame.K_w:
            ready[1] = True

        self._p_ready = ready

        # Start when all required players are ready
        needed = self.num_players
        if sum(ready[:needed]) == needed:
            lv = getattr(self, '_start_level', 1)
            self._start_level = 1
            self._p_ready = [False, False]
            self._new_game(level_num=lv)
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
            self._vpad.handle_event(event)   # touch / mouse → virtual pad
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        if self.score > self.hiscore:
                            self.hiscore = self.score
                            _save_hiscore(self.hiscore)
                    self._go_to_menu()

                if self.state == MENU:
                    _LEVEL_KEYS = {
                        pygame.K_F1: 1, pygame.K_F2: 2, pygame.K_F3: 3,
                        pygame.K_F4: 4, pygame.K_F5: 5,
                    }
                    if event.key in _LEVEL_KEYS:
                        self._start_level = _LEVEL_KEYS[event.key]
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif event.key == pygame.K_1:
                        self.num_players = 1
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT
                    elif event.key in (pygame.K_2, pygame.K_RETURN):
                        self.num_players = 1 if event.key == pygame.K_RETURN else 2
                        self.p1_color = 'asaf'  if sprites.is_ready() else 'blue'
                        self.p2_color = 'lotem' if sprites.is_ready() else 'red'
                        opts = self._COLOR_OPTIONS
                        self._color_cursor = [opts.index(self.p1_color),
                                              opts.index(self.p2_color)]
                        self._p_ready = [False, False]
                        self.state = COLOR_SELECT

                elif self.state == COLOR_SELECT:
                    self._handle_color_select(event.key)

                elif self.state == VICTORY:
                    if event.key == pygame.K_RETURN:
                        next_level = self.current_level + 1
                        self._new_game(level_num=next_level)
                        self.state = PLAYING
                elif self.state == GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self._go_to_menu()
                elif self.state == CREDITS:
                    if event.key == pygame.K_RETURN:
                        self._go_to_menu()

            # Joystick start button
            if event.type == pygame.JOYBUTTONDOWN:
                if self.state == MENU and event.button == 9:  # Start
                    self.num_players = 1
                    self._new_game()
                    self.state = PLAYING
                elif self.state == VICTORY and event.button == 9:
                    next_level = self.current_level + 1
                    self._new_game(level_num=next_level)
                    self.state = PLAYING
                elif self.state in (GAME_OVER, CREDITS) and event.button == 9:
                    self._go_to_menu()

    # ------------------------------------------------------------------ update
    def _update(self):
        if self._hit_stop > 0:
            self._hit_stop -= 1
            return

        all_keys = pygame.key.get_pressed()

        # Feed touch controls into P1's virtual input
        self.players[0].virtual_input = self._vpad.get_state()

        # --- Player input ---
        platforms = self.level.platforms
        pits      = self.level.pits
        for player in self.players:
            player.handle_input(all_keys)
            player.update(int(self.camera_x), platforms, pits)
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
        # Tsunami camera-minimum: wave forces the viewport forward
        if self.current_level == 3 and getattr(self.level, 'tsunami_active', False):
            cam_min = max(0.0, self.level.tsunami_world_x - TSUNAMI_CAM_GAP)
        else:
            cam_min = 0.0
        self.camera_x = max(cam_min, min(self.camera_x, float(WORLD_W - SCREEN_W)))

        # --- Spawn new enemies ---
        new_spawns = self.level.update(int(self.camera_x))
        for e in new_spawns:
            if isinstance(e, Boss):
                sfx.play('boss_roar', 1.0)
        self.enemies.extend(new_spawns)

        # Swarm warning flash
        if self.level.swarm_active:
            self.level.swarm_active = False
            self._float_texts.append([SCREEN_W // 2, SCREEN_H // 3,
                                      '!! SWARM !!', (255, 55, 55), 110])
            self._shake       = max(self._shake, 10.0)
            self._magic_flash = max(self._magic_flash, 25)

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
            if isinstance(e, Bomber):
                continue   # death FX fires when fuse burns (handled below)
            scr_x = e.rect.centerx - int(self.camera_x)
            spawn_death(self.particles, scr_x, e.rect.centery, e.death_color)

        # Bomber explosions: fires after fuse countdown
        for enemy in self.enemies:
            if isinstance(enemy, Bomber) and enemy.pending_explosion:
                enemy.pending_explosion = False
                ecx = enemy.rect.centerx
                scr_x = ecx - int(self.camera_x)
                spawn_explosion(self.particles, scr_x, int(enemy.y + enemy.H // 2))
                self._shake = max(self._shake, 12.0)
                self._magic_flash = max(self._magic_flash, 12)
                for player in self.players:
                    if player.dead or player.out_of_lives:
                        continue
                    if abs(player.rect.centerx - ecx) < BOMBER_RADIUS:
                        player.take_damage(BOMBER_EXPL_DMG)
                # Splash damage to nearby minions (excludes bosses + the bomber itself)
                for other in self.enemies:
                    if other is enemy or other.dead:
                        continue
                    if isinstance(other, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)):
                        continue
                    if abs(other.rect.centerx - ecx) < BOMBER_RADIUS:
                        other.take_damage(BOMBER_EXPL_DMG // 2)
                scr_x_int = scr_x
                self._float_texts.append([scr_x_int, int(enemy.y) - 10,
                                          'BOOM!', (255, 120, 0), 40])

        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        # --- RocketBoss rockets ---
        for enemy in self.enemies:
            if isinstance(enemy, RocketBoss):
                if enemy.pending_rockets:
                    self.rockets.extend(enemy.pending_rockets)
                    enemy.pending_rockets = []
                if enemy.fire_text:
                    scr_x = enemy.rect.centerx - int(self.camera_x)
                    self._float_texts.append([scr_x, int(enemy.y) - 14,
                                              enemy.fire_text, (255, 100, 20), 45])
                    enemy.fire_text = ''

        live_rockets = []
        for rocket in self.rockets:
            rocket.update()
            if not rocket.alive:
                continue
            hit = False
            for player in self.players:
                if player.dead or player.out_of_lives or player.hurt_timer > 0:
                    continue
                if rocket.rect.colliderect(player.rect):
                    if player.take_damage(rocket.dmg):
                        self._shake = max(self._shake, 8.0)
                    scr_x = rocket.rect.centerx - int(self.camera_x)
                    spawn_explosion(self.particles, scr_x, rocket.rect.centery)
                    hit = True
                    break
            if not hit:
                live_rockets.append(rocket)
        self.rockets = live_rockets

        # --- DoriBoss toy blocks ---
        for enemy in self.enemies:
            if isinstance(enemy, DoriBoss):
                if enemy.pending_blocks:
                    self.blocks.extend(enemy.pending_blocks)
                    enemy.pending_blocks = []
                if enemy.block_text:
                    scr_x = enemy.rect.centerx - int(self.camera_x)
                    self._float_texts.append([scr_x, int(enemy.y) - 14,
                                              enemy.block_text, (238, 202, 45), 50])
                    enemy.block_text = ''

        live_blocks = []
        for block in self.blocks:
            block.update()
            if not block.alive:
                continue
            hit = False
            for player in self.players:
                if player.dead or player.out_of_lives or player.hurt_timer > 0:
                    continue
                if block.rect.colliderect(player.rect):
                    if player.take_damage(block.dmg):
                        self._shake = max(self._shake, 6.0)
                    scr_x = block.rect.centerx - int(self.camera_x)
                    spawn_hit(self.particles, scr_x, block.rect.centery)
                    hit = True
                    break
            if not hit:
                live_blocks.append(block)
        self.blocks = live_blocks

        # --- Projectile hits (Thrower + TeacherBoss chalk) ---
        for enemy in self.enemies:
            if hasattr(enemy, 'pending_hits'):
                for player, dmg in enemy.pending_hits:
                    if player.take_damage(dmg):
                        self._shake = max(self._shake, 4.0)
                        sfx.play('hit', 0.5)

        # --- TeacherBoss: reinforcement spawns + SILENCE! float text ---
        for enemy in self.enemies:
            if hasattr(enemy, 'pending_spawns') and enemy.pending_spawns:
                for gx in enemy.pending_spawns:
                    gx = max(50, min(int(gx), WORLD_W - 50))
                    self.enemies.append(self.level.spawn_grunt(gx))
                enemy.pending_spawns = []
            if hasattr(enemy, 'swing_text') and enemy.swing_text:
                scr_x = enemy.rect.centerx - int(self.camera_x)
                self._float_texts.append([scr_x, enemy.rect.top - 10, enemy.swing_text,
                                          (255, 80, 80), 55])
                enemy.swing_text = ''

        # --- Enemy platform correction ---
        if platforms:
            for enemy in self.enemies:
                if not enemy.dead and not enemy.on_ground and enemy.vy >= 0:
                    ecx = enemy.x + enemy.W // 2
                    for wx, wy, pw in platforms:
                        if wx <= ecx <= wx + pw:
                            prev_feet = (enemy.y + enemy.H) - enemy.vy
                            curr_feet = enemy.y + enemy.H
                            if prev_feet <= wy <= curr_feet:
                                enemy.y = float(wy - enemy.H)
                                enemy.vy = 0.0
                                enemy.on_ground = True
                                break

        # --- Pit collision ---
        # Decrement pit-avoidance cooldowns once per frame (outside pit loop)
        for enemy in self.enemies:
            if getattr(enemy, '_pit_avoid_cd', 0) > 0:
                enemy._pit_avoid_cd -= 1

        for pit_x1, pit_x2 in self.level.pits:
            # Players: always bounce out — don't wait for hurt_timer to expire
            for player in self.players:
                if player.dead or player.out_of_lives:
                    continue
                pcx = int(player.x) + P_W // 2
                if pit_x1 <= pcx <= pit_x2 and player.y > GROUND_Y + 20:
                    # Snap back above ground and eject to nearest pit edge
                    player.vy = JUMP_VY * 0.85
                    player.y  = float(GROUND_Y - P_H)
                    if pcx - pit_x1 < pit_x2 - pcx:
                        player.x = float(pit_x1 - P_W - 2)
                    else:
                        player.x = float(pit_x2 + 2)
                    self._shake = max(self._shake, 5.0)
                    player.take_damage(30)  # damage attempt (blocked by hurt_timer = intentional)

            # --- Pit avoidance AI ---
            # Runs every frame: hard-walls enemies out of the pit, no intentional fall-ins
            GUARD = 22   # px before pit edge to start blocking
            for enemy in self.enemies:
                if enemy.dead or not enemy.on_ground:
                    continue
                if isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, FlyingEye)):
                    continue
                ecx = enemy.rect.centerx
                if not (pit_x1 - GUARD <= ecx <= pit_x2 + GUARD):
                    continue

                closer_to_left = (ecx - pit_x1) < (pit_x2 - ecx)
                toward_pit = 1 if closer_to_left else -1

                # Hard reposition if inside kill zone (safety net)
                if pit_x1 <= ecx <= pit_x2:
                    enemy.x = float(pit_x1 - enemy.W) if closer_to_left else float(pit_x2 + 1)
                    enemy.vx = -float(toward_pit) * enemy.SPEED
                    enemy.facing = 1 if enemy.vx > 0 else -1

                # Block forward movement toward the pit every frame
                elif ecx < pit_x1 and enemy.vx > 0:
                    enemy.x  = float(pit_x1 - enemy.W)
                    enemy.vx = 0.0
                elif ecx > pit_x2 and enemy.vx < 0:
                    enemy.x  = float(pit_x2 + 1)
                    enemy.vx = 0.0
                else:
                    continue   # inside guard zone but moving away — nothing to do

                # Jumpers jump across (cooldown prevents repeated triggering)
                if isinstance(enemy, Jumper) and getattr(enemy, '_pit_avoid_cd', 0) == 0:
                    enemy.vy = JP_LEAP_VY
                    enemy.on_ground = False
                    enemy._is_leaping = True
                    enemy.vx = float(toward_pit) * max(abs(enemy.vx) if enemy.vx else 1.0,
                                                        enemy.SPEED * 2.5)
                    enemy._pit_avoid_cd = 55

            # Enemies: die immediately when they walk into the pit
            for enemy in self.enemies:
                if not enemy.dead and enemy.on_ground:
                    if isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss, FlyingEye)):
                        continue
                    ecx = enemy.rect.centerx
                    if pit_x1 <= ecx <= pit_x2:
                        pit_cx = (pit_x1 + pit_x2) // 2
                        enemy.dead       = True
                        enemy._die_timer = 36
                        enemy._die_vx    = 2.5 if pit_cx > ecx else -2.5
                        enemy._die_vy    = 3.0   # fall downward
                        self.score += enemy.score_value
                        scr_x = ecx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery,
                                    enemy.death_color)

        # --- Lava: enemy avoidance + typed damage ---
        # Heavy, Healer, and FlyingEye are immune; others take slow damage and avoid the edge
        _LAVA_IMMUNE = (Heavy, Healer, FlyingEye)
        for lx1, lx2 in self.level.lava:
            for enemy in self.enemies:
                if enemy.dead:
                    continue
                if isinstance(enemy, _LAVA_IMMUNE):
                    continue  # immune — walk right through
                ecx = enemy.rect.centerx
                # Smart avoidance: stop 12px before the lava edge
                if enemy.on_ground and not isinstance(enemy, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)):
                    if enemy.vx > 0 and lx1 - 12 < ecx < lx1 + 8:
                        enemy.vx = 0.0  # halt before left edge
                    elif enemy.vx < 0 and lx2 - 8 < ecx < lx2 + 12:
                        enemy.vx = 0.0  # halt before right edge

                if enemy.on_ground and lx1 <= ecx <= lx2:
                    # Slow tick damage (1 HP every 30 frames per enemy)
                    eid = id(enemy)
                    self._lava_timers[eid] = self._lava_timers.get(eid, 0) + 1
                    if self._lava_timers[eid] >= 30:
                        self._lava_timers[eid] = 0
                        enemy.hp = max(0, enemy.hp - 1)
                        if enemy.hp == 0:
                            enemy.dead       = True
                            enemy._die_timer = 36
                            enemy._die_vx    = 0.0
                            enemy._die_vy    = -4.0
                            self.score += enemy.score_value
                            scr_x = ecx - int(self.camera_x)
                            spawn_death(self.particles, scr_x, enemy.rect.centery,
                                        enemy.death_color)
                else:
                    self._lava_timers.pop(id(enemy), None)

        # --- Lava damage to players ---
        for i, player in enumerate(self.players):
            if player.dead or player.out_of_lives:
                continue
            pcx = int(player.x) + P_W // 2
            in_lava = player.on_ground and any(lx1 <= pcx <= lx2 for lx1, lx2 in self.level.lava)
            if in_lava:
                self._lava_timers[i] = self._lava_timers.get(i, 0) + 1
                if self._lava_timers[i] >= LAVA_INTERVAL:
                    self._lava_timers[i] = 0
                    player.hp = max(0, player.hp - LAVA_DMG)
                    self._shake = max(self._shake, 2.0)
                    if player.hp == 0 and not player.dead:
                        player._die()
            else:
                self._lava_timers[i] = 0

        # --- Tsunami damage to players (Level 3) ---
        if self.current_level == 3 and getattr(self.level, 'tsunami_active', False):
            tsw = self.level.tsunami_world_x
            for i, player in enumerate(self.players):
                if player.dead or player.out_of_lives:
                    continue
                if player.x < tsw:
                    self._tsunami_timers[i] = self._tsunami_timers.get(i, 0) + 1
                    if self._tsunami_timers[i] >= TSUNAMI_INTERVAL:
                        self._tsunami_timers[i] = 0
                        player.hp = max(0, player.hp - TSUNAMI_DMG)
                        self._shake = max(self._shake, 3.0)
                        if player.hp == 0 and not player.dead:
                            player._die()
                else:
                    self._tsunami_timers[i] = 0

        # --- Healer ally healing ---
        for enemy in self.enemies:
            if not enemy.dead and hasattr(enemy, '_heal_cd') and enemy._heal_cd == 0:
                for target in self.enemies:
                    if (target is not enemy and not target.dead and
                            target.hp < target.max_hp and
                            abs(target.rect.centerx - enemy.rect.centerx) < 300):
                        target.hp = min(target.max_hp, target.hp + HL_HEAL_AMT)
                        enemy._heal_cd = HL_HEAL_CD
                        mid_x = (target.rect.centerx + enemy.rect.centerx) // 2 - int(self.camera_x)
                        mid_y = min(target.rect.centery, enemy.rect.centery)
                        spawn_heal(self.particles, mid_x, mid_y)
                        break

        # --- Twin assists (Nitay magic) ---
        for ta in self._twin_assists:
            ta[0] += P_TWIN_SPEED * ta[1]
            ta[2] -= 1
            ta_rect = pygame.Rect(int(ta[0]) - 20, GROUND_Y - P_H - 5, 40, P_H + 10)
            for enemy in self.enemies:
                if enemy not in ta[3] and not enemy.dead:
                    if ta_rect.colliderect(enemy.rect):
                        ta[3].add(enemy)
                        if enemy.take_damage(P_TWIN_DMG, int(ta[1]), 30):
                            scr_x = enemy.rect.centerx - int(self.camera_x)
                            spawn_hit(self.particles, scr_x, enemy.rect.centery)
                            if enemy.dead:
                                self.score += enemy.score_value
                                spawn_death(self.particles, scr_x, enemy.rect.centery,
                                            enemy.death_color)
        self._twin_assists = [ta for ta in self._twin_assists if ta[2] > 0]
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]

        # --- Pickups ---
        for pickup in self.pickups:
            for player in self.players:
                if player.dead or player.out_of_lives:
                    continue
                label = pickup.try_collect(player)
                if label:
                    scr_x = int(player.x) - int(self.camera_x) + 19
                    scr_y = int(player.y) - 20
                    col   = (80, 220, 255) if 'Crystal' in label else (255, 220, 80) if 'Woof' in label else (80, 220, 80)
                    self._float_texts.append([scr_x, scr_y, label, col, 50])

        # --- Falling hazards (level 2+ during boss fight) ---
        if self.current_level >= 2 and self.level.boss_triggered:
            self._hazard_cd -= 1
            if self._hazard_cd <= 0:
                self._hazard_cd = random.randint(FALL_HAZARD_MIN_CD, FALL_HAZARD_MAX_CD)
                # Spawn above a living player's area
                living = [p for p in self.players if not p.out_of_lives and not p.dead]
                if living:
                    tx = random.choice(living)
                    wx = int(tx.x) + random.randint(-120, 120)
                    wx = max(50, min(wx, WORLD_W - 50))
                    self._hazards.append([wx, -30.0, 0.0,
                                          FALL_HAZARD_WARN, random.randint(0, 2)])

            hit_players = set()
            for hz in self._hazards:
                hz[3] -= 1   # warn_t countdown
                if hz[3] <= 0:
                    hz[2] += FALL_HAZARD_SPEED   # falling vy (stored as distance per frame)
                    hz[1] += hz[2]               # y increases downward (screen coords)
                    if hz[1] >= GROUND_Y - 20:
                        # Impact!
                        hz_scr_x = hz[0] - int(self.camera_x)
                        for player in self.players:
                            if player.dead or player.out_of_lives:
                                continue
                            if abs(player.x + P_W // 2 - hz[0]) < 30:
                                if player not in hit_players:
                                    hit_players.add(player)
                                    if player.take_damage(FALL_HAZARD_DMG):
                                        self._shake = max(self._shake, 4.0)
                        hz[1] = GROUND_Y + 100   # mark for removal
            self._hazards = [hz for hz in self._hazards if hz[1] < GROUND_Y + 80]

        # --- Particles ---
        self.particles = [p for p in self.particles if p.update()]

        # --- Decay ---
        self._shake       = max(0.0, self._shake - 0.4)
        if self._magic_flash > 0: self._magic_flash -= 1
        for ft in self._float_texts:
            ft[1] -= 1   # float upward
            ft[4] -= 1   # tick down lifetime
        self._float_texts = [ft for ft in self._float_texts if ft[4] > 0]

        # --- Win/Lose ---
        boss_dead = self.level.boss_triggered and not any(
            isinstance(e, (Boss, TeacherBoss, RollerBoss, RocketBoss, DoriBoss)) and not e.dead
            for e in self.enemies
        )
        if boss_dead:
            self._victory_wait += 1
            if self._victory_wait > 100:
                if self.score > self.hiscore:
                    self.hiscore = self.score
                    _save_hiscore(self.hiscore)
                if self.current_level < 5:
                    self.state = VICTORY          # → next level
                else:
                    _unlock_yael()               # beat all 5 levels!
                    self.state = CREDITS

        all_out = all(p.out_of_lives for p in self.players)
        if all_out:
            self.state = GAME_OVER

    # ------------------------------------------------------------------ magic
    def _do_magic(self, caster):
        char = getattr(caster, 'char_name', '')
        if   char == 'lotem': self._magic_lotem(caster)
        elif char == 'gal':   self._magic_gal(caster)
        elif char == 'nitay': self._magic_nitay(caster)
        else:                 self._magic_asaf(caster)
        self._shake       = 12.0
        self._magic_flash = 18
        sfx.play('magic', 0.8)

    def _magic_asaf(self, caster):
        """Power Slam — wide shockwave in all directions."""
        cx = int(caster.x) + P_W // 2
        cy = int(caster.y) + P_H // 2
        for enemy in self.enemies:
            if abs(enemy.rect.centerx - cx) < P_MAGIC_RAD_ASAF:
                kb_dir = 1 if enemy.rect.centerx >= cx else -1
                if enemy.take_damage(P_MAGIC_DMG_ASAF, kb_dir, 0):
                    if enemy.dead:
                        self.score += enemy.score_value
                        scr_x = enemy.rect.centerx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        spawn_magic(self.particles, cx - int(self.camera_x), cy, P_MAGIC_RAD_ASAF)

    def _magic_lotem(self, caster):
        """Pee Stream — forward cone that stuns enemies."""
        cx = int(caster.x) + P_W // 2
        cy = int(caster.y) + P_H // 2
        for enemy in self.enemies:
            dx = enemy.rect.centerx - cx
            in_front = (caster.facing == 1 and dx > 0) or (caster.facing == -1 and dx < 0)
            if in_front and abs(dx) <= P_PEE_RANGE and abs(enemy.rect.centery - cy) < 45:
                if enemy.take_damage(P_PEE_DMG, caster.facing, P_PEE_STUN):
                    if enemy.dead:
                        self.score += enemy.score_value
                        scr_x = enemy.rect.centerx - int(self.camera_x)
                        spawn_death(self.particles, scr_x, enemy.rect.centery, enemy.death_color)
        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        spawn_pee(self.particles, cx - int(self.camera_x), cy, caster.facing)

    def _magic_gal(self, caster):
        """Chain Lightning — zaps up to 5 enemies, bolt jumps to the nearest next."""
        cam = int(self.camera_x)
        cx  = int(caster.x) + P_W // 2
        cy  = int(caster.y) + P_H // 2

        # Build chain: start at caster, greedily pick nearest un-hit enemy
        remaining = [e for e in self.enemies if not e.dead]
        chain_world  = [(cx, cy)]          # world-space positions for distance calc
        chain_screen = [(cx - cam, cy)]    # screen-space for drawing

        prev_x, prev_y = cx, cy
        for _ in range(P_CHAIN_MAX):
            if not remaining:
                break
            # Nearest enemy within range of previous node
            candidates = [
                e for e in remaining
                if math.hypot(e.rect.centerx - prev_x, e.rect.centery - prev_y) <= P_CHAIN_RANGE
            ]
            if not candidates:
                break
            target = min(candidates, key=lambda e: math.hypot(
                e.rect.centerx - prev_x, e.rect.centery - prev_y))
            remaining.remove(target)

            kb_dir = 1 if target.rect.centerx >= cx else -1
            if target.take_damage(P_CHAIN_DMG, kb_dir, 20):
                if target.dead:
                    self.score += target.score_value
                    scr_x = target.rect.centerx - cam
                    spawn_death(self.particles, scr_x, target.rect.centery, target.death_color)

            prev_x, prev_y = target.rect.centerx, target.rect.centery
            chain_world.append((prev_x, prev_y))
            chain_screen.append((prev_x - cam, prev_y))

        self.enemies = [e for e in self.enemies if not e.dead or e._die_timer > 0]
        if len(chain_screen) > 1:
            spawn_lightning_chain(self.particles, chain_screen)

    def _magic_nitay(self, caster):
        """Twin Assist — ghost Gal flies across the screen dealing damage."""
        direction = float(caster.facing)
        if caster.facing == 1:
            start_wx = float(int(self.camera_x) - 60)
        else:
            start_wx = float(int(self.camera_x) + SCREEN_W + 60)
        self._twin_assists.append([start_wx, direction, 80, set()])
        spawn_magic(self.particles,
                    int(caster.x) + P_W // 2 - int(self.camera_x),
                    int(caster.y) + P_H // 2,
                    60)

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill((0, 0, 0))  # clear first — prevents ghost pixels in fullscreen
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
                self._draw_game_over()
            elif self.state == VICTORY:
                hi = '  NEW HI-SCORE!' if self.score >= self.hiscore else f'  Hi: {self.hiscore:,}'
                next_lv = self.current_level + 1
                self._draw_overlay('VICTORY!', SCORE_COL,
                                   f'Score: {self.score:,}{hi}   — Press ENTER for Level {next_lv}!')
        pygame.display.flip()

    def _draw_world(self, cam_x):
        self.level.draw_background(self.screen, int(self.camera_x))

        for pickup in self.pickups:
            pickup.draw(self.screen, cam_x)

        for p in self.particles:
            p.draw(self.screen, 0)   # particles already in screen-space

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        for rocket in self.rockets:
            rocket.draw(self.screen, cam_x)

        for block in self.blocks:
            block.draw(self.screen, cam_x)

        # Twin assists (Nitay magic) — ghost Gal sprinting across the screen
        for ta in self._twin_assists:
            scr_x = int(ta[0]) - cam_x
            if -80 <= scr_x <= SCREEN_W + 80:
                t_norm = 1.0 - ta[2] / 80.0
                edge_fade = 1.0 - abs(t_norm - 0.5) * 2.0
                base_alpha = max(40, int(180 * edge_fade))

                # Animated Gal sprite, tinted electric-purple
                anim_tick = (80 - ta[2]) // 6
                flip_sprite = ta[1] < 0
                ghost = sprites.get_frame('gal', 'run', anim_tick, P_H, flip_sprite)
                if ghost is not None:
                    ghost = ghost.copy()
                    # Purple-electric tint: keep blues, cut green, boost red a bit
                    ghost.fill((210, 80, 255), special_flags=pygame.BLEND_RGB_MULT)
                    ghost.set_alpha(base_alpha)
                    self.screen.blit(ghost, (scr_x - ghost.get_width() // 2, GROUND_Y - P_H))

                # Small purple glow on the ground
                sw, sh = 50, 10
                shad = pygame.Surface((sw, sh), pygame.SRCALPHA)
                pygame.draw.ellipse(shad, (180, 60, 255, base_alpha // 2), (0, 0, sw, sh))
                self.screen.blit(shad, (scr_x - sw // 2, GROUND_Y + 2))

        # Falling hazards
        for hz in self._hazards:
            sx = hz[0] - cam_x
            if not (-40 <= sx <= SCREEN_W + 40):
                continue
            ht = hz[4]  # type: 0=bag, 1=broccoli, 2=clothing
            if hz[3] > 0:
                # Shadow warning on ground
                warn_alpha = int(180 * (1 - hz[3] / FALL_HAZARD_WARN))
                shadow_w   = max(8, int(40 * (1 - hz[3] / FALL_HAZARD_WARN)))
                shad = pygame.Surface((shadow_w, 8), pygame.SRCALPHA)
                shad.fill((0, 0, 0, warn_alpha))
                self.screen.blit(shad, (sx - shadow_w // 2, GROUND_Y - 4))
            else:
                sy = int(hz[1])
                if ht == 0:   # school bag (dark rectangle with straps)
                    pygame.draw.rect(self.screen, (40, 35, 80),  (sx - 14, sy - 20, 28, 22))
                    pygame.draw.rect(self.screen, (60, 55, 100), (sx - 10, sy - 22, 20, 4))
                    pygame.draw.line(self.screen, (40, 35, 80), (sx - 8, sy - 20), (sx - 14, sy + 2), 3)
                    pygame.draw.line(self.screen, (40, 35, 80), (sx + 8, sy - 20), (sx + 14, sy + 2), 3)
                elif ht == 1: # broccoli
                    pygame.draw.rect(self.screen, (60, 140, 30), (sx - 4, sy - 10, 8, 16))
                    pygame.draw.circle(self.screen, (40, 120, 20), (sx, sy - 14), 12)
                    pygame.draw.circle(self.screen, (60, 150, 35), (sx - 6, sy - 12), 7)
                    pygame.draw.circle(self.screen, (60, 150, 35), (sx + 6, sy - 12), 7)
                else:         # clothing (floppy shirt)
                    pts = [(sx - 14, sy - 14), (sx + 14, sy - 14),
                           (sx + 18, sy + 6),  (sx - 18, sy + 6)]
                    pygame.draw.polygon(self.screen, (180, 80, 80), pts)
                    pygame.draw.rect(self.screen, (200, 100, 100), (sx - 12, sy - 14, 24, 5))

        for player in self.players:
            player.draw(self.screen, cam_x)
            player.draw_respawn_countdown(self.screen, cam_x)

        if self._magic_flash > 0:
            alpha = int(110 * self._magic_flash / 18)
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((50, 80, 220, alpha))
            self.screen.blit(flash, (0, 0))

        # --- Tsunami HUD warning (Level 3) ---
        if self.current_level == 3:
            lv = self.level
            if not lv.tsunami_active and lv._tsunami_delay <= 240:
                # Countdown warning before the wave starts
                frames_left = lv._tsunami_delay
                secs = math.ceil(frames_left / 60)
                blink = (lv._tsunami_delay // 15) % 2 == 0
                if blink:
                    warn = self.font_gameover.render(f'TSUNAMI IN {secs}s!', True, (255, 80, 40))
                    self.screen.blit(warn, warn.get_rect(center=(SCREEN_W // 2, 80)))
            elif lv.tsunami_active:
                # Show a small "WAVE" danger tag at the left side of screen
                sx = int(lv.tsunami_world_x - self.camera_x)
                if 0 < sx < SCREEN_W:
                    blink2 = (int(lv.tsunami_world_x) // 12) % 2 == 0
                    if blink2:
                        tag = self.font_float.render('WAVE ►', True, (100, 200, 255))
                        self.screen.blit(tag, (max(0, sx - 50), SCREEN_H // 2 - 10))

        ui.draw_hud(self.screen, self.players, self.score, self.enemies)

        self._vpad.draw(self.screen)

        for fx, fy, text, col, life in self._float_texts:
            max_life = 110 if text.startswith('!!') else 55
            alpha = max(0, int(255 * life / max_life))
            font  = self.font_big if text.startswith('!!') else self.font_float
            surf  = font.render(text, True, col)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (fx - surf.get_width() // 2, fy))

    def _draw_menu(self):
        # Lazy-load and cache the entry screen background
        if not hasattr(self, '_entry_bg'):
            try:
                raw = pygame.image.load(
                    os.path.join(os.path.dirname(__file__), 'images', 'entry_screen.png')
                ).convert()
                self._entry_bg = pygame.transform.scale(raw, (SCREEN_W, SCREEN_H))
            except Exception:
                self._entry_bg = None

        if self._entry_bg:
            self.screen.blit(self._entry_bg, (0, 0))
            # Dark overlay so text stays readable
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 110))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(SKY_TOP)
            pygame.draw.rect(self.screen, SKY_BOT,   (0, SCREEN_H // 2, SCREEN_W, SCREEN_H // 2))
            pygame.draw.rect(self.screen, GRASS_COL, (0, SCREEN_H - 75, SCREEN_W, 75))
            pygame.draw.rect(self.screen, GROUND_COL,(0, SCREEN_H - 50, SCREEN_W, 50))

        # Title
        title  = self.font_title.render('The NOYS', True, SCORE_COL)
        shadow = self.font_title.render('The NOYS', True, (70, 55, 0))
        tr = title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3))
        self.screen.blit(shadow, (tr.x + 4, tr.y + 4))
        self.screen.blit(title,  tr)

        # Hi-score
        if self.hiscore > 0:
            hi = self.font_small.render(f'Hi-Score: {self.hiscore:,}', True, SCORE_COL)
            self.screen.blit(hi, hi.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3 + 88)))

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
            self.screen.blit(t, t.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20 + i * 28)))


    def _draw_color_select(self):
        self.screen.fill(SKY_TOP)
        pygame.draw.rect(self.screen, GROUND_COL, (0, SCREEN_H - 80, SCREEN_W, 80))
        pygame.draw.rect(self.screen, GRASS_COL,  (0, SCREEN_H - 80, SCREEN_W, 14))

        title = self.font_big.render('Choose Your Character', True, SCORE_COL)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 65)))

        lv = getattr(self, '_start_level', 1)
        if lv > 1:
            lv_label = self.font_small.render(f'Starting at Level {lv}', True, (255, 200, 80))
            self.screen.blit(lv_label, lv_label.get_rect(center=(SCREEN_W // 2, 105)))

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

        ready  = getattr(self, '_p_ready', [False, False])
        p_keys = ['← → then ENTER', 'A  D  then W']

        for pi in range(num_p):
            is_ready = ready[pi]
            col    = (80, 220, 80) if is_ready else WHITE
            status = '  READY!' if is_ready else f'  {p_keys[pi]}'
            label  = f'P{pi + 1}{status}'
            if num_p == 1:
                base_x = SCREEN_W // 2
            else:
                base_x = SCREEN_W // 4 + pi * SCREEN_W // 2
            lbl = self.font_med.render(label, True, col)
            self.screen.blit(lbl, lbl.get_rect(center=(base_x, 130)))

            sel = cx_arr[pi]
            for i, name in enumerate(opts):
                bx = base_x - (n_opts // 2) * spacing + i * spacing + spacing // 2
                by = 220
                is_sel = (i == sel)

                if name in _SPRITE_CHARS and sprites.is_ready():
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
                    ring_col = (80, 220, 80) if is_ready else WHITE
                    pygame.draw.circle(self.screen, ring_col, (bx, by), r + 5, 3)
                    n_surf = self.font_small.render(name.upper(), True, ring_col)
                    self.screen.blit(n_surf, n_surf.get_rect(center=(bx, by + r + 18)))

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

        yael_line = ('★ YAEL UNLOCKED! ★', (255, 120, 220)) if _is_yael_unlocked() else ('', WHITE)
        lines = [
            ('Game Design & Code', WHITE),
            ('Lotem & Asaf', SCORE_COL),
            ('', WHITE),
            yael_line,
            ('Art Assets', WHITE),
            ('KayKit — Kay Lousberg (CC0)', (180, 200, 255)),
            ('', WHITE),
            ('Engine', WHITE),
            ('Python + Pygame', (180, 200, 255)),
            ('', WHITE),
            ('Thanks for playing The NOYS!', (220, 180, 255)),
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

    # Game over screen with random Hebrew/English flavor text
    _GAMEOVER_LINES = [
        ('אמא אמרה שעת שינה',  'Mom said it\'s bedtime.'),
        ('לך לסדר את החדר',              'Go clean your room.'),
        ('יש לך שיעורי בית',        'You have homework!'),
        ('אין קינוח בשבילך',   'No dessert for you!'),
    ]

    def _draw_game_over(self):
        self._draw_overlay('GAME OVER', (210, 45, 45), 'Press ENTER to return to Menu')

        heb, eng = self._GAMEOVER_LINES[self._gameover_line_idx]

        # Try Hebrew first; fall back to English if the font can't render it
        flavor_surf = None
        try:
            flavor_surf = self.font_gameover.render(heb, True, (255, 220, 80))
            # Sanity check: if all glyphs rendered as boxes (width too small), fallback
            if flavor_surf.get_width() < 30:
                raise ValueError('font missing glyphs')
        except Exception:
            flavor_surf = None

        if flavor_surf is None:
            flavor_surf = self.font_med.render(eng, True, (255, 220, 80))

        self.screen.blit(flavor_surf,
                         flavor_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 68)))
