import os

from dotenv import load_dotenv

load_dotenv(f"core/cities/envs/{os.getenv("CITY")}.env", override=True)

bind = os.getenv("GUNICORN_DOMAIN")
workers = 2
threads = 3
timeout = 30

reload = False
wsgi_app = "core.wsgi:application"

accesslog = "logs/gunicorn/gunicorn_access.log"
errorlog = "logs/gunicorn/gunicorn_error.log"
loglevel = "debug"
