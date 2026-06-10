SCREEN_W = 1024
SCREEN_H = 576
FPS      = 60
TITLE    = "The NOYS"

# Camera: player appears at roughly CAM_LEAD px from left
CAM_LEAD = SCREEN_W // 4   # 256

# --- Colors ---
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
SKY_TOP    = ( 25,  70, 150)
SKY_BOT    = ( 90, 150, 215)
MOUNTAIN   = ( 55,  70,  95)
GROUND_COL = ( 70,  46,  20)
GRASS_COL  = ( 45, 105,  30)
TREE_COL   = ( 28,  75,  22)
TRUNK_COL  = ( 85,  55,  18)

PLAYER_BODY  = ( 45,  85, 195)
PLAYER_HEAD  = ( 65, 108, 218)
PLAYER_HAIR  = ( 28,  18,   8)
PLAYER2_BODY = (195,  65,  45)    # P2 = red knight
PLAYER2_HEAD = (218,  90,  65)
SWORD_COL    = (205, 212, 228)
SWORD_COMBO  = (240, 210,  50)   # golden sword on finisher
GUARD_COL    = (145, 148, 168)
SHIELD_COL   = (140,  20,  20)
CAPE_COL     = ( 28,  50, 155)
CAPE2_COL    = (155,  28,  28)   # P2 cape

ENEMY_BODY  = (160,  80,  30)
ENEMY_HEAD  = (190, 120,  70)
HELMET_COL  = ( 80,  45,  15)
AXE_HANDLE  = (140,  80,  20)
AXE_BLADE   = (195, 200, 210)

HEAVY_BODY  = (100,  55,  20)    # darker, armoured
HEAVY_HEAD  = (150,  95,  55)
HEAVY_ARMOR = ( 60,  40,  15)
CLUB_COL    = (110,  70,  25)
CLUB_HEAD   = (160, 160, 175)

BOSS_BODY   = (105,  22, 125)
BOSS_HEAD   = (145,  42, 165)
BOSS_ARMOR  = ( 65,  12,  75)
BOSS_CROWN  = (198, 168,  28)

HP_GREEN   = ( 42, 192,  52)
HP_RED     = (192,  32,  32)
HP_BG      = ( 25,   5,   5)
MAGIC_COL  = ( 42,  72, 212)
MAGIC_BG   = (  8,  18,  75)
SCORE_COL  = (238, 208,  48)
UI_PANEL   = (  8,   8,   8)
LIFE_COL   = (220,  50,  50)

HIT_COL    = (255, 198,  38)
SPARK_COL  = (255, 238,  95)
MAGIC_FX   = ( 75, 125, 255)

# --- World ---
GROUND_Y   = 420
WORLD_W    = 8500
BOSS_SPAWN = 7700

# --- Physics ---
GRAVITY  = 0.65
JUMP_VY  = -14.5

# --- Player (Knight) ---
P_W           = 38
P_H           = 68
P_SPEED       = 5
P_HP          = 100
P_MAGIC       = 100
P_ATK_DMG     = 25
P_ATK_W       = 70
P_ATK_H       = 36
P_ATK_DUR     = 12
P_ATK_CD      = 26
P_MAGIC_DMG   = 65
P_MAGIC_RAD   = 145
P_MAGIC_CD    = 90
P_MAGIC_COST  = 30
P_HURT_DUR    = 22

# Combo system
P_COMBO_WINDOW = 42    # frames to continue a combo chain
P_COMBO2_DMG   = 30   # 2nd hit damage
P_COMBO3_DMG   = 48   # 3rd hit finisher damage
P_COMBO3_W     = 108  # wider hitbox on finisher
P_COMBO3_STUN  = 52   # extra stun frames applied to hit enemy
P_COMBO3_DUR   = 20   # finisher active frames (longer swing)

# Heavy attack (Insert+Delete mapped; single powerful hit, no combo)
P_HEAVY_DMG = 67   # ~1.4× combo finisher
P_HEAVY_W   = 108  # wide hitbox
P_HEAVY_DUR = 18
P_HEAVY_CD  = 52

# Lives & respawn
PLAYER_LIVES       = 3
PLAYER_LIVES_MAX   = 5   # max lives achievable via crystals
RESPAWN_DELAY      = 180   # frames (~3 s)
INVINCIBILITY_DUR  = 120   # post-respawn invincibility frames

