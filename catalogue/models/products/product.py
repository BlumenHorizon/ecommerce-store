from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse_lazy
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


class ProductsListPageModel(models.Model):
    meta_tags = models.TextField(
        verbose_name="Мета-теги",
        max_length=1000,
        default="""<title> | BlumenHorizon</title>
<meta name="description" content="Описание">""",
    )

    class Meta:
        verbose_name = "Мета-тег списка всех продуктов"
        verbose_name_plural = "Мета-теги списка всех продуктов"

    def __str__(self):
        return "Мета-теги списка всех продуктов"


class ProductCategory(
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
        verbose_name = "Категория продукта"
        verbose_name_plural = "7. Категории продуктов"

    def __str__(self):
        return self.name

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:products-category",
            kwargs={
                "category_slug": self.slug,
            },
        )


class ProductSubcategory(
    CategoryAbstractModel, TimeStampAdbstractModel, MetaDataAbstractModel
):
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="subcategories/%Y-%m-%d",
        default="defaults/no-image.webp",
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        verbose_name="Категория",
        related_name="subcategories",
    )
    image_alt = models.CharField(verbose_name="Описание картинки", max_length=200)

    class Meta:
        verbose_name = "Подкатегория продукта"
        verbose_name_plural = "8. Подкатегории продуктов"

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:products-subcategory",
            kwargs={"category_slug": self.category.slug, "subcategory_slug": self.slug},
        )

    def clean_category(self):
        if self.category is None:
            self.is_active = False


class Product(ProductAbstractModel):
    subcategory = models.ForeignKey(
        ProductSubcategory,
        on_delete=models.PROTECT,
        verbose_name="Подкатегория",
        related_name="products",
    )
    sku = models.CharField(max_length=25, unique=True, default=generate_sku, null=True)
    tax_percent: TaxPercent = models.ForeignKey(
        TaxPercent,
        on_delete=models.PROTECT,
        default=2,
        related_name="products",
        verbose_name="Налоговая ставка",
        help_text="Выберите налоговую ставку, применимую к данному товару. Вычисляется после скидки.",
    )

    @property
    def is_bouquet(self) -> bool:
        return False

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "6. Продукты"

    def get_relative_url(self):
        return reverse_lazy(
            "catalogue:product-details",
            kwargs={
                "category_slug": self.subcategory.category.slug,
                "subcategory_slug": self.subcategory.slug,
                "product_slug": self.slug,
            },
        )


class ProductReview(ItemReview):
    item = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Продукт",
    )


@receiver(post_save, sender=ProductReview)
def order_created(
    sender: Product,
    instance: ProductReview,
    created,
    **kwargs,
):
    country = SiteRepository.get_country()
    city = SiteRepository.get_city()
    if created:
        review = instance
        text = (
            f"*Новый отзыв на продукт оформлен!* 🎉\n\n"
            f"*ID отзыва*: `{review.pk}`\n"
            f"*Страна*: `{escape_markdown(country)}`\n"
            f"*Город*: `{escape_markdown(city)}`\n"
            f"*Имя автора*: `{escape_markdown(review.author_name)}`\n"
            f"*Email автора*: `{escape_markdown(review.email)}`\n"
            f"Вперёд за модерацию! 🚀"
        )
        send_message_to_telegram(text, get_admins_chat_ids())
