from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from telegram.helpers import escape_markdown

from catalogue.models import Bouquet, Product, TaxPercent, generate_sku
from core.base_models import TimeStampAdbstractModel
from tg_bot import send_message_to_telegram
from tg_bot.utils import get_admins_chat_ids


class Florist(TimeStampAdbstractModel, models.Model):
    title = models.CharField(verbose_name="Название", max_length=255)
    contact = models.TextField(verbose_name="Контакт флориста")
    address = models.TextField(verbose_name="Адрес флориста", null=True, blank=True)
    vat_id = models.CharField(
        max_length=15,
        verbose_name="НДС/Налоговый номер флориста",
        null=True,
        blank=True,
    )
    description = models.TextField(
        verbose_name="Описание флориста",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "3. Флорист"
        verbose_name_plural = "3. Флористы"


class BankAccount(TimeStampAdbstractModel, models.Model):
    title = models.CharField(verbose_name="Название банка", max_length=255)
    owner_name = models.CharField(verbose_name="Имя владельца счёта", max_length=255)
    number = models.CharField(verbose_name="Номер счёта", max_length=255, unique=True)
    comment = models.TextField(
        verbose_name="Комментарий",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "5. Банковский счёт"
        verbose_name_plural = "5. Банковские счета"

    def __str__(self):
        return f"{self.title} [{self.number}]"


class RefundReceipt(TimeStampAdbstractModel, models.Model):
    image = models.FileField(
        upload_to="refund_receipts/%Y-%m-%d",
        verbose_name="Подтверждение возврата от флориста",
        help_text="В случае если флорист сделал свою работу плохо и мы добились возврата (фото/PDF-файл)",
        null=True,
        blank=True,
    )
    issue_date = models.DateTimeField(
        verbose_name="Дата выдачи",
    )
    receipt_date = models.DateTimeField(
        verbose_name="Дата поступления",
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма возврата",
        help_text="Указано в чеке возврата",
        null=True,
        blank=True,
    )
    account_received_funds = models.ForeignKey(
        BankAccount,
        models.PROTECT,
        verbose_name="Банковский счёт на который вернули деньги",
        related_name="refund_receipts",
    )
    comment = models.TextField(
        verbose_name="Комментарий",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "4. Чек возврата от флориста"
        verbose_name_plural = "4. Чеки возвратов от флористов"

    def __str__(self):
        return f"Чек возврата на сумму {self.refund_amount}"


class Bill(TimeStampAdbstractModel, models.Model):
    florist = models.ForeignKey(
        Florist,
        models.PROTECT,
        verbose_name="Флорист выдавший чек",
        related_name="bills",
    )
    brutto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Себестоимость",
        help_text="С налогом",
        null=True,
        blank=True,
    )
    netto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Себестоимость",
        help_text="Без налога",
        null=True,
        blank=True,
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Налог",
        null=True,
        blank=True,
    )
    number = models.CharField(
        max_length=255, verbose_name="Номер чека", null=True, blank=True
    )
    image = models.FileField(
        upload_to="bills/%Y-%m-%d",
        verbose_name="Фото/PDF-файл чека",
        null=True,
        blank=True,
    )
    refund_receipt = models.ForeignKey(
        RefundReceipt,
        models.PROTECT,
        verbose_name="Чек возврата от флориста",
        help_text="В случае если флорист сделал свою работу плохо и мы добились возврата",
        related_name="bills",
        null=True,
        blank=True,
    )
    account_paid_funds = models.ForeignKey(
        BankAccount,
        models.PROTECT,
        verbose_name="Банковский счёт с которого провели оплату",
        related_name="bills",
        null=True,
        blank=True,
    )
    is_paid = models.BooleanField(
        "Оплачено?",
        default=True,
    )
    comment = models.TextField(
        verbose_name="Комментарий",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "2. Чек"
        verbose_name_plural = "2. Чеки"

    def __str__(self):
        return f"#{self.number} - {self.florist.title}"


class Order(TimeStampAdbstractModel, models.Model):
    is_reported_to_tax = models.BooleanField(
        default=False,
        verbose_name="Сообщено в налоговую",
        help_text="Отметьте, если заказ был отправлен в налоговую",
    )
    reporting_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата отправки в налоговую",
        help_text="Дата, когда заказ был отправлен в налоговую",
    )
    STATUS_CHOICES = [
        ("processing", _("В обработке")),
        ("declined", _("Возврат")),
        ("awaiting_payment", _("Ожидание оплаты")),
        ("shipping", _("В доставке")),
        ("delivered", _("Доставлен")),
    ]
    ADDRESS_FORM_CHOICES = [
        ("Mr.", _("Уважаемый")),
        ("Mrs.", _("Уважаемая")),
    ]
    user = models.ForeignKey(
        get_user_model(),
        related_name="orders",
        verbose_name="Пользователь",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    manager = models.ForeignKey(
        get_user_model(),
        related_name="earned_orders",
        verbose_name="Менеджер принёсший заказ",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    session_key = models.CharField(
        max_length=255,
    )
    clarify_address = models.BooleanField(
        default=False,
        verbose_name="Уточнить адрес?",
    )
    country = models.CharField(
        verbose_name="Страна",
        max_length=40,
    )
    city = models.CharField(
        verbose_name="Город",
        max_length=40,
    )
    email = models.EmailField(
        verbose_name="Способ связи с заказчиком",
    )
    address_form = models.CharField(
        max_length=20,
        choices=ADDRESS_FORM_CHOICES,
        default="Mr.",
        verbose_name="Форма обращения к заказчику",
    )
    name = models.CharField(verbose_name="Имя заказчика", max_length=80)
    postal_code = models.CharField(
        verbose_name="Почтовый индекс",
        max_length=40,
        null=True,
        blank=True,
    )
    street = models.CharField(
        verbose_name="Улица",
        max_length=255,
        null=True,
        blank=True,
    )
    building = models.CharField(
        verbose_name="Здание",
        max_length=40,
        null=True,
        blank=True,
    )
    flat = models.CharField(
        verbose_name="Квартира/офис",
        max_length=40,
        null=True,
        blank=True,
    )
    delivery_date = models.DateField(verbose_name="Дата доставки")
    delivery_time = models.TimeField(verbose_name="Время доставки")
    delivery_vat_rate = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(100),
        ),
        verbose_name="Процент НДС на доставку",
        null=True,
        blank=True,
        default=0,
    )
    delivery_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Стоимость доставки",
        help_text="С налогом",
        null=True,
        blank=True,
    )
    message_card = models.TextField(
        verbose_name="Записка к букету",
        max_length=10000,
        null=True,
        blank=True,
    )
    instructions = models.TextField(
        verbose_name="Инструкции к доставке",
        max_length=800,
        null=True,
        blank=True,
    )
    recipient_address_form = models.CharField(
        max_length=20,
        choices=ADDRESS_FORM_CHOICES,
        default="Mr.",
        verbose_name="Форма обращения к получателю",
    )
    recipient_name = models.CharField(verbose_name="Имя получателя", max_length=80)
    recipient_phonenumber = models.CharField(
        verbose_name="Номер телефона получателя",
        max_length=30,
    )
    is_recipient = models.BooleanField(
        default=False,
        verbose_name="Заказчик - получатель?",
    )
    is_surprise = models.BooleanField(
        default=False,
        verbose_name="Доставка с сюрпризом?",
    )
    is_agreement_accepted = models.BooleanField(
        default=False,
        verbose_name="Соглашение с AGB и Datenschutz",
    )
    code = models.CharField(
        max_length=60,
        verbose_name="Код заказа",
        default=generate_sku,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="awaiting_payment",
        verbose_name="Статус заказа",
    )
    sub_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Чистая стоимость"),
        help_text="Без налога",
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Налоговая стоимость"),
        help_text="Стоимость налога",
    )
    payment_system_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Комиссия системы приёма платежей",
        help_text="Спросить у Виталика",
        null=True,
        blank=True,
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Итоговая стоимость"),
        help_text="С налогом",
    )
    refund_currency_convertasion_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Разница конвертации валюты",
        help_text="При возврате",
        null=True,
        blank=True,
    )
    language_code = models.CharField(
        max_length=2, verbose_name="Язык пользователя на сайте"
    )
    bill = models.OneToOneField(
        Bill,
        models.PROTECT,
        verbose_name="Чек",
        null=True,
        blank=True,
        related_name="orders",
        unique=True,
    )
    comment = models.TextField(
        verbose_name="Комментарий",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "1. Заказ"
        verbose_name_plural = "1. Заказы"

    def __str__(self):
        return f"{self.code} - {self.status}"


@receiver(post_save, sender=Order)
def order_created(sender: Order, instance: Order, created, **kwargs):
    if created:
        order = instance
        text = (
            f"*Новый заказ оформлен!* 🎉\n\n"
            f"*ID заказа*: `{order.id}`\n"
            f"*Стоимость*: `{order.grand_total} EUR`\n"
            f"*Страна*: `{escape_markdown(order.country)}`\n"
            f"*Город*: `{escape_markdown(order.city)}`\n"
            f"*Имя заказчика*: `{escape_markdown(order.name)}`\n"
            f"*Email заказчика*: `{escape_markdown(order.email)}`\n"
            f"*Имя получателя*: `{escape_markdown(order.recipient_name)}`\n"
            f"*Телефон получателя*: `{escape_markdown(order.recipient_phonenumber)}`\n\n"
            f"Вперёд за работу! 🚀"
        )

        send_message_to_telegram(text, get_admins_chat_ids())


class OrderItem(models.Model):
    discount = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(100),
        ),
        verbose_name="Скидка на продукт",
        null=True,
        default=0,
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена продукта",
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена продукта cо скидкой",
    )
    tax_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена продукта с налогом",
    )
    tax_price_discounted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена продукта со скидкой и налогом",
    )
    taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Всего заплаченных налогов",
    )
    quantity = models.IntegerField(verbose_name="Количество продукта")
    supplier_paid_taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Всего заплаченных налогов за продукт у поставщика",
        null=True,
        blank=True,
    )
    supplier_vat_rate = models.IntegerField(
        validators=(
            MinValueValidator(0),
            MaxValueValidator(100),
        ),
        verbose_name="Ставка НДС от поставщика",
        null=True,
        blank=True,
        default=0,
    )
    supplier_paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Заплаченная себестоимость поставщику",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"«{self.product.name}»"