# --- Grunt (Barbarian minion) ---
E_W         = 36
E_H         = 64
E_SPEED     = 1.9    # was 1.7 — more aggressive
E_HP        = 55    # was 50
E_ATK_DMG   = 10   # was 8
E_ATK_RANGE = 54
E_ATK_CD    = 62   # slightly faster attacks
E_HURT_DUR  = 16
E_SCORE     = 100

# --- Heavy (armoured bruiser) ---
H_W         = 46
H_H         = 76
H_SPEED     = 1.25  # was 1.1
H_HP        = 120   # was 110
H_ATK_DMG   = 18   # was 15
H_ATK_RANGE = 64
H_ATK_CD    = 55
H_HURT_DUR  = 18
H_SCORE     = 200

# --- Boss ---
B_W         = 60
B_H         = 90
B_SPEED     = 1.5
B_HP        = 400
B_ATK_DMG   = 22
B_ATK_RANGE = 78
B_ATK_CD    = 45
B_SCORE     = 2500

# --- Thrower (ranged axe-tosser) ---
THROWER_BODY = (170, 135,  40)
THROWER_HEAD = (200, 165,  70)
TR_HP        = 45
TR_ATK_DMG   = 10
TR_ATK_RANGE = 270
TR_THROW_CD  = 110
TR_RETREAT   = 80
TR_SPEED     = 1.4
TR_SCORE     = 150
TR_PROJ_SPD  = 5

# --- Jumper (acrobatic leaper) ---
JUMPER_BODY  = (140, 100, 160)
JUMPER_HEAD  = (170, 130, 195)
JP_HP        = 45
JP_ATK_DMG   = 12
JP_ATK_RANGE = 50
JP_LEAP_CD   = 90
JP_LEAP_VY   = -13.0
JP_SPEED     = 1.6
JP_SCORE     = 150

# --- Healer (support unit that heals allies) ---
HEALER_BODY  = ( 80, 160,  80)
HEALER_HEAD  = (110, 190, 110)
HEALER_ROBE  = ( 50, 130,  50)
HL_HP        = 35
HL_HEAL_CD   = 180
HL_HEAL_AMT  = 20
HL_RETREAT   = 110
HL_SPEED     = 1.6
HL_SCORE     = 200

# --- Bomber (explodes on death after a short fuse) ---
BOMBER_BODY    = ( 70, 150,  40)
BOMBER_HEAD    = (110, 195,  70)
BOMBER_HP      = 35
BOMBER_ATK_DMG = 8
BOMBER_RANGE   = 52
BOMBER_SPEED   = 2.3
BOMBER_FUSE    = 48    # frames from death-hit to explosion
BOMBER_RADIUS  = 90   # explosion damage radius (px)
BOMBER_EXPL_DMG = 28  # explosion damage to players

# --- Cannoneer (artillery lobber — fires arcing cannonballs) ---
CN_BODY       = ( 70,  45, 120)
CN_HEAD       = (100,  75, 155)
CN_ARM        = ( 45,  28,  88)
CN_HP         = 55
CN_SPEED      = 1.3
CN_SCORE      = 210
CN_FIRE_CD    = 145   # frames between shots
CN_FIRE_MIN   = 180   # won't fire if player is closer than this
CN_FIRE_MAX   = 490   # won't fire if player is farther than this
CN_RETREAT    = 140   # runs away when player is within this range
CN_LAUNCH_VY  = 12.5  # upward launch speed; arc height ~120 px at GRAVITY=0.65
CN_PROJ_DMG   = 22
CN_PROJ_SIZE  = 8     # cannonball radius (draw + hitbox)
CN_BLAST_RAD  = 75    # ground blast radius
BOMBER_SCORE   = 175

# --- Per-character magic ---
P_MAGIC_RAD_ASAF    = 200    # wider shockwave
P_MAGIC_DMG_ASAF    = 80
P_PEE_RANGE         = 120    # Lotem forward stream
P_PEE_STUN          = 90
P_PEE_DMG           = 20
P_TORNADO_RAD       = 150    # Gal spinning radius (kept for fallback)
P_TORNADO_DMG       = 55
P_TORNADO_LAUNCH_VY = -8.0
P_CHAIN_DMG         = 32     # Gal chain lightning — damage per zap
P_CHAIN_RANGE       = 290    # max world-px jump between enemies
P_CHAIN_MAX         = 5      # max enemies hit in one chain
P_TWIN_DMG          = 40     # Nitay twin assist
P_TWIN_SPEED        = 8

