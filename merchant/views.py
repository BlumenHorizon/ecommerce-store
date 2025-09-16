import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from tg_bot import send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids

from .exceptions import OrderNotFound
from .services.utils import (
    handle_order_confirmation,
    process_order,
    try_clear_cart,
    verify_stripe_webhook,
)


@api_view(["POST"])
def stripe_webhook(request: Request):
    """
    Обрабатывает webhook от Stripe для подтверждения платежей.

    Параметры:
    - request (Request): Объект HTTP-запроса, содержащий данные webhook от Stripe.

    Действия:
    - Проверяет подпись webhook.
    - Извлекает код заказа из данных события.
    - Отправляет подтверждение заказа на email пользователя.
    - Обновляет статус заказа в базе данных.
    - Очищает корзину пользователя.

    Возвращает:
    - Response: HTTP-ответ с кодом состояния:
      - 200: Если webhook обработан успешно.
      - 400: Если проверка подписи или данных не удалась.
      - 500: Если возникла внутренняя ошибка сервера.

    Исключения:
    - OrderNotFound: Если заказ с указанным кодом не найден.
    """
    logger = logging.getLogger("django_stripe_info")
    try:
        event_dict, error_response = verify_stripe_webhook(request)
        if error_response:
            return error_response

        order = process_order(event_dict)
        handle_order_confirmation(order)
        try_clear_cart(order)
    except OrderNotFound as e:
        logger.error(e, stack_info=True)
        text = (
            f"Stripe попытался связаться с веб-хуком: \n\n"
            f"{request.build_absolute_uri(request.get_full_path())}"
        )
        send_message_to_telegram(text, get_admins_chat_ids())
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(e, stack_info=True)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(status=status.HTTP_200_OK)
