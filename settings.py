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
E_SPEED     = 1.7
E_HP        = 50
E_ATK_DMG   = 8
E_ATK_RANGE = 54
E_ATK_CD    = 68
E_HURT_DUR  = 16
E_SCORE     = 100

# --- Heavy (armoured bruiser) ---
H_W         = 46
H_H         = 76
H_SPEED     = 1.1
H_HP        = 110
H_ATK_DMG   = 15
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

# --- Per-character magic ---
P_MAGIC_RAD_ASAF    = 200    # wider shockwave
P_MAGIC_DMG_ASAF    = 80
P_PEE_RANGE         = 120    # Lotem forward stream
P_PEE_STUN          = 90
P_PEE_DMG           = 20
P_TORNADO_RAD       = 150    # Gal spinning radius
P_TORNADO_DMG       = 55
P_TORNADO_LAUNCH_VY = -8.0   # upward launch on hit
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
    (2200, [(3400, 'grunt'), (3600, 'heavy'), (3800, 'grunt')]),
    (2800, [(4000, 'grunt'), (4200, 'heavy'), (4400, 'grunt'), (4600, 'heavy')]),
    (3400, [(4800, 'heavy'), (5000, 'grunt')]),
    (3800, [(5200, 'grunt'), (5400, 'thrower'), (5600, 'grunt'), (5800, 'heavy'), (6000, 'thrower')]),
    (4700, [(6200, 'heavy'), (6400, 'jumper'), (6600, 'heavy')]),
    (5300, [(6800, 'healer'), (7000, 'heavy'), (7200, 'grunt'), (7400, 'thrower')]),
    (6400, [(BOSS_SPAWN, 'boss')]),
]

# Level 2 — denser, more heavies, tighter corridors
SPAWNS_L2 = [
    (  0, [(700,  'heavy'), (900,  'grunt')]),
    (300, [(1200, 'grunt'), (1400, 'heavy'), (1600, 'grunt')]),
    (700, [(1800, 'heavy'), (2000, 'heavy')]),
    (1100, [(2200, 'grunt'), (2400, 'heavy'), (2600, 'grunt'), (2800, 'heavy')]),
    (1700, [(3000, 'heavy'), (3200, 'grunt'), (3400, 'heavy')]),
    (2300, [(3600, 'grunt'), (3800, 'heavy'), (4000, 'grunt'), (4200, 'heavy')]),
    (3000, [(4400, 'jumper'), (4600, 'grunt'), (4800, 'jumper'), (5000, 'thrower')]),
    (3800, [(5200, 'heavy'), (5400, 'healer'), (5600, 'jumper')]),
    (4500, [(5800, 'thrower'), (6000, 'heavy'), (6200, 'jumper'), (6400, 'heavy')]),
    (5200, [(6600, 'healer'), (6800, 'jumper'), (7000, 'thrower')]),
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

# ---------------------------------------------------------------------------
# Boss upgrade (Long Sword Lunge + Ground Slam)
# ---------------------------------------------------------------------------
B_LUNGE_DMG    = 35
B_LUNGE_RANGE  = 180
B_LUNGE_CD     = 200   # frames between lunge attempts
B_LUNGE_WINDUP = 30    # telegraph glow frames
B_LUNGE_DUR    = 20    # active hitbox frames
B_SLAM_DMG     = 20
B_SLAM_RANGE   = 130   # shockwave radius
B_SLAM_VY      = -13.0
B_SLAM_CD      = 300
B_P2_CHARGE_CD = 120   # reduced charge cooldown in phase 2

# ---------------------------------------------------------------------------
# Teacher Boss (Level 2 boss)
# ---------------------------------------------------------------------------
TB_W           = 65
TB_H           = 95
TB_SPEED       = 1.4
TB_HP          = 500
TB_ATK_DMG     = 25    # Ruler Sweep damage
TB_ATK_RANGE   = 250
TB_ATK_CD      = 55
TB_CHALK_DMG   = 18
TB_CHALK_SPD   = 6
TB_CHALK_CD    = 90
TB_SCORE       = 4000
TB_BODY        = ( 80,  80,  90)
TB_HEAD        = (210, 180, 155)
TB_SUIT        = ( 55,  55,  65)
TB_REIN_CD     = 300   # frames between reinforcement waves (phase 2)

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
RB_DASH_CD     = 80
RB_DASH_SPD    = 12.0
RB_SPIN_DMG    = 12
RB_SPIN_RAD    = 100
RB_SCORE       = 3500
RB_BODY        = ( 30, 100, 170)
RB_HEAD        = ( 55, 140, 210)

# ---------------------------------------------------------------------------
# Yael (unlockable character — beat all 3 levels)
# ---------------------------------------------------------------------------
YAEL_SPEED_MULT = 1.2
YAEL_HP         = 75
YAEL_BODY       = (220,  80, 150)
YAEL_HEAD       = (245, 115, 185)
YAEL_CAPE       = (160,  40, 110)
YAEL_UNLOCK_FILE = 'yael_unlocked.txt'

# ---------------------------------------------------------------------------
# Falling hazards (active during boss fights from level 2+)
# ---------------------------------------------------------------------------
FALL_HAZARD_DMG    = 15
FALL_HAZARD_MIN_CD = 200
FALL_HAZARD_MAX_CD = 300
FALL_HAZARD_WARN   = 60    # shadow frames before impact
FALL_HAZARD_SPEED  = 7

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
    (2400, [(4100, 'heavy'), (4300, 'thrower'),(4500, 'jumper'), (4700, 'heavy')]),
    (3100, [(4900, 'jumper'),(5100, 'healer'), (5300, 'heavy'),  (5500, 'jumper')]),
    (3900, [(5700, 'thrower'),(5900, 'jumper'),(6100, 'heavy'),  (6300, 'thrower')]),
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
