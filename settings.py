SCREEN_W = 1024
SCREEN_H = 576
FPS      = 60
TITLE    = "LotemAxe"

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

# Lives & respawn
PLAYER_LIVES       = 3
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
    (3800, [(5200, 'grunt'), (5400, 'heavy'), (5600, 'grunt'), (5800, 'heavy'), (6000, 'grunt')]),
    (4700, [(6200, 'heavy'), (6400, 'grunt'), (6600, 'heavy')]),
    (5300, [(6800, 'grunt'), (7000, 'heavy'), (7200, 'grunt'), (7400, 'heavy')]),
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
    (3000, [(4400, 'heavy'), (4600, 'grunt'), (4800, 'heavy'), (5000, 'grunt')]),
    (3800, [(5200, 'heavy'), (5400, 'heavy'), (5600, 'grunt')]),
    (4500, [(5800, 'grunt'), (6000, 'heavy'), (6200, 'grunt'), (6400, 'heavy')]),
    (5200, [(6600, 'heavy'), (6800, 'grunt'), (7000, 'heavy')]),
    (6000, [(7200, 'grunt'), (7400, 'heavy'), (7500, 'grunt')]),
    (6400, [(BOSS_SPAWN, 'boss')]),
]
