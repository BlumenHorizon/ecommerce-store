import gzip
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from subprocess import SubprocessError

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from telegram.error import TimedOut

from tg_bot.main import send_document_to_telegram
from tg_bot.utils import get_admins_chat_ids

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(
        TimedOut,
        TimeoutError,
        SoftTimeLimitExceeded,
        SubprocessError,
        Exception,
    ),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=900,
    time_limit=960,
)
def make_db_dump():
    """
    Создаёт дамп MySQL с уникальным именем, сжимает его и отправляет админам в Telegram.
    """
    dump_dir = Path("/tmp/db_dumps")
    dump_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = dump_dir / f"db_dump_{timestamp}.sql"
    dump_file_gz = dump_dir / f"db_dump_{timestamp}.sql.gz"

    try:
        logger.info(
            f"Начало создания дампа базы: {settings.DATABASES['default']['NAME']}"
        )
        subprocess.run(
            [
                "mysqldump",
                f"-u{settings.DATABASES['default']['USER']}",
                f"-p{settings.DATABASES['default']['PASSWORD']}",
                f"-h{settings.DATABASES['default']['HOST']}",
                settings.DATABASES["default"]["NAME"],
            ],
            stdout=open(dump_file, "w"),
            check=True,
            timeout=50,
        )

        with open(dump_file, "rb") as f_in, gzip.open(dump_file_gz, "wb") as f_out:
            f_out.writelines(f_in)

        caption = (
            f"💾 *Резервная копия базы данных*\n\n"
            f"База: `{settings.DATABASES['default']['NAME']}`\n"
            f"Дата и время создания: `{timestamp}`\n"
            f"Размер файла: `{dump_file_gz.stat().st_size / 1024:.1f} KB`\n\n"
            f"Файл готов к загрузке и использованию для восстановления данных.\n"
            f"#dump #{settings.DATABASES['default']['NAME']}"
        )
        send_document_to_telegram(str(dump_file_gz), get_admins_chat_ids(), caption)
        logger.info(f"Дамп успешно создан и отправлен: {dump_file_gz}")

    except Exception as e:
        logger.error(f"Ошибка при создании дампа базы: {e}", exc_info=True)

    finally:
        for f in [dump_file, dump_file_gz]:
            if f.exists():
                try:
                    f.unlink()
                    logger.info(f"Удалён временный файл: {f}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {f}: {e}")