class OrderProducts(TimeStampAdbstractModel, OrderItem):
    order = models.ForeignKey(
        Order,
        related_name="products",
        verbose_name="Заказ",
        on_delete=models.PROTECT,
    )
    product = models.ForeignKey(
        Product,
        related_name="orders",
        verbose_name="Продукт",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "Продукт в заказе"
        verbose_name_plural = "Продукты в заказе"


class OrderBouquets(TimeStampAdbstractModel, OrderItem):
    order = models.ForeignKey(
        Order,
        related_name="bouquets",
        verbose_name="Заказ",
        on_delete=models.PROTECT,
    )
    product = models.ForeignKey(
        Bouquet,
        related_name="orders",
        verbose_name="Букет",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "Букет в заказе"
        verbose_name_plural = "Букеты в заказе"

        def __str__(self):
            return f"{self.pk}"


class AbstractOrderAdjustment(models.Model):
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
        help_text="Сумма корректировки",
    )
    comment = models.TextField(
        verbose_name="Комментарий",
        blank=True,
        null=True,
        help_text="Опишите причину корректировки или дополнительные детали",
    )
    processed_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Обработано сотрудником",
        help_text="Сотрудник, который обработал данную транзакцию",
    )
    external_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Внешняя ссылка",
        help_text="Ссылка на внешний источник или номер транзакции",
    )
    is_reported_to_tax = models.BooleanField(
        default=False,
        verbose_name="Сообщено в налоговую",
        help_text="Отметьте, если транзакция была отправлена в налоговую",
    )
    reporting_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата отправки в налоговую",
        help_text="Дата, когда транзакция была отправлена в налоговую",
    )
    issue_date = models.DateTimeField(
        verbose_name="Дата инициации",
        help_text="Дата, когда была инициирована корректировка",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.get_adjustment_type_display()} - {self.paid_amount} ({self.issue_date})"


