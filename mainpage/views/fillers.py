from django.urls import reverse_lazy
from django.views.generic.base import TemplateView

from core.services.mixins import CanonicalsContextMixin, CommonContextMixin
from core.services.mixins.canonicals import CanonicalLinksMixin
from extended_contrib_models.models import Filial

from ..models import (
    AboutUsPageModel,
    ContactsPageModel,
    DeliveryPageModel,
    FAQPageModel,
    MainPageModel,
)


class FillerViewMixin:
    """
    Реализация паттернов «Шаблонный метод и «Стратегия».

    Филлерами называются дополнительные страницы, в основном посвящённые
    информированию пользователя. К примеру как с нами связаться, как работает
    доставка и т.д.
    """

    template_name = "mainpage/filler.html"
    http_method_names = ["get"]
    page_model: (
        AboutUsPageModel | DeliveryPageModel | ContactsPageModel | FAQPageModel
    ) = None
    relative_url: str = None

    def get_context_data(self, *args, **kwargs):
        if not self.page_model:
            raise NotImplementedError("Attribute “page_model” must be specified.")

        context = super().get_context_data(*args, **kwargs)
        page = self.page_model.objects.first()
        context["description"] = page.description
        context["meta_tags"] = page.meta_tags
        context["image_url"] = page.image.url
        context["image_alt"] = page.image_alt
        return context


class AboutUsView(
    FillerViewMixin,
    CommonContextMixin,
    CanonicalsContextMixin,
    CanonicalLinksMixin,
    TemplateView,
):
    """
    Контроллер который показывает страницу «О нас»
    """

    page_model = AboutUsPageModel
    relative_url = reverse_lazy("mainpage:about")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["is_about_us"] = True
        context["json_ld_description"] = (
            MainPageModel.objects.only("json_ld_description")
            .first()
            .json_ld_description
        )
        context["filials"] = Filial.objects.only("url").all()
        return context


class AboutDeliveryView(
    FillerViewMixin,
    CommonContextMixin,
    CanonicalsContextMixin,
    CanonicalLinksMixin,
    TemplateView,
):
    """
    Контроллер который показывает страницу «Доставка»
    """

    page_model = DeliveryPageModel
    relative_url = reverse_lazy("mainpage:delivery")


class ContactUsView(
    FillerViewMixin,
    CommonContextMixin,
    CanonicalsContextMixin,
    CanonicalLinksMixin,
    TemplateView,
):
    """
    Контроллер который показывает страницу «Контакты»
    """

    page_model = ContactsPageModel
    relative_url = reverse_lazy("mainpage:contact")


class FAQView(
    FillerViewMixin,
    CommonContextMixin,
    CanonicalsContextMixin,
    CanonicalLinksMixin,
    TemplateView,
):
    """
    Контроллер который показывает страницу «Часто задаваемые вопросы».

    На данный момент этот контроллер не подключён к роутеру, так как
    контент для неё ещё не составлен.
    """

    page_model = FAQPageModel
    relative_url = reverse_lazy("mainpage:faq")