# --- Level 2 (cave/dungeon) colors ---
CAVE_SKY_TOP  = ( 10,   8,  20)
CAVE_SKY_BOT  = ( 25,  18,  45)
CAVE_WALL     = ( 48,  35,  60)
CAVE_GROUND   = ( 32,  22,  42)
CAVE_GRASS    = ( 55,  38,  70)
CAVE_STALA    = ( 38,  28,  50)   # stalactite color
TORCH_COL     = (220, 140,  30)
TORCH_GLOW    = (255, 200,  80)

# ---------------------------------------------------------------------------
# Spawn groups: (camera_trigger_x, [(world_x, kind), ...])
# kind = 'grunt' | 'heavy' | 'boss'
# ---------------------------------------------------------------------------
SPAWNS = [
    (  0, [(900,  'grunt'), (1060, 'grunt')]),
    (400, [(1350, 'grunt'), (1500, 'grunt'), (1650, 'grunt')]),
    (800, [(1900, 'grunt'), (2100, 'grunt')]),
    (1200, [(2300, 'grunt'), (2450, 'heavy'), (2600, 'grunt'), (2800, 'grunt')]),
    (1800, [(3000, 'heavy'), (3200, 'grunt')]),
    # --- SWARM (L1) ---
    (2400, [(3500, 'swarm')]),
    (2800, [(4000, 'grunt'), (4200, 'heavy'), (4400, 'grunt'), (4600, 'heavy')]),
    (3400, [(4800, 'heavy'), (5000, 'grunt')]),
    (3800, [(5200, 'grunt'), (5400, 'thrower'), (5600, 'bomber'), (5800, 'heavy'), (6000, 'cannoneer')]),
    (4700, [(6200, 'heavy'), (6400, 'cannoneer'), (6600, 'heavy')]),
    (5300, [(6800, 'healer'), (7000, 'cannoneer'), (7200, 'grunt'), (7400, 'thrower')]),
    (6400, [(BOSS_SPAWN, 'boss')]),
]

# Level 2 — denser, more heavies, tighter corridors
SPAWNS_L2 = [
    (  0, [(700,  'heavy'), (900,  'grunt')]),
    (300, [(1200, 'grunt'), (1400, 'heavy'), (1600, 'grunt')]),
    (700, [(1800, 'heavy'), (2000, 'heavy')]),
    (1100, [(2200, 'grunt'), (2400, 'heavy'), (2600, 'grunt'), (2800, 'heavy')]),
    (1700, [(3000, 'heavy'), (3200, 'grunt'), (3400, 'heavy')]),
    # --- SWARM (L2) ---
    (2400, [(3700, 'swarm')]),
    (3000, [(4400, 'jumper'), (4600, 'cannoneer'), (4800, 'jumper'), (5000, 'thrower')]),
    (3800, [(5200, 'heavy'), (5400, 'healer'), (5600, 'cannoneer')]),
    (4500, [(5800, 'cannoneer'), (6000, 'bomber'), (6200, 'jumper'), (6400, 'heavy')]),
    (5200, [(6600, 'healer'), (6800, 'heavy'), (7000, 'grunt')]),
    (6000, [(7200, 'grunt'), (7400, 'heavy'), (7500, 'grunt')]),
    (6400, [(BOSS_SPAWN, 'boss')]),
]

# ---------------------------------------------------------------------------
# Pickup placements: (world_x, kind)
# kind = 'milk' | 'salmon' | 'crystal' | 'dog'
# ---------------------------------------------------------------------------
PICKUPS_L1 = [
    (1000, 'crystal'), (1800, 'milk'),
    (2700, 'crystal'), (3500, 'salmon'),
    (4300, 'crystal'), (5100, 'milk'),
    (5900, 'crystal'), (6500, 'salmon'),
    (7100, 'crystal'), (7400, 'dog'),
]

PICKUPS_L2 = [
    (800,  'crystal'), (1500, 'salmon'),
    (2500, 'crystal'), (3300, 'milk'),
    (4200, 'crystal'), (5100, 'salmon'),
    (5900, 'crystal'), (6300, 'milk'),
    (7100, 'crystal'), (7300, 'dog'),
]

