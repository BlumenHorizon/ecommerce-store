from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from telegram.helpers import escape_markdown
from tinymce.models import HTMLField

from core.base_models import TimeStampAdbstractModel
from core.services.repositories import SiteRepository
from tg_bot import send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids


class MainPageModel(models.Model):
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="<title> | BlumenHorizon</title>",
    )
    json_ld_description = models.CharField(
        verbose_name="Description в JSON LD для OnlineStore",
        max_length=500,
        default="Blumen Horizon интернет-магазин цветов и подарков в Берлине",
    )
    description = HTMLField(
        verbose_name=_("Описание"),
    )

    class Meta:
        verbose_name = "1. Главная страница"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Главная страница"


class MainPageSliderImages(models.Model):
    image = models.ImageField(
        upload_to="mainpage-slider/",
        verbose_name="Фото на главном слайде",
        help_text="1000px/450px",
    )
    is_active = models.BooleanField(default=False, verbose_name="Активное?")
    image_alt = models.CharField(verbose_name="Описание картинки", max_length=200)

    class Meta:
        verbose_name = "2. Фото слайдера вверху главной страницы"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.image} - {"Активно" if self.is_active else "Неактивно"}"


class IndividualOrder(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="individual_orders",
        verbose_name="Связанный аккаунт",
        null=True,
        blank=False,
    )
    first_name = models.CharField(max_length=40, verbose_name="Имя")
    contact_method = models.TextField(
        max_length=100,
        verbose_name="Способ связи с клиентом",
    )
    recall_me = models.BooleanField(
        verbose_name="Разрешил ли клиент звонить ему", default=False
    )

    class Meta:
        verbose_name = "Индивидуальный заказ"
        verbose_name_plural = "Индивидуальные заказы"

    def __str__(self):
        return f"{self.first_name}"


@receiver(post_save, sender=IndividualOrder)
def individual_order_created(sender, instance: IndividualOrder, created, **kwargs):
    country = SiteRepository.get_country()
    city = SiteRepository.get_city()
    if created:
        individual_order = instance
        text = (
            f"*Индивидуальный заказ!* 🎉\n\n"
            f"*ID вопроса*: `{escape_markdown(str(individual_order.id))}`\n"
            f"*Страна*: `{escape_markdown(country)}`\n"
            f"*Город*: `{escape_markdown(city)}`\n"
            f"*Имя*: `{escape_markdown(individual_order.first_name)}`\n"
            f"*Способ связи*: \n `{escape_markdown(individual_order.contact_method)}`\n\n"
            f"Вперёд за работу! 🚀"
        )

        send_message_to_telegram(text, get_admins_chat_ids())


class MainPageSeoBlock(TimeStampAdbstractModel, models.Model):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="seoblock/",
        help_text="1000px/450px",
    )
    image_alt = models.CharField(max_length=200, verbose_name="Описание картинки")

    class Meta:
        verbose_name = "3. Фотография внизу главной страницы"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.image} ...... {self.image_alt}"


class FAQPageModel(TimeStampAdbstractModel):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="seoblock/",
        default="defaults/no-image.webp",
        help_text="1000px/450px",
    )
    image_alt = models.CharField(max_length=200, verbose_name="Описание картинки")
    description = HTMLField(
        verbose_name=_("Описание"),
    )
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="<title> | BlumenHorizon</title>",
    )

    def __str__(self):
        return "Страница «Частозадаваемые вопросы»"

    class Meta:
        verbose_name = "Страница «Частозадаваемые вопросы»"
        verbose_name_plural = verbose_name


class AboutUsPageModel(TimeStampAdbstractModel):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="seoblock/",
        default="defaults/no-image.webp",
        help_text="1000px/450px",
    )
    image_alt = models.CharField(max_length=200, verbose_name="Описание картинки")
    description = HTMLField(
        verbose_name=_("Описание"),
    )
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="<title> | BlumenHorizon</title>",
    )

    def __str__(self):
        return "Страница «О нас»"

    class Meta:
        verbose_name = "Страница «О нас»"
        verbose_name_plural = verbose_name


class DeliveryPageModel(TimeStampAdbstractModel):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="seoblock/",
        default="defaults/no-image.webp",
        help_text="1000px/450px",
    )
    image_alt = models.CharField(max_length=200, verbose_name="Описание картинки")
    description = HTMLField(
        verbose_name=_("Описание"),
    )
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="<title> | BlumenHorizon</title>",
    )

    def __str__(self):
        return "Страница о условиях доставки"

    class Meta:
        verbose_name = "Страница «Доставка»"
        verbose_name_plural = verbose_name


class ContactsPageModel(TimeStampAdbstractModel):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="seoblock/",
        default="defaults/no-image.webp",
        help_text="1000px/450px",
    )
    image_alt = models.CharField(max_length=200, verbose_name="Описание картинки")
    description = HTMLField(
        verbose_name=_("Описание"),
    )
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="<title> | BlumenHorizon</title>",
    )

    def __str__(self):
        return "Страница с контактами"

    class Meta:
        verbose_name = "Страница «Контакты»"
        verbose_name_plural = verbose_name


class ConditionsPageModelAbstract(models.Model):
    description = HTMLField(
        verbose_name=_("Описание"),
    )
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        default="<title> | BlumenHorizon</title>",
    )

    class Meta:
        abstract = True


class AGBPageModel(ConditionsPageModelAbstract, TimeStampAdbstractModel):
    class Meta:
        verbose_name = "Страница «Условия и положения»"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Условия и положения"


class PrivacyAndPolicyPageModel(ConditionsPageModelAbstract, TimeStampAdbstractModel):
    class Meta:
        verbose_name = "Страница «Условия конфиденциальности и безопасности данных»"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Условия конфиденциальности и безопасности данных"


class ImpressumPageModel(ConditionsPageModelAbstract, TimeStampAdbstractModel):
    class Meta:
        verbose_name = "Страница «Правовая информация»"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Страница «Правовая информация»"


class ReturnPolicyPageModel(ConditionsPageModelAbstract, TimeStampAdbstractModel):
    class Meta:
        verbose_name = "Страница «Условия возврата»"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "Условия возврата"
