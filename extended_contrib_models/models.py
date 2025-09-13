"""
Модели для расширенных данных о сайте и социальных сетях.

Модуль содержит две основные модели:
1. `ExtendedSite` — хранит расширенную информацию о сайте, включая данные о валюте, стране, городе, налогах и банковских реквизитах.
2. `Social` — хранит информацию о социальных сетях, включая ссылки, цвета и иконки.

Также имеется сигнал, который создает объект `ExtendedSite` для каждого нового сайта.
"""

from colorfield.fields import ColorField
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class ExtendedSite(models.Model):
    """
    Модель для хранения расширенной информации о сайте.

    Связан с моделью `django.contrib.sites.models.Site` через One-to-One связь и содержит различные поля,
    такие как код валюты, символ валюты, страна, город, НДС, банковские реквизиты и
    текстовое уведомление для отображения на сайте.
    """

    site = models.OneToOneField(Site, related_name="extended", on_delete=models.PROTECT)
    currency_code = models.CharField(
        max_length=5, verbose_name="Код валюты", unique=True
    )
    currency_symbol = models.CharField(max_length=5, verbose_name="Знак валюты")
    country = models.CharField(max_length=40, verbose_name="Название страны")
    city = models.CharField(max_length=40, verbose_name="Название города")
    country_iso_3166_1_alpha_2 = models.CharField(
        max_length=2,
        verbose_name="Код страны ISO 3166-1 alpha-2",
        help_text="ISO 3166-1 alpha-2",
    )
    header_alert_message = models.CharField(
        max_length=174,
        verbose_name="Текст для красного уведомления под хедером, белый текст на красном фоне во всю ширину строки.",
        null=True,
        blank=True,
    )

    email = models.CharField(
        "Email компании",
        max_length=50,
        default="service@blumenhorizon.de",
    )

    def __str__(self):
        """
        Строковое представление модели `ExtendedSite`.

        Возвращает строку с именем сайта и его доменом.
        """
        return f"{self.site.name} | {self.site.domain}"

    class Meta:
        verbose_name = "Расширенные данные о сайте"
        verbose_name_plural = verbose_name


class AdminsTelegramChatIDs(models.Model):
    chat_id = models.CharField(
        max_length=20,
        verbose_name="Telegram chat ID",
        unique=True,
        help_text="Используется для отправки уведомлений администратору в Telegram.",
    )

    def __str__(self):
        return self.chat_id

    class Meta:
        verbose_name = "TG chat ID администратора"
        verbose_name_plural = "TG chat IDs администраторов"


class Social(models.Model):
    """
    Модель для хранения информации о социальных сетях.

    Связана с моделью `ExtendedSite` и хранит данные о ссылке на соц. сеть, цвета иконки и фона,
    а также иконку в формате Bootstrap.
    """

    absolute_url = models.URLField(verbose_name="Ссылка на соц. сеть", unique=True)
    outline_hex_code = ColorField(
        verbose_name="HEX код цвета обводки (#f4678a к примеру)",
        help_text="Введите HEX-код цвета, например: #FFFFFF (белый) или #FFF (сокращённый формат).",
    )
    background_hex_code = ColorField(
        verbose_name="HEX код цвета фона (#f4678a к примеру)",
        help_text="Введите HEX-код цвета, например: #FFFFFF (белый) или #FFF (сокращённый формат).",
    )
    icon_hex_code = ColorField(
        verbose_name="HEX код цвета иконки (#f4678a к примеру)",
        help_text="Введите HEX-код цвета, например: #FFFFFF (белый) или #FFF (сокращённый формат).",
    )
    bootstrap_icon = models.CharField(
        max_length=40,
        verbose_name="Название класса иконки",
        help_text="https://icons.getbootstrap.com/",
    )
    extended_site = models.ForeignKey(
        ExtendedSite,
        on_delete=models.PROTECT,
        related_name="socials",
    )

    class Meta:
        verbose_name = "Соц. сеть"
        verbose_name_plural = "Соц. сети"

    def __str__(self):
        """
        Строковое представление модели `Social`.

        Возвращает строку с классом иконки и ссылкой на соц. сеть.
        """
        return f"{self.bootstrap_icon} - {self.absolute_url}"

    def to_dict(self):
        return {
            "id": self.id,
            "absolute_url": self.absolute_url,
            "outline_hex_code": self.outline_hex_code,
            "background_hex_code": self.background_hex_code,
            "icon_hex_code": self.icon_hex_code,
            "bootstrap_icon": self.bootstrap_icon,
        }


class Filial(models.Model):
    extended_site = models.ForeignKey(
        ExtendedSite,
        default=1,
        on_delete=models.PROTECT,
        related_name="filials",
    )
    title = models.CharField(
        max_length=60, verbose_name="Название “Город/Страна”", help_text="ISO"
    )
    url = models.URLField("Ссылка на филиал")

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

    def to_dict(self):
        return {"url": self.url, "title": self.title}

    def __str__(self) -> str:
        return self.title


@receiver(post_save, sender=Site)
def create_extended_site(sender, instance, created, **kwargs):
    """
    Сигнал для создания объекта `ExtendedSite` при создании нового сайта.

    Если для сайта не существует объекта `ExtendedSite`, он создается с предустановленными
    значениями для валюты, страны и города.
    """
    if not ExtendedSite.objects.filter(site=instance).exists():
        ExtendedSite.objects.create(
            site=instance,
            currency_code="USD",
            currency_symbol="$",
            country="Германия",
            city="Берлин",
        )
