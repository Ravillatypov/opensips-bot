from os import environ as env
from asyncpg.pool import Pool

TOKEN = env.get('API_TOKEN', default='1306273788:AAG81WDz07FwRXVWvGQsxFCdQt75P9g5GFs')
ADMINS = env.get('ADMINS', default='LatypovRavil,cashman2100').split(',')

VOX_USERNAME = env.get('VOX_USERNAME', default='voximplant')
OSIPS_IP = env.get('OSIPS_IP', default='185.119.58.109')
OSIPS_DOMAIN = env.get('OSIPS_DOMAIN', default='fs.everyit.online')
OSIPS_MI_URL = env.get('OSIPS_MI_URL', default='http://127.0.0.1:8888/mi')

DB_DSN = env.get('DB_DSN', default='postgres://opensips:43YgEKx87s7l0HmNr1lc@127.0.0.1/opensips')

db_pool: Pool = None
