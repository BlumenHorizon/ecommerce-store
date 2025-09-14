import asyncio
import logging

from django.conf import settings
from telegram import Bot
from telegram.request import HTTPXRequest

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

request = HTTPXRequest(
    connection_pool_size=1,
    read_timeout=900,
    write_timeout=900,
    connect_timeout=60,
    pool_timeout=60,
)

bot = Bot(token=TELEGRAM_BOT_TOKEN, request=request)


async def send_document_to_telegram_async(
    chat_id: str, file_path: str, caption: str = None
):
    with open(file_path, "rb") as f:
        await bot.send_document(
            chat_id=chat_id,
            document=f,
            caption=caption,
            parse_mode="Markdown",
            read_timeout=900,
            write_timeout=900,
            connect_timeout=60,
            pool_timeout=60,
        )


async def send_documents_to_multiple_chat_ids(
    chat_ids: list[str], file_path: str, caption: str = None
):
    tasks = [
        send_document_to_telegram_async(chat_id, file_path, caption)
        for chat_id in chat_ids
    ]
    await asyncio.gather(*tasks)


def send_document_to_telegram(
    file_path: str, telegram_chat_ids: list[str], caption: str = None
):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        asyncio.ensure_future(
            send_documents_to_multiple_chat_ids(telegram_chat_ids, file_path, caption)
        )
    else:
        loop.run_until_complete(
            send_documents_to_multiple_chat_ids(telegram_chat_ids, file_path, caption)
        )


async def send_message_to_telegram_async(chat_id: str, text: str):
    try:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception as e:
        logger = logging.getLogger("telegramBot")
        logger.error(
            f"Error sending message to chat_id {chat_id}: {e}", stack_info=True
        )


async def send_messages_to_multiple_chat_ids(chat_ids: list[str], text: str):
    tasks = [send_message_to_telegram_async(chat_id, text) for chat_id in chat_ids]
    await asyncio.gather(*tasks)


def send_message_to_telegram(text: str, telegram_chat_ids: list[str]):
    """
    Sends a message to multiple chat_ids using asyncio.
    :param text: The message text to send.
    :param chat_ids: A list of chat IDs to send the message to.
    """
    logger = logging.getLogger("telegramBot")
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.ensure_future(
                send_messages_to_multiple_chat_ids(telegram_chat_ids, text)
            )
        else:
            loop.run_until_complete(
                send_messages_to_multiple_chat_ids(telegram_chat_ids, text)
            )
    except Exception as e:
        logger.error(f"Error in send_message_to_telegram: {e}")