# ---------------------------------------------------------------------------
# Platforms: (world_x, surface_y, width) — player/enemy can land on top
# ---------------------------------------------------------------------------
PLATFORMS_L1 = [
    (2300, GROUND_Y - 115, 180),
    (4100, GROUND_Y - 120, 160),
    (5800, GROUND_Y - 110, 180),
]
PLATFORMS_L2 = [
    (1700, GROUND_Y - 120, 160),
    (3600, GROUND_Y - 130, 140),
    (5300, GROUND_Y - 110, 170),
]

# ---------------------------------------------------------------------------
# Pits: (world_x_start, world_x_end) — players fall through; enemies die
# ---------------------------------------------------------------------------
PITS_L1 = [
    (3600, 3750),
    (5500, 5620),
]
PITS_L2 = [
    (2700, 2840),
    (4800, 4940),
    (6200, 6340),
]

# ---------------------------------------------------------------------------
# Lava zones: (world_x_start, world_x_end) — ground-level heat hazard
# ---------------------------------------------------------------------------
LAVA_L1 = [
    (2500, 2660),
    (4400, 4560),
]
LAVA_L2 = [
    (1300, 1490),
    (3100, 3290),
    (5000, 5190),
]
LAVA_DMG      = 15   # HP removed per tick
LAVA_INTERVAL = 45   # frames between lava damage ticks (~0.75 s)

# --- Tsunami (Level 3) ---
TSUNAMI_SPEED    = 1.6   # world-px per frame the wave advances
TSUNAMI_DMG      = 15    # HP removed per tick when caught in the wave
TSUNAMI_INTERVAL = 40    # frames between tsunami damage ticks
TSUNAMI_DELAY    = 360   # frames grace period before wave starts moving (~6 s)
TSUNAMI_CAM_GAP  = 450   # how many px ahead of the wave the camera minimum sits

# ---------------------------------------------------------------------------
# Boss upgrade (Long Sword Lunge + Ground Slam)
# ---------------------------------------------------------------------------
B_LUNGE_DMG    = 35
B_LUNGE_RANGE  = 180
B_LUNGE_CD     = 130   # frames between lunge attempts
B_LUNGE_WINDUP = 26    # telegraph glow frames
B_LUNGE_DUR    = 22    # active hitbox frames
B_SLAM_DMG     = 20
B_SLAM_RANGE   = 130   # shockwave radius
B_SLAM_VY      = -13.0
B_SLAM_CD      = 240
B_P2_CHARGE_CD = 80    # reduced charge cooldown in phase 2

# ---------------------------------------------------------------------------
# Teacher Boss (Level 2 boss)
# ---------------------------------------------------------------------------
TB_W           = 65
TB_H           = 95
TB_SPEED       = 1.23
TB_HP          = 350
TB_ATK_DMG     = 22    # Ruler Sweep damage
TB_ATK_RANGE   = 180
TB_ATK_CD      = 43
TB_CHALK_DMG   = 16
TB_CHALK_SPD   = 4.4
TB_CHALK_CD    = 240
TB_CHALK_RANGE = 380   # max world-px chalk travels before fading out
TB_SCORE       = 4000
TB_BODY        = ( 80,  80,  90)
TB_HEAD        = (210, 180, 155)
TB_SUIT        = ( 55,  55,  65)
TB_REIN_CD     = 340   # frames between reinforcement waves (phase 2)

# ---------------------------------------------------------------------------
# Roller Boss (Level 3 boss)
# ---------------------------------------------------------------------------
RB_W           = 55
RB_H           = 85
RB_SPEED       = 3.5
RB_HP          = 350
RB_ATK_DMG     = 18
RB_ATK_RANGE   = 70
RB_ATK_CD      = 50
RB_DASH_DMG    = 22
RB_DASH_CD     = 52
RB_DASH_SPD    = 12.0
RB_SPIN_DMG    = 12
RB_SPIN_RAD    = 100
RB_SCORE       = 3500
RB_BODY        = ( 30, 100, 170)
RB_HEAD        = ( 55, 140, 210)

# ---------------------------------------------------------------------------
# Yael (unlockable character — beat all 5 levels)
# ---------------------------------------------------------------------------
YAEL_SPEED_MULT = 1.2
YAEL_HP         = 75
YAEL_BODY       = (220,  80, 150)
YAEL_HEAD       = (245, 115, 185)
YAEL_CAPE       = (160,  40, 110)
YAEL_UNLOCK_FILE = 'yael_unlocked.txt'

