from os.path import join

GAME_SERVER_WEB_SOCKET_URL = u"ws://0.0.0.0:%s"
GUARD_WEB_SOCKET_URL = u"ws://127.0.0.1:%s?guard=%s"
GAME_SERVER_WEB_SOCKET_PORT = '9000'
TEMPLATES_DIR = 'templates'
REST_ROOT = 'rest'
FRONTEND_PORT = 8080

SERVER_LOG_FILE = join('logs', 'server.log')
CLIENT_LOG_FILE = join('logs', 'client.log')
LOG_TO_FILE = False
MAX_LOG_BYTES = 1048576
BACKUP_COUNT = 3

SCORE_STRING_HEADER = "score=%s"
PLAYERS_STRING_HEADER = "players=%s"
BOARD_SIZE_HEADER = "size=%d"

GOLD_CELLS_NUMBER = 30
WAIT_FREE_CELL_TICK = 0.001
STOP_WAIT_FREE_CELL_TIMEOUT = 1
TICK_TIME = 1

CATCH_Guard_REWARD = 5
CATCH_Player_REWARD = 100

INACTIVITY_TIMEOUT = 100 * 60

GUARDS_NUMBER = 4
GUARD_NAME_PREFIX = "AI_"

BOARD_BLOCKS_NUMBER = 2

DEBUG = True
