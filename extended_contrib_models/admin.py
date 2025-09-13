from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import AdminsTelegramChatIDs, ExtendedSite, Social


@admin.register(Social)
class SocialAdmin(admin.ModelAdmin):
    list_display = (
        "absolute_url",
        "background_hex_code",
        "bootstrap_icon",
        "extended_site",
    )
    search_fields = ("absolute_url", "bootstrap_icon", "extended_site__site__domain")


class SocialInline(admin.StackedInline):
    model = Social
    extra = 0
    max_num = 3
    verbose_name = "Соц. сеть"
    verbose_name_plural = "Социальные сети"


@admin.register(ExtendedSite)
class ExtendedSiteAdmin(TranslationAdmin):
    list_display = (
        "site",
        "currency_code",
        "currency_symbol",
        "country",
        "city",
        "email",
        "header_alert_message",
    )
    search_fields = (
        "site__domain",
        "currency_code",
        "currency_symbol",
        "country",
        "city",
    )
    inlines = [SocialInline]


@admin.register(AdminsTelegramChatIDs)
class AdminsTelegramChatIDsAdmin(admin.ModelAdmin):
    list_display = ("id", "chat_id")
    search_fields = ("chat_id",)
    list_filter = ("id",)
    ordering = ("-id",)
