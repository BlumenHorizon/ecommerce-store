from datetime import datetime
from logging import Logger
from pathlib import Path

from tg_bot.main import send_document_to_telegram, send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids


def process_and_send_file(
    create_file_func, caption_template: str, prefix: str, ext: str, logger: Logger
):
    """
    Универсальная функция для создания файла (дампа/архива),
    его отправки и очистки.
    """
    tmp_dir = Path(f"/tmp/{prefix}")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = tmp_dir / f"{prefix}_{timestamp}{ext}"

    try:
        logger.info(f"Начало создания {prefix}")
        create_file_func(file_path)

        caption = caption_template.format(
            timestamp=timestamp,
            size=file_path.stat().st_size / 1024,
        )
        send_document_to_telegram(str(file_path), get_admins_chat_ids(), caption)
        logger.info(f"{prefix} успешно создан и отправлен: {file_path}")

    except Exception as e:
        try:
            send_message_to_telegram(
                f"❗️ Ошибка при создании {prefix}:\n{e}",
                get_admins_chat_ids(),
            )
        finally:
            logger.error(f"Ошибка при создании {prefix}: {e}", exc_info=True)

    finally:
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Удалён временный файл: {file_path}")
            except Exception as e:
                try:
                    send_message_to_telegram(
                        f"⚠️ Не удалось удалить временный файл: {file_path}\nОшибка: {e}",
                        get_admins_chat_ids(),
                    )
                finally:
                    logger.warning(f"Не удалось удалить файл {file_path}: {e}")
