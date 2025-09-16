from extended_contrib_models.models import AdminsTelegramChatIDs


def get_admins_chat_ids() -> list[str]:
    """Возвращает список chat_id администраторов для отправки уведомлений в Telegram."""
    return list(AdminsTelegramChatIDs.objects.values_list("chat_id", flat=True))
