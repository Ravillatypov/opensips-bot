from os import environ as env
from asyncpg.pool import Pool

TOKEN = env.get('API_TOKEN', default='')
ADMINS = env.get('ADMINS', default='').split(',')

VOX_USERNAME = env.get('VOX_USERNAME', default='')
OSIPS_IP = env.get('OSIPS_IP', default='')
OSIPS_DOMAIN = env.get('OSIPS_DOMAIN', default='')
OSIPS_MI_URL = env.get('OSIPS_MI_URL', default='http://127.0.0.1:8888/mi')

LOCAL_DB_PATH = env.get('LOCAL_DB_PATH', default='/tmp/bot-state')
DB_DSN = env.get('DB_DSN', default='postgres://opensips:43YgEKx87s7l0HmNr1lc@127.0.0.1/opensips')

db_pool: Pool = None
