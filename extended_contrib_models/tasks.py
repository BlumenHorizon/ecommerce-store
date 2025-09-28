import gzip
import logging
import os
import subprocess
import tarfile
from pathlib import Path
from subprocess import SubprocessError

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from telegram.error import TimedOut

from extended_contrib_models.models import ExtendedSite
from extended_contrib_models.utils.dumps import process_and_send_file

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
    Создаёт дамп MySQL, сжимает и отправляет.
    """

    def create_db_dump(file_path: Path):
        dump_file = file_path.with_suffix("")

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
        with open(dump_file, "rb") as f_in, gzip.open(file_path, "wb") as f_out:
            f_out.writelines(f_in)
        dump_file.unlink(missing_ok=True)

    caption_template = (
        "💾 *Резервная копия базы данных*\n\n"
        f"База: `{settings.DATABASES['default']['NAME']}`\n"
        "Дата и время создания: `{timestamp}`\n"
        "Размер файла: `{size:.1f} KB`\n\n"
        "Файл готов к загрузке и использованию для восстановления данных.\n"
        f"#dump #{settings.DATABASES['default']['NAME']}"
    )

    process_and_send_file(
        create_db_dump, caption_template, "db_dump", ".sql.gz", logger
    )


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
def make_bills_archive():
    0
    bills_dir = Path(settings.BASE_DIR) / "media" / os.getenv("CITY") / "bills"

    def create_bills_archive(file_path: Path):
        if not bills_dir.exists():
            raise FileNotFoundError(f"Папка {bills_dir} не существует")
        with tarfile.open(file_path, "w:gz") as tar:
            tar.add(bills_dir, arcname="bills")

    city = (
        ExtendedSite.objects.first().city
        if ExtendedSite.objects.exists()
        else "unknown"
    )
    caption_template = (
        "📂 *Архив счетов*\n\n"
        "Папка: `media/bills`\n"
        "Дата и время создания: `{timestamp}`\n"
        "Размер файла: `{size:.1f} KB`\n\n"
        "Файл готов для загрузки и использования.\n"
        f"Город: {city}\n"
        "#archive #bills"
    )

    process_and_send_file(
        create_bills_archive, caption_template, "bills", ".tar.gz", logger
    )