# ---------------------------------------------------------------------------
# DoriBoss (Level 5 final boss — giant, powerful, blonde baby)
# ---------------------------------------------------------------------------
DORI_W          = 96
DORI_H          = 140
DORI_SPEED      = 2.0
DORI_HP         = 700
DORI_ATK_DMG    = 30
DORI_ATK_RANGE  = 110
DORI_ATK_CD     = 36
DORI_BLOCK_DMG  = 42
DORI_BLOCK_SPD  = 5
DORI_BLOCK_CD   = 80     # frames between block throws
DORI_BLOCK_CD2  = 45     # phase 2 throw cooldown
DORI_POUND_DMG  = 55     # shockwave damage on landing
DORI_POUND_CD   = 170    # frames between ground pounds
DORI_CHARGE_SPD = 9.0    # phase-2 tantrum charge speed
DORI_CHARGE_DUR = 36     # frames the charge lasts
DORI_CHARGE_CD  = 140    # frames between charges
DORI_SCORE      = 8000
DORI_SKIN       = (235, 190, 168)   # peach/pink skin
DORI_SKIN_DARK  = (210, 160, 138)   # shading
DORI_HAIR       = (238, 202,  45)   # golden blonde hair
DORI_DIAPER     = (242, 242, 252)   # white diaper
DORI_PIN        = (200, 180, 220)   # safety pin
DORI_BLUSH      = (230, 140, 135)   # cheek blush
DORI_EYE_IRIS   = ( 80, 130, 210)   # baby-blue iris

# ---------------------------------------------------------------------------
# Level 5 (Dori's Nursery) colors
# ---------------------------------------------------------------------------
NURSERY_SKY_TOP  = (195, 220, 248)   # soft blue
NURSERY_SKY_BOT  = (228, 240, 255)   # lighter near horizon
NURSERY_WALL     = (210, 195, 225)   # lavender wall
NURSERY_CARPET   = (185, 158, 122)   # warm tan carpet
NURSERY_CARPET2  = (165, 138, 102)   # carpet stripe
NURSERY_BLOCK_R  = (218,  72,  72)   # red toy block
NURSERY_BLOCK_B  = ( 72, 115, 218)   # blue toy block
NURSERY_BLOCK_Y  = (238, 195,  45)   # yellow toy block
NURSERY_BLOCK_G  = ( 72, 175,  80)   # green toy block
NURSERY_STAR     = (255, 238, 130)   # wall star
NURSERY_MOON     = (248, 225, 130)   # crescent moon

# ---------------------------------------------------------------------------
# Level 5 data
# ---------------------------------------------------------------------------
BOSS_SPAWN_L5 = 7800

SPAWNS_L5 = [
    (  0, [(700,  'heavy'),  (900,  'eye')]),
    (300, [(1200, 'jumper'), (1400, 'heavy'),  (1600, 'thrower'), (1800, 'eye')]),
    (700, [(2000, 'heavy'),  (2200, 'cannoneer'), (2400, 'thrower'), (2600, 'eye')]),
    (1200, [(2800, 'cannoneer'),(3000, 'heavy'),(3200, 'jumper'), (3400, 'bomber'), (3600, 'eye')]),
    (1800, [(3800, 'eye'),   (4000, 'healer'), (4200, 'cannoneer'), (4400, 'heavy'), (4600, 'eye')]),
    (2200, [(4800, 'swarm')]),
    (2800, [(5000, 'cannoneer'),(5200, 'eye'),  (5400, 'thrower'), (5600, 'bomber'), (5800, 'heavy')]),
    (3400, [(6000, 'jumper'), (6200, 'cannoneer'),(6400, 'healer'),(6600, 'bomber')]),
    (4100, [(6800, 'cannoneer'),(7000, 'eye'),  (7200, 'thrower'), (7400, 'heavy')]),
    (6500, [(BOSS_SPAWN_L5, 'boss')]),
]

PLATFORMS_L5 = [
    (1500, GROUND_Y - 140, 180),
    (3400, GROUND_Y - 130, 170),
    (5500, GROUND_Y - 140, 180),
]

PITS_L5 = [
    (2200, 2380),
    (4000, 4180),
    (6000, 6180),
    (7100, 7280),
]

