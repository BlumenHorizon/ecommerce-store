from decimal import ROUND_HALF_UP, Decimal

from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse_lazy
from django.utils import timezone
from telegram.helpers import escape_markdown
from tinymce.models import HTMLField

from core.base_models import TimeStampAdbstractModel
from core.services.repositories import SiteRepository
from tg_bot import send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids

from ..services import (
    CategoryAbstractModel,
    ItemReview,
    MetaDataAbstractModel,
    ProductAbstractModel,
    TaxPercent,
    generate_sku,
)


class Color(models.Model):
    name = models.CharField(
        max_length=15,
        verbose_name="Название",
        unique=True,
    )
    hex_code = ColorField(
        verbose_name="HEX код цвета (#f4678a к примеру)",
        help_text="Введите HEX-код цвета, например: #FFFFFF (белый) или #FFF (сокращённый формат).",
        unique=True,
    )

    class Meta:
        verbose_name = "Цвет букета"
        verbose_name_plural = "3. Цветовые гаммы букетов"

    def __str__(self):
        return f"{self.name} ({self.hex_code})"


class Flower(models.Model):
    name = models.CharField(
        max_length=30,
        verbose_name="Название",
        unique=True,
    )

    class Meta:
        verbose_name = "Цветок"
        verbose_name_plural = "2. Состав букетов"

    def __str__(self):
        return self.name


class BouquetsListPageModel(models.Model):
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="""<title> | BlumenHorizon</title>
<meta name="description" content="Описание">""",
    )

    class Meta:
        verbose_name = "Мета-тег списка всех букетов"
        verbose_name_plural = "Мета-теги списка всех букетов"

    def __str__(self):
        return "Мета-теги списка всех букетов"


class BouquetCategory(
    CategoryAbstractModel, TimeStampAdbstractModel, MetaDataAbstractModel
):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="categories/%Y-%m-%d",
        default="defaults/no-image.webp",
    )
    image_alt = models.CharField(verbose_name="Описание картинки", max_length=200)
    catalog_page_meta_tags = models.TextField(
        verbose_name="Мета-теги на странице категории со списком подкатегорий",
        max_length=4000,
        default="""<title> | BlumenHorizon</title>
<meta name="description" content="Описание">""",
    )
    description = HTMLField(verbose_name="Описание на странице категории", null=True)

    class Meta:
        verbose_name = "Категория букета"
        verbose_name_plural = "4. Категории букетов"

    def __str__(self):
        return self.name

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:bouquets-category",
            kwargs={
                "category_slug": self.slug,
            },
        )


class BouquetSubcategory(
    CategoryAbstractModel, TimeStampAdbstractModel, MetaDataAbstractModel
):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="subcategories/%Y-%m-%d",
        default="defaults/no-image.webp",
    )
    image_alt = models.CharField(verbose_name="Описание картинки", max_length=200)
    category = models.ForeignKey(
        BouquetCategory,
        on_delete=models.PROTECT,
        verbose_name="Категория",
        related_name="subcategories",
    )

    class Meta:
        verbose_name = "Подкатегория букета"
        verbose_name_plural = "5. Подкатегории букетов"

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:bouquets-subcategory",
            kwargs={
                "category_slug": self.category.slug,
                "subcategory_slug": self.slug,
            },
        )

    def clean_category(self):
        if self.category is None:
            self.is_active = False


class Bouquet(ProductAbstractModel):
    subcategory = models.ForeignKey(
        BouquetSubcategory,
        on_delete=models.PROTECT,
        verbose_name="Подкатегория",
        related_name="bouquets",
    )
    amount_of_flowers = models.IntegerField(verbose_name="Количество цветов в букете")
    diameter = models.IntegerField(verbose_name="Диаметр букета")
    colors = models.ManyToManyField(
        Color,
        related_name="bouquet",
        verbose_name="Цветовые гаммы букетов",
        help_text="Выберите какого цвета букет.",
    )
    flowers = models.ManyToManyField(
        Flower,
        related_name="bouquets",
        verbose_name="Состав букетов",
        help_text="Выберите какие цветы в букете.",
    )
    sku = models.CharField(max_length=25, unique=True, default=generate_sku, null=True)
    tax_percent = models.ForeignKey(
        TaxPercent,
        default=1,
        on_delete=models.PROTECT,
        related_name="bouquets",
        verbose_name="Налоговая ставка",
        help_text="Выберите налоговую ставку, применимую к данному букету. Вычисляется после скидки.",
    )

    class Meta:
        verbose_name = "Букет"
        verbose_name_plural = "1. Букеты"

    def __str__(self):
        return f"{self.name} ({self.diameter} см, {self.amount_of_flowers} цветов)"

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:bouquet-details",
            kwargs={
                "category_slug": self.subcategory.category.slug,
                "subcategory_slug": self.subcategory.slug,
                "bouquet_slug": self.slug,
            },
        )

    @property
    def is_bouquet(self) -> bool:
        return True


class BouquetReview(ItemReview):
    item = models.ForeignKey(
        Bouquet,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Букет",
    )


@receiver(post_save, sender=BouquetReview)
def order_created(
    sender: BouquetReview,
    instance: BouquetReview,
    created,
    **kwargs,
):
    country = SiteRepository.get_country()
    city = SiteRepository.get_city()
    if created:
        review = instance
        text = (
            f"*Новый отзыв на букет оформлен!* 🎉\n\n"
            f"*ID отзыва*: `{review.pk}`\n"
            f"*Страна*: `{escape_markdown(country)}`\n"
            f"*Город*: `{escape_markdown(city)}`\n"
            f"*Имя автора*: `{escape_markdown(review.author_name)}`\n"
            f"*Email автора*: `{escape_markdown(review.email)}`\n"
            f"Вперёд за модерацию! 🚀"
        )
        send_message_to_telegram(text, get_admins_chat_ids())


class BouquetSize(models.Model):
    bouquet = models.ForeignKey(
        Bouquet, related_name="sizes", verbose_name="Букет", on_delete=models.CASCADE
    )
    amount_of_flowers = models.IntegerField(verbose_name="Количество цветов в букете")
    diameter = models.IntegerField(verbose_name="Диаметр букета")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена размера",
        help_text="Цена размера до 10ти значений, два из которых плавающая запятая. Т.е. до 99999999.99",
    )
    discount = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(100),
        ),
        verbose_name="Скидка",
        null=True,
        default=0,
    )
    discount_expiration_datetime = models.DateTimeField(
        verbose_name="Время истечения скидки", default=timezone.now
    )

    @property
    def discount_price(self) -> float:
        discount = Decimal(self.discount)
        result = self.price * (1 - discount / 100) if discount else self.price
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    class Meta:
        verbose_name = "Размер букета"
        verbose_name_plural = "Размеры букетов"

    def __str__(self):
        return f"{self.diameter}cm, {self.price}у.е."
