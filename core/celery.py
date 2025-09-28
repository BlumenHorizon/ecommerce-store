import logging
import os
from logging.handlers import RotatingFileHandler

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings
from dotenv import load_dotenv
from kombu import Exchange, Queue


load_dotenv("core/cities/envs/base.env", override=True)

city = os.getenv("CITY")
if not city:
    raise Exception("CITY environment variable is not set.")

load_dotenv(f"core/cities/envs/{city}.env", override=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"core.cities.settings.{city}")

app = Celery(f"BlumenHorizon")
app.config_from_object("django.conf:settings")
app.autodiscover_tasks()

app.conf.task_track_started = True
app.conf.broker_url = os.getenv("CELERY_BROKER")
app.conf.result_backend = os.getenv("CELERY_BACKEND")
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

app.conf.task_queues = [
    Queue("berlin", Exchange("berlin"), routing_key="berlin"),
    Queue("athens", Exchange("athens"), routing_key="athens"),
    Queue("madrid", Exchange("madrid"), routing_key="madrid"),
    Queue("larnaca", Exchange("larnaca"), routing_key="larnaca"),
    Queue("limassol", Exchange("limassol"), routing_key="limassol"),
    Queue("europe", Exchange("europe"), routing_key="europe"),
]
app.conf.task_default_queue = "default"
app.conf.task_default_exchange = "default"
app.conf.task_default_routing_key = "default"

app.conf.result_backend_transport_options = {
    "keyprefix": f"{settings.CITY}:celery-task-meta-"
}




class LevelFilter(logging.Filter):
    """Фильтр для записи только сообщений указанного уровня"""

    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


def configure_celery_logging():
    LOG_DIR = getattr(settings, "CELERY_LOG_DIR", "./logs/celery")
    os.makedirs(LOG_DIR, exist_ok=True)

    log_formatter = logging.Formatter(
        fmt="[%(asctime)s: %(levelname)s/%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    info_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "celery_info.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=14,
    )
    info_handler.setFormatter(log_formatter)
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(LevelFilter(logging.INFO))
    root_logger.addHandler(info_handler)

    warning_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "celery_warning.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=14,
    )
    warning_handler.setFormatter(log_formatter)
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(LevelFilter(logging.WARNING))
    root_logger.addHandler(warning_handler)

    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "celery_error.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=14,
    )
    error_handler.setFormatter(log_formatter)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(LevelFilter(logging.ERROR))
    root_logger.addHandler(error_handler)


@setup_logging.connect
def setup_loggers(**kwargs):
    configure_celery_logging()