LAVA_L5 = [
    (1000, 1200),
    (3200, 3400),
    (5200, 5400),
    (6700, 6900),
]

PICKUPS_L5 = [
    (800,  'crystal'), (1700, 'milk'),
    (2900, 'crystal'), (3700, 'salmon'),
    (4600, 'crystal'), (5500, 'milk'),
    (6400, 'crystal'), (7000, 'salmon'),
    (7300, 'crystal'), (7600, 'dog'),
]

# ---------------------------------------------------------------------------
# Falling hazards (active during boss fights from level 2+)
# ---------------------------------------------------------------------------
FALL_HAZARD_DMG    = 15
FALL_HAZARD_MIN_CD = 200
FALL_HAZARD_MAX_CD = 300
FALL_HAZARD_WARN   = 60    # shadow frames before impact
FALL_HAZARD_SPEED  = 4

# Falling crystal boxes
FBOX_CD_MIN   = 540   # min frames between spawns (~9 s)
FBOX_CD_MAX   = 900   # max frames between spawns (~15 s)
FBOX_VY_INIT  = 0.5   # initial fall speed (px/frame)
FBOX_GRAVITY  = 0.038 # acceleration per frame
FBOX_CRYSTALS = 2     # reward on collect

# ---------------------------------------------------------------------------
# Destructible Props (world_x, kind) per level
# kind: 'barrel' | 'crate' | 'vase'
# ---------------------------------------------------------------------------
PROPS_L1 = [
    (850,  'crate'), (1300, 'barrel'),(1900, 'vase'),
    (2600, 'crate'), (3300, 'barrel'),(4000, 'vase'),
    (4900, 'barrel'),(5700, 'crate'), (6400, 'barrel'),(7100, 'vase'),
]
PROPS_L2 = [
    (700,  'barrel'),(1100, 'crate'), (1800, 'vase'),
    (2500, 'barrel'),(3100, 'crate'), (4000, 'barrel'),
    (5000, 'vase'),  (5800, 'crate'), (6500, 'barrel'),(7000, 'vase'),
]
PROPS_L3 = [
    (900,  'vase'),  (1400, 'crate'), (2100, 'barrel'),
    (2900, 'crate'), (3600, 'barrel'),(4400, 'vase'),
    (5200, 'barrel'),(6000, 'crate'), (6600, 'vase'), (7000, 'barrel'),
]
PROPS_L4 = [
    (800,  'crate'), (1300, 'barrel'),(2000, 'vase'),
    (2700, 'crate'), (3500, 'barrel'),(4300, 'vase'),
    (5100, 'barrel'),(5900, 'crate'), (6700, 'vase'), (7200, 'barrel'),
]
PROPS_L5 = [
    (750,  'vase'),  (1300, 'crate'), (2100, 'barrel'),
    (2800, 'vase'),  (3600, 'crate'), (4500, 'barrel'),
    (5300, 'vase'),  (6100, 'crate'), (6800, 'barrel'),(7200, 'vase'),
]
PROP_DROP_CHANCE = 0.30   # chance a broken prop drops a pickup

# ---------------------------------------------------------------------------
# Hazard Zones (x1, x2, kind) — persistent toggling floor hazards
# kind: 'acid' (L2) | 'electric' (L3) | 'vent' (L4) | 'slime' (L5)
# ---------------------------------------------------------------------------
HAZARD_ZONE_WARN   = 75    # warning phase (flickering)
HAZARD_ZONE_ACTIVE = 60    # active phase (damages player)
HAZARD_ZONE_COOL   = 90    # clear phase (safe)
HAZARD_ZONE_CYCLE  = 225   # WARN + ACTIVE + COOL
HAZARD_ZONE_DMG    = 8     # HP damage per tick
HAZARD_ZONE_TICK   = 30    # frames between damage ticks

HAZARD_ZONES_L2 = [(1600, 1760, 'acid'),     (3400, 3560, 'acid'),    (5600, 5760, 'acid')]
HAZARD_ZONES_L3 = [(1200, 1370, 'electric'), (3000, 3170, 'electric'),(5800, 5970, 'electric')]
HAZARD_ZONES_L4 = [(1000, 1180, 'vent'),     (3600, 3780, 'vent'),    (6200, 6380, 'vent')]
HAZARD_ZONES_L5 = [(1300, 1470, 'slime'),    (3500, 3670, 'slime'),   (5700, 5870, 'slime')]