class OrderCreditAdjustment(TimeStampAdbstractModel, AbstractOrderAdjustment):
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="credit_adjustments",
        verbose_name="Заказ",
        help_text="Заказ, к которому относится корректировка",
    )
    image = models.FileField(
        upload_to="order_adjustments/credit/%Y-%m-%d",
        verbose_name="Изображение",
        help_text="Загрузите фото или PDF-файл, подтверждающий транзакцию",
        null=True,
        blank=True,
    )
    receipt_date = models.DateTimeField(
        verbose_name="Дата поступления средств",
        help_text="Дата, когда средства были зачислены на счет",
    )
    account_received_funds = models.ForeignKey(
        BankAccount,
        models.PROTECT,
        verbose_name="Банковский счёт на который поступили деньги",
        related_name="orders_credit_adjustments",
        help_text="Выберите банковский счёт, на который были зачислены средства",
    )
    tax_percent = models.ForeignKey(
        TaxPercent,
        default=1,
        on_delete=models.PROTECT,
        related_name="orders_credit_adjustments",
        verbose_name="Налоговая ставка",
        help_text="Выберите налоговую ставку, применимую к данной операции. Вычисляется после скидки.",
    )
    taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Всего заплаченных налогов клиентом",
        help_text="Сумма налога, уплаченная клиентом в рамках этой корректировки",
    )
    payment_system_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Комиссия системы приёма платежей",
        help_text="Спросить у Виталика",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Корректировка (начисление)"
        verbose_name_plural = "Корректировки (начисления)"

    def __str__(self):
        return f"Credit Adjustment - {self.paid_amount} ({self.issue_date})"


class OrderDebitAdjustment(TimeStampAdbstractModel, AbstractOrderAdjustment):
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="debit_adjustments",
        verbose_name="Заказ",
        help_text="Заказ, к которому относится корректировка",
    )
    image = models.FileField(
        upload_to="order_adjustments/debit/%Y-%m-%d",
        verbose_name="Изображение",
        help_text="Загрузите фото или PDF-файл, подтверждающий транзакцию",
        null=True,
        blank=True,
    )
    transfer_date = models.DateTimeField(
        verbose_name="Дата отправки средств",
        help_text="Дата, когда средства были отправлены клиенту",
    )
    account_received_funds = models.ForeignKey(
        BankAccount,
        models.PROTECT,
        verbose_name="Банковский счёт с которого вернули деньги",
        related_name="orders_debit_adjustments",
        help_text="Выберите банковский счёт, с которого были возвращены средства",
    )

    class Meta:
        verbose_name = "Корректировка (возврат)"
        verbose_name_plural = "Корректировки (возвраты)"

    def __str__(self):
        return f"Debit Adjustment - {self.paid_amount} ({self.issue_date})"
