from django.contrib import admin

from .models import (
    BankAccount,
    Bill,
    Florist,
    Order,
    OrderBouquets,
    OrderCreditAdjustment,
    OrderDebitAdjustment,
    OrderProducts,
    RefundReceipt,
)


class BillInline(admin.StackedInline):
    model = Bill
    extra = 0
    show_change_link = True


class OrderInline(admin.StackedInline):
    model = Order
    extra = 0
    show_change_link = True


@admin.register(Florist)
class FloristAdmin(admin.ModelAdmin):
    list_display = ("title", "contact", "address", "vat_id")
    search_fields = ("title", "contact", "vat_id")
    list_filter = ("vat_id",)
    fieldsets = (
        ("Основная информация", {"fields": ("title", "contact", "address")}),
        (
            "Дополнительно",
            {
                "fields": ("vat_id", "description"),
            },
        ),
    )
    ordering = ("title",)
    inlines = [
        BillInline,
    ]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "florist",
        "brutto",
        "netto",
        "tax",
        "created_at",
        "is_paid",
    )
    search_fields = ("number", "florist__title")
    list_filter = ("florist", "account_paid_funds", "created_at")
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "number",
                    "florist",
                    "account_paid_funds",
                    "refund_receipt",
                    "is_paid",
                ),
            },
        ),
        (
            "Цены",
            {
                "fields": (
                    "brutto",
                    "netto",
                    "tax",
                ),
            },
        ),
        (
            "Изображение",
            {
                "fields": ("image",),
            },
        ),
        (
            "Дополнительная информация",
            {
                "fields": ("comment",),
            },
        ),
    )
    ordering = ("-created_at",)
    autocomplete_fields = ("florist",)


@admin.register(RefundReceipt)
class RefundReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "issue_date",
        "receipt_date",
        "refund_amount",
        "account_received_funds",
        "image_display",
    )

    list_filter = (
        "account_received_funds__title",
        "issue_date",
        "receipt_date",
    )

    search_fields = (
        "account_received_funds__title",
        "account_received_funds__number",
        "refund_amount",
    )

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "image",
                    "issue_date",
                    "receipt_date",
                    "refund_amount",
                ),
            },
        ),
        (
            "Дополнительно",
            {
                "fields": (
                    "account_received_funds",
                    "comment",
                ),
            },
        ),
    )

    def image_display(self, obj):
        if obj.image:
            return f"\u2714 {obj.image.name}"
        return "\u2718 Нет файла"

    image_display.short_description = "Файл подтверждения"
    ordering = ("-receipt_date",)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "owner_name",
        "number",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "owner_name",
        "number",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "title",
                    "owner_name",
                    "number",
                ),
            },
        ),
        (
            "Дополнительно",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "comment",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


class OrderProductsStackedInline(admin.StackedInline):
    model = OrderProducts
    extra = 0


class OrderBouquetsStackedInline(admin.StackedInline):
    model = OrderBouquets
    extra = 0


class OrderCreditAdjustmentInline(admin.StackedInline):
    model = OrderCreditAdjustment
    extra = 0
    verbose_name = "Корректировка (Кредит)"
    verbose_name_plural = "Корректировки (Кредит)"
    fk_name = "order"


class OrderDebitAdjustmentInline(admin.StackedInline):
    model = OrderDebitAdjustment
    extra = 0
    verbose_name = "Корректировка (Дебит)"
    verbose_name_plural = "Корректировки (Дебит)"
    fk_name = "order"

    readonly_fields = (
        "paid_amount",
        "transfer_date",
    )


@admin.register(Order)
class OrderAdminModel(admin.ModelAdmin):
    inlines = (
        OrderProductsStackedInline,
        OrderBouquetsStackedInline,
        OrderCreditAdjustmentInline,
        OrderDebitAdjustmentInline,
    )

    fieldsets = (
        (
            "Общая информация",
            {
                "fields": (
                    "user",
                    "manager",
                    "status",
                    "bill",
                    "code",
                    "created_at",
                    "updated_at",
                    "is_reported_to_tax",
                    "reporting_date",
                ),
            },
        ),
        (
            "Стоимость",
            {
                "fields": (
                    "grand_total",
                    "sub_total",
                    "tax",
                    "payment_system_fee",
                    "refund_currency_convertasion_fee",
                ),
            },
        ),
        (
            "Данные отправителя",
            {
                "fields": (
                    "address_form",
                    "name",
                    "email",
                ),
            },
        ),
        (
            "Данные получателя",
            {
                "fields": (
                    "recipient_address_form",
                    "recipient_name",
                    "recipient_phonenumber",
                ),
            },
        ),
        (
            "Доставка",
            {
                "fields": (
                    "delivery_price",
                    "delivery_vat_rate",
                    "delivery_date",
                    "delivery_time",
                    "instructions",
                    "clarify_address",
                    "country",
                    "city",
                    "postal_code",
                    "street",
                    "building",
                    "flat",
                    "is_recipient",
                    "is_surprise",
                ),
            },
        ),
        (
            "Открытка",
            {
                "fields": ("message_card",),
            },
        ),
        (
            "Согласия",
            {
                "fields": ("is_agreement_accepted",),
            },
        ),
        (
            "Дополнительная информация",
            {
                "fields": ("comment",),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "code",
    )

    list_display = (
        "grand_total",
        "delivery_date",
        "delivery_time",
        "recipient_name",
        "recipient_phonenumber",
        "street",
        "building",
        "flat",
        "code",
        "user",
    )

    search_fields = (
        "code",
        "recipient_phonenumber",
        "email",
    )

    ordering = ("-created_at",)


@admin.register(OrderCreditAdjustment)
class OrderCreditAdjustmentAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "paid_amount",
                    "receipt_date",
                    "taxes",
                    "payment_system_fee",
                    "comment",
                )
            },
        ),
        (
            "Банковская информация",
            {
                "fields": ("account_received_funds", "image", "external_reference"),
            },
        ),
        (
            "Налоговая информация",
            {
                "fields": ("tax_percent", "is_reported_to_tax", "reporting_date"),
            },
        ),
    )

    list_display = (
        "order",
        "paid_amount",
        "receipt_date",
        "taxes",
        "tax_percent",
        "created_at",
    )
    search_fields = ("order__code", "comment", "external_reference")
    list_filter = ("tax_percent", "order__status", "created_at")
    ordering = ("-created_at",)

    list_per_page = 20


@admin.register(OrderDebitAdjustment)
class OrderDebitAdjustmentAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "paid_amount",
                    "transfer_date",
                    "comment",
                )
            },
        ),
        (
            "Банковская информация",
            {
                "fields": ("account_received_funds", "image", "external_reference"),
            },
        ),
    )

    list_display = (
        "order",
        "paid_amount",
        "transfer_date",
        "created_at",
    )
    search_fields = ("order__code", "comment", "external_reference")
    list_filter = ("order__status", "created_at")
    ordering = ("-created_at",)

    list_per_page = 20