# ---------------------------------------------------------------------------
# Buddy Special (2-player sync magic → Team Blast)
# ---------------------------------------------------------------------------
BUDDY_SYNC_WINDOW = 45    # frames both players must use magic within
BUDDY_SYNC_DIST   = 300   # max px apart to trigger
BUDDY_BLAST_DMG   = 40    # damage to all on-screen enemies
BUDDY_BLAST_STUN  = 90    # stun frames applied to enemies
BUDDY_INVINC      = 90    # invincibility frames for both players
BUDDY_CD          = 600   # cooldown frames before buddy special can fire again

# ---------------------------------------------------------------------------
# Berserk Mode
# ---------------------------------------------------------------------------
BERSERK_SPEED_MULT   = 1.35   # enemy walk speed multiplier
BERSERK_DMG_MULT     = 1.4    # enemy attack damage multiplier
BERSERK_SCORE_MULT   = 2      # score multiplier for all kills

# ---------------------------------------------------------------------------
# Hit-Streak Combo Life
# ---------------------------------------------------------------------------
COMBO_LIFE_THRESHOLD = 20     # consecutive hits without taking damage → +1 life

# ---------------------------------------------------------------------------
# Star Rating thresholds (fraction of total max HP taken as damage)
# ---------------------------------------------------------------------------
STAR_3_DMG_FRAC = 0.25   # took < 25% of max HP → 3 stars
STAR_2_DMG_FRAC = 0.65   # took < 65% of max HP → 2 stars

# ---------------------------------------------------------------------------
# Level 3 (city / skate park) colors
# ---------------------------------------------------------------------------
CITY_SKY_TOP   = (155, 180, 215)
CITY_SKY_BOT   = (195, 215, 235)
CITY_GROUND    = ( 80,  78,  72)
CITY_ROAD_LINE = (220, 215, 200)
CITY_BUILDING  = (110, 105, 100)
CITY_WINDOW    = (180, 210, 240)

# ---------------------------------------------------------------------------
# Level 3 data
# ---------------------------------------------------------------------------
BOSS_SPAWN_L3 = 7200

SPAWNS_L3 = [
    (  0, [(800,  'grunt'),  (1000, 'jumper')]),
    (400, [(1300, 'jumper'), (1500, 'heavy'),  (1700, 'jumper')]),
    (800, [(2000, 'thrower'),(2200, 'grunt'),  (2400, 'jumper')]),
    (1200, [(2700, 'heavy'), (2900, 'jumper'), (3100, 'thrower'), (3300, 'grunt')]),
    (1800, [(3500, 'jumper'),(3700, 'healer'), (3900, 'jumper')]),
    # --- SWARM (L3) ---
    (2200, [(4000, 'swarm')]),
    (2700, [(4100, 'heavy'), (4300, 'cannoneer'),(4500, 'jumper'), (4700, 'heavy')]),
    (3100, [(4900, 'jumper'),(5100, 'healer'),  (5300, 'cannoneer'),(5500, 'jumper')]),
    (3900, [(5700, 'cannoneer'),(5900, 'bomber'),(6100, 'heavy'), (6300, 'thrower')]),
    (4600, [(6500, 'jumper'),(6700, 'heavy'),  (6900, 'jumper')]),
    (5300, [(7000, 'grunt'), (7100, 'thrower'),(7150, 'heavy')]),
    (6400, [(BOSS_SPAWN_L3, 'boss')]),
]

PLATFORMS_L3 = [
    (1500, GROUND_Y - 125, 170),
    (3200, GROUND_Y - 115, 180),
    (5100, GROUND_Y - 130, 150),
]

PITS_L3 = [
    (2200, 2340),
    (4600, 4740),
    (6000, 6140),
]

LAVA_L3 = [
    (1800, 1970),
    (3900, 4080),
]

PICKUPS_L3 = [
    (900,  'crystal'), (1600, 'milk'),
    (2800, 'crystal'), (3700, 'salmon'),
    (4500, 'crystal'), (5300, 'milk'),
    (6200, 'crystal'), (6700, 'salmon'),
    (7000, 'crystal'), (7100, 'dog'),
]

