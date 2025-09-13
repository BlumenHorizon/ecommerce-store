import os

from django.conf import settings
from django.utils.translation import get_language

from core.services.repositories import SiteRepository
from extended_contrib_models.models import Filial


class CommonContextMixin:
    def get_context_data(self, *args, **kwargs):
        "Must be implemented and inherited by every view"
        context = super().get_context_data(*args, **kwargs)
        if not context.get("site_name"):
            context["site_name"] = SiteRepository.get_name()
            context["domain_name"] = SiteRepository.get_domain()
            context["company_email"] = SiteRepository.get_email()
        context["DEBUG"] = settings.DEBUG
        context["gtag_id"] = os.getenv("GTAG_ID")
        context["merchant_id"] = os.getenv("MERCHANT_ID")
        context["currency_symbol"] = SiteRepository.get_currency_symbol()
        context["currency_code"] = SiteRepository.get_currency_code()
        context["country"] = SiteRepository.get_country()
        context["country_code"] = SiteRepository.get_country_code()
        context["city"] = SiteRepository.get_city()
        context["socials_right_bottom"] = SiteRepository.get_socials()
        context["MEDIA_URL"] = settings.MEDIA_URL
        context["alert"] = SiteRepository.get_alert_message()
        context["filials"] = Filial.objects.only("title", "url").order_by("title").all()
        return context


class CanonicalsContextMixin:
    def get_context_data(self, *args, **kwargs):
        """
        Наследуется каждым контроллером, который требует
        генерации canonical/alternate/x-default ссылок.
        """
        context = super().get_context_data(*args, **kwargs)

        current_lang_code = get_language()
        context["canonical_link"] = self.get_canonical_link(current_lang_code)
        context["alternate_links"] = self.get_alternate_links(
            current_lang_code,
            settings.LANGUAGES,
        )
        context["xdefault_link"] = self.get_xdefault_link(settings.LANGUAGES[0][0])
        return context
