from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from telegram.helpers import escape_markdown
from tinymce.models import HTMLField

from catalogue.models.bouquets.bouquet import Bouquet
from catalogue.models.products.product import Product
from core.base_models import TimeStampAdbstractModel
from core.services.repositories import SiteRepository
from tg_bot import send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids


class CatalogPageModel(models.Model):
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="""<title> | BlumenHorizon</title>
<meta name="description" content="Описание">""",
    )
    description = HTMLField(verbose_name="Описание на странице 'Каталог'", null=True)

    class Meta:
        verbose_name = "Страница «Каталог»"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Страница «Каталог»"


class IndividualQuestion(TimeStampAdbstractModel, models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="individual_questions",
        verbose_name="Связанный аккаунт",
        null=True,
        blank=False,
    )
    contact_method = models.TextField(
        max_length=100,
        verbose_name="Способ связи с клиентом",
    )
    recall_me = models.BooleanField(
        verbose_name="Разрешил ли клиент звонить ему", default=False
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name="individual_question",
        verbose_name="Связанный продукт",
        null=True,
        blank=True,
    )
    bouquet = models.ForeignKey(
        Bouquet,
        on_delete=models.SET_NULL,
        related_name="individual_question",
        verbose_name="Связанный букет",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Индивидуальный вопрос о продукте"
        verbose_name_plural = "Индивидуальные вопросы о продуктах"

    def __str__(self):
        return f"{self.user if self.user else "Неизвестный пользователь"}"


@receiver(post_save, sender=IndividualQuestion)
def individual_question_created(
    sender, instance: IndividualQuestion, created, **kwargs
):
    country = SiteRepository.get_country()
    city = SiteRepository.get_city()
    if created:
        individual_question = instance
        text = (
            f"*Индивидуальный вопрос по продукту!* 🎉\n\n"
            f"*ID заказа*: `{escape_markdown(str(individual_question.id))}`\n"
            f"*Страна*: `{escape_markdown(country)}`\n"
            f"*Город*: `{escape_markdown(city)}`\n"
            f"*Продукт*: `{escape_markdown(individual_question.product.name if individual_question.product else individual_question.bouquet.name)}`\n"
            f"*Способ связи*: \n `{escape_markdown(individual_question.contact_method)}`\n\n"
            f"Вперёд за работу! 🚀"
        )

        send_message_to_telegram(text, get_admins_chat_ids())