# ---------------------------------------------------------------------------
# FlyingEye (aerial minion — immune to pits and lava, swoops to attack)
# ---------------------------------------------------------------------------
FE_W         = 44
FE_H         = 44
FE_FLOAT_Y   = GROUND_Y - 115   # hover height (world y)
FE_SPEED      = 2.9
FE_HP         = 38
FE_ATK_DMG    = 14
FE_ATK_RANGE  = 58
FE_ATK_CD     = 65
FE_HURT_DUR   = 12
FE_SCORE      = 180
FE_EYE_COL    = (200, 55, 30)
FE_WING_COL   = (100, 55, 28)
FE_SPIT_CD    = 155   # frames between spit shots
FE_SPIT_SPD   = 5.5   # pixels per frame
FE_SPIT_DMG   = 11    # damage per spit hit
FE_SPIT_RANGE = 400   # max horizontal px to trigger a spit

# ---------------------------------------------------------------------------
# RocketBoss (Level 4 boss: rocket launcher + phase-2 double volley)
# ---------------------------------------------------------------------------
ROKB_W            = 72
ROKB_H            = 102
ROKB_SPEED        = 1.7
ROKB_HP           = 650
ROKB_ATK_DMG      = 22
ROKB_ATK_RANGE    = 90
ROKB_ATK_CD       = 55
ROKB_ROCKET_DMG   = 35
ROKB_ROCKET_SPD   = 7
ROKB_ROCKET_CD    = 110
ROKB_SCORE        = 6000
ROKB_BODY         = (160, 55, 20)
ROKB_HEAD         = (205, 100, 55)
ROKB_ARMOR        = ( 95,  38, 15)
ROKB_LAUNCHER_COL = ( 50,  50, 60)

# ---------------------------------------------------------------------------
# Level 4 (lava inferno cave) colors
# ---------------------------------------------------------------------------
INFERNO_SKY_TOP = ( 35,   5,   2)
INFERNO_SKY_BOT = ( 78,  18,   8)
INFERNO_GROUND  = ( 55,  20,   8)
INFERNO_ROCK    = ( 72,  28,  12)
INFERNO_CEILING = ( 40,  12,   4)

# ---------------------------------------------------------------------------
# Level 4 data
# ---------------------------------------------------------------------------
BOSS_SPAWN_L4 = 7800

SPAWNS_L4 = [
    (  0, [(700,  'heavy'),  (900,  'jumper')]),
    (300, [(1200, 'jumper'), (1400, 'heavy'),  (1600, 'bomber')]),
    (700, [(1900, 'heavy'),  (2100, 'jumper'), (2300, 'cannoneer'), (2500, 'eye')]),
    (1200, [(2600, 'cannoneer'),(2800, 'heavy'),(3000, 'jumper'), (3200, 'bomber')]),
    (1800, [(3400, 'eye'),   (3600, 'healer'), (3800, 'cannoneer'), (3950, 'eye')]),
    (2200, [(4000, 'swarm')]),
    (2800, [(4200, 'heavy'),  (4400, 'cannoneer'),(4600, 'thrower'), (4800, 'heavy')]),
    (3400, [(5000, 'bomber'), (5200, 'jumper'), (5400, 'cannoneer'), (5600, 'eye')]),
    (4100, [(5800, 'cannoneer'),(6000, 'bomber'),(6200, 'eye'),  (6400, 'thrower')]),
    (4900, [(6600, 'heavy'),  (6800, 'eye'),   (7000, 'bomber')]),
    (5600, [(7200, 'thrower'),(7300, 'heavy'),  (7400, 'jumper')]),
    (6500, [(BOSS_SPAWN_L4, 'boss')]),
]

PLATFORMS_L4 = [
    (1800, GROUND_Y - 130, 160),
    (3500, GROUND_Y - 120, 170),
    (5600, GROUND_Y - 125, 155),
]

PITS_L4 = [
    (2400, 2560),
    (4200, 4380),
    (5900, 6060),
    (6800, 6960),
]

LAVA_L4 = [
    (1200, 1420),
    (3000, 3220),
    (4900, 5100),
    (6500, 6680),
]

PICKUPS_L4 = [
    (800,  'crystal'), (1700, 'milk'),
    (2900, 'crystal'), (3800, 'salmon'),
    (4700, 'crystal'), (5500, 'milk'),
    (6300, 'crystal'), (6900, 'salmon'),
    (7200, 'crystal'), (7600, 'dog'),
]
