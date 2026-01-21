# game.config.py

# ===== GAME CONSTANTS =====
# game screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 16 # DO NOT CHANGE!!!
BG_COLOR = '#4F42B5'

# world boundaries
WORLD_LEFT = -6400
WORLD_RIGHT = 6400
WORLD_TOP = 795
WORLD_BOTTOM = 3520

# frames
dt = 1/60
FPS = 60

# ===== PLAYER CONSTANTS =====
# player stats
PLAYER_SPEED = 120
PLAYER_HEALTH = 100
PLAYER_MAX_POWER = 100 # power core
POWER_REGEN = 5 # regen per second
BOOST_COST = 10
TORPEDO_COST = 15
BOOST_SPEED = 200
TAKE_DAMAGE_CD = 1000 # takes damage per second instead of consecutively

# HP regeneration
HP_REGEN_LEVEL_REQUIRED = 3
HP_REGEN_DELAY = 5.0 # seconds after taking damage
HP_REGEN_MIN = 1
HP_REGEN_MAX = 5

# ===== MONSTERS CONSTANTS =====
# monsters stats
DETECTION_RANGE = 400
LOSE_INTEREST_RANGE = 500

MONSTER_TYPES = {
    "angler_fish": {
        "hp": 60,
        "speed": (50, 70),
        "damage": 10,
        "xp": 15,
        "frames": 6,
        "size": (40, 40), 
    },
    "lamprey": {
        "hp": 20,
        "speed": (50, 70),
        "damage": 10,
        "xp": 10,
        "frames": 4,
        "size": (35, 35),
    },
    "squid": {
        "hp": 200,
        "speed": (30, 40),
        "damage": 30,
        "xp": 50,
        "frames": 4,
        "size": (200, 200),
    },
    "sword_fish": {
        "hp": 40,
        "speed": (100, 150),
        "damage": 25,
        "xp": 30,
        "frames": 3,
        "size": (56, 32),
    },
    "fly": {  # fallback
        "hp": 20,
        "speed": (30, 50),
        "damage": 5,
        "xp": 50,
        "frames": 1,
        "size": (40, 40),
    }
}
MONSTER_SPAWN_AREA = {
    "lamprey": {
        "areas": [(344, 900, 2176, 900), (344, 1080, 2176, 1080)],
        "count": 20
    },
    "squid": {
        "areas": [(2472, 1521, 4027, 1521), (2472, 1864, 4027, 1864)],
        "count": 4
    },
    "angler_fish": {
        "areas": [(2764, 3420, 3948, 3420), (2764, 3198, 3948, 3198)],
        "count": 15
    },
    "sword_fish": {
        "areas": [(5576, 928, 6236, 928), (5576, 1306, 6236, 1306)],
        "count": 4
    }
}

MONSTER_SPAWN_RATIO = {
    "lamprey": 4,
    "squid": 1,
    "angler_fish": 3,
    "sword_fish": 2
}
MONSTER_SPAWN_INTERVAL = 30.0 # seconds
MONSTER_COUNT_DIFFICULTY_SCALE = 0.25

# ===== TORPEDO =====
# torpedo stats
TORPEDO_SPEED = 1500
TORPEDO_COOLDOWN = 0.5
TORPEDO_DROP_DURATION = 0.3
TORPEDO_FLOAT_DURATION = 0.1
TORPEDO_ACCEL_DURATION = 0.2
TORPEDO_DROP_SPEED = 30
TORPEDO_FLOAT_SPEED = 10
TORPEDO_ACCELERATION = 1000
TORPEDO_DAMAGE_RADIUS = 80

# ===== SONAR =====
# sonar stats
SONAR_LEVEL_REQUIRED = 5
SONAR_DURATION = 3.5 # secs
SONAR_COOLDOWN = 8.0 # seconds
SONAR_COST = 35
SONAR_RANGE = 1000 # pixels

# ===== XP =====
# XP system
PLAYER_MAX_LEVEL = 20
PLAYER_BASE_DAMAGE = 20
PLAYER_MAX_DAMAGE = 100

# ===== CAMERA =====
# camera
SMOOTHING = 1

# ===== FOG =====
# fog effect
VISIBILITY_RADIUS = 275
FOG_RADIUS = 300
FOG_ALPHA = 200

# ===== RESPAWN =====
# Respawn System
RESPAWN_POINTS = [
    (6025, 3150), 
    (867, 2145), 
    (1050, 3380)
]

RESPAWN_SAFE_RADIUS = 350
RESPAWN_PROTECTION_TIME = 10  # seconds
RESPAWN_DELAY = 2.0  # seconds before respawn
RESPAWN_FLASH_INTERVAL = 200

# ===== PORTAL =====
# portal nodes
PORTAL_NODES = [
    (1176, 1079, 1291, 1237),  # Portal 1
    (3671, 1922, 3786, 2080),  # Portal 2
    (3973, 2718, 4088, 2876),  # Portal 3
    (6249, 2072, 6364, 2230),  # Portal 4
]

# circular linked list order: 1 → 2 → 3 → 4 → 1
PORTAL_LINKED_LIST = [0, 1, 2, 3]  # Indices in navigation order

# portal stats
PORTAL_COOLDOWN = 10000 # milliseconds
PORTAL_RADIUS = 60  # collision radius

# ===== COLORS =====
# colors
CROSSHAIR_COLOR = (199, 14, 32)

# ===== ABILITY ICONS =====
ABILITY_ICON_RADIUS = 28
ABILITY_ICON_GAP = 20
ABILITY_ICON_ALPHA = 160
ABILITY_ICON_Y_OFFSET = 80

# ===== IMAGE PATHS =====
# player folder
PLAYER_PATH = 'assets/images/player'
# monster folder
MONSTERS_PATH = 'assets/images/monsters'
# explosion folder
EXPLOSION_PATH = 'assets/images/explosion'
# torpedo folders
LEFT_TORPEDO_PATH = 'assets/images/projectile/left_torpedo'
RIGHT_TORPEDO_PATH = 'assets/images/projectile/right_torpedo'
# portal folder
PORTAL_PATH = 'assets/images/portal'

# ===== MAP PATH =====
MAP_PATH = 'assets/data/map/subnautic_shooter_map.tmx'

# ===== ICONS PATH =====
SONAR_ICON_PATH = 'assets/images/icons/sonar_icon.png'
PORTAL_ICON_PATH = 'assets/images/icons/portal_icon.png'
TORPEDO_ICON_PATH = 'assets/images/icons/torpedo_icon.png'

# audio paths
PLAYING_MUSIC = 'assets/audio/music/playing_music.mp3'
START_MENU_MUSIC = 'assets/audio/music/start_menu_music.mp3'
TORPEDO_HIT_SOUND = 'assets/audio/sound_effects/projectile_hit.mp3'
TORPEDO_LAUNCH_SOUND = 'assets/audio/sound_effects/projectile_launch.mp3'
SONAR_PING = 'assets/audio/sound_effects/sonar_ping.mp3'
DAMAGE_SOUND = 'assets/audio/sound_effects/damage.mp3'
TELEPORT_SOUND = 'assets/audio/sound_effects/teleport.mp3'
LOW_HEALTH_ALERT = 'assets/audio/sound_effects/low_health.mp3'
RESPAWN_SOUND = 'assets/audio/sound_effects/respawn.mp3'
IM_BACK = 'assets/audio/sound_effects/im_back.mp3'