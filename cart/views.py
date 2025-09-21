import logging
from typing import Any, Collection

import stripe
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponseForbidden, JsonResponse
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView, FormView
from stripe import InvalidRequestError

from accounts.models import User
from catalogue.models import Bouquet, BouquetImage, Product, ProductImage
from core.services.dataclasses.related_model import RelatedModel
from core.services.mixins import CommonContextMixin
from core.services.repositories import SiteRepository
from core.services.utils.recommended_items import get_recommended_items_with_first_image
from core.services.utils.urls import build_absolute_url

from .cart import BouquetCart, ProductCart
from .forms import OrderForm
from .models import Order, OrderBouquets, OrderProducts
from .services.mixins.edit import (
    CartBouquetEditMixin,
    CartEditAbstractMixin,
    CartItemAddMixin,
    CartItemRemoveMixin,
    CartItemRemoveSingleMixin,
    CartProductEditMixin,
)

stripe.api_key = settings.STRIPE_API_KEY


class CartView(CommonContextMixin, FormView):
    template_name = "cart/index.html"
    form_class = OrderForm

    def form_valid(self, form: OrderForm):
        """
        Обрабатывает успешную отправку формы оформления заказа, генерирует список товаров
        для страницы оплаты Stripe и перенаправляет пользователя на страницу оплаты.

        После успешного оформления заказа сохраняет заказ, генерирует элементы для Stripe,
        добавляет код заказа в сессию пользователя и формирует URL для страницы оплаты Stripe.

        Параметры:
        form (OrderForm): Форма, содержащая данные о заказе (продукты, букеты и т. д.).

        Возвращает:
        HttpResponseRedirect: Перенаправление пользователя на страницу оплаты Stripe.
        """
        logger = logging.getLogger("django_stripe")
        order = self.save_order(
            form,
            self.request,
        )

        line_items = self.generate_line_items_and_attach_first_images(
            order.products,
            order.bouquets,
            SiteRepository.get_currency_code(),
        )

        self.add_order_in_user_session(self.request, order.code)
        try:
            self.success_url = self.generate_payment_page_url(
                order.code,
                customer_email=order.email,
                line_items=line_items,
            )
        except InvalidRequestError:
            logger.error(
                "Ошибка в генерации ссылки для оплаты, возможно введён некорректный метод оплаты.",
                stack_info=True,
            )
        return super().form_valid(form)

    @staticmethod
    def generate_payment_page_url(
        order_code: str,
        customer_email: str,
        line_items: list[dict[str, str | int]],
    ) -> str | None:
        """
        Генерирует URL для страницы оплаты Stripe с учётом переданных данных.

        Эта функция создаёт сессию оплаты в Stripe с указанными товарами, email клиента,
        и генерирует URL для успешной и отменённой оплаты. Возвращает URL страницы оплаты,
        которая будет использована для перенаправления клиента.

        Параметры:
        domain (str): Домен сайта, на котором будет размещена страница оплаты.
        order_code (str): Код заказа, который используется в URL успешной оплаты и метаданных.
        customer_email (str): Электронная почта клиента, для которой создается сессия оплаты.
        line_items (list[dict]): Список товаров, которые будут отображаться на странице оплаты.

        Возвращает:
        str: URL страницы для завершения оплаты в Stripe.
        """
        checkout_session = stripe.checkout.Session.create(
            billing_address_collection="required",
            line_items=line_items,
            mode="payment",
            customer_email=customer_email,
            success_url=build_absolute_url(
                reverse_lazy(
                    "cart:success-order",
                    kwargs={"order_code": order_code},
                )
            ),
            cancel_url=build_absolute_url(
                reverse_lazy("cart:show"),
            ),
            metadata={
                "order_code": order_code,
            },
            payment_method_types=[
                "card",
                "ideal",
                "klarna",
                "paypal",
                "revolut_pay",
                "link",
                "bancontact",
                "eps",
                "p24",
            ],
        )
        return checkout_session.url

    def generate_line_items_and_attach_first_images(
        self,
        order_products: BaseManager[OrderProducts],
        order_bouquets: BaseManager[OrderBouquets],
        currency: str,
    ) -> list[dict[str, Any]]:
        """
        Генерирует список элементов для Stripe и прикрепляет первое изображение продукта.

        Эта функция проходит по всем продуктам и букетам в заказе, прикрепляет первое изображение
        каждого продукта и генерирует элементы для Stripe (line items), которые будут использоваться
        при создании сессии оплаты.

        Параметры:
        order_products (BaseManager[OrderProducts]): Менеджер для получения продуктов из заказа.
        order_bouquets (BaseManager[OrderBouquets]): Менеджер для получения букетов из заказа.
        currency (str): Валюта, которая будет использована для отображения в Stripe.

        Возвращает:
        tuple: Кортеж, содержащий:
            - Список элементов заказа для продуктов (QuerySet[OrderProducts]).
            - Список элементов заказа для букетов (QuerySet[OrderBouquets]).
            - Список line items для Stripe (list[dict[str, str | int]]).
        """
        line_items = []
        for order_product in order_products.all():
            if ProductImage := order_product.product.images.first():
                order_product.product.first_image_url = ProductImage.absolute_url
            else:
                order_product.product.first_image_url = build_absolute_url(
                    static("defaults/no-image.webp")
                )
            line_items.append(
                self.create_line_item(
                    order_product,
                    order_product.quantity,
                    currency,
                    order_product.product.tax_percent.stripe_id,
                )
            )
        for order_bouquet in order_bouquets.all():
            if BouquetImage := order_bouquet.product.images.first():
                order_bouquet.product.first_image_url = BouquetImage.absolute_url
            else:
                order_bouquet.product.first_image_url = build_absolute_url(
                    static("defaults/no-image.webp")
                )

            line_items.append(
                self.create_line_item(
                    order_bouquet,
                    order_bouquet.quantity,
                    currency,
                    order_bouquet.product.tax_percent.stripe_id,
                )
            )
        return line_items

    @staticmethod
    def create_line_item(
        order_product: OrderBouquets | OrderProducts,
        quantity: int,
        currency: str,
        tax_rate_id: str,
    ) -> dict[str, Collection[str]]:
        """
        Создаёт элемент для Stripe (line item) на основе данных о продукте или букете.

        Функция формирует словарь, который будет использоваться в сессии Stripe для
        представления одного товара или букета, включая информацию о его цене,
        названии, изображении и количестве.

        Параметры:
        order_product (OrderBouquets | OrderProducts): Объект продукта или букета из заказа.
        quantity (int): Количество товара или букета в заказе.
        currency (str): Валюта, используемая для расчётов в Stripe.
        domain (str): Домен сайта, необходимый для формирования корректных URL изображений.

        Возвращает:
        dict: Словарь, представляющий элемент заказа для Stripe с ценой, названием, изображением и количеством.
        """
        return {
            "price_data": {
                "currency": currency,
                "product_data": {
                    "name": f"{order_product.product.name}",
                    "images": [order_product.product.first_image_url],
                    "tax_code": "txcd_99999999",
                },
                "unit_amount_decimal": f"{order_product.tax_price_discounted * 100}",
                "tax_behavior": "inclusive",
            },
            "quantity": quantity,
            "tax_rates": [
                tax_rate_id,
            ],
        }

    @staticmethod
    def add_order_in_user_session(request: HttpRequest, order_code: str):
        """
        Добавляет код заказа в сессию пользователя.

        Эта функция добавляет код нового заказа в сессию пользователя. Если в сессии уже существует
        список заказов, она добавляет код нового заказа в этот список. Если заказов в сессии нет,
        создаётся новый список с кодом заказа.

        Параметры:
        request (HttpRequest): Объект запроса, содержащий сессию пользователя.
        order_code (str): Код нового заказа, который должен быть добавлен в сессию.

        Возвращает:
        None
        """
        if "orders" in request.session:
            request.session["orders"].append(order_code)
            request.session.save()
        else:
            request.session["orders"] = [
                order_code,
            ]
            request.session.save()

    def save_order(self, form: OrderForm, request: HttpRequest):
        """
        Сохраняет заказ в базе данных, делегируя процесс сохранения в отдельную функцию.

        Эта функция извлекает корзины продуктов и букетов из сессии пользователя, получает процент НДС
        из репозитория общих данных сайта и язык из текущих настроек, а затем передаёт все данные в метод
        save_order_in_db, который выполняет сохранение заказа в базе данных и извлечение связанных данных.

        Параметры:
        form (OrderForm): Форма, содержащая информацию о заказе.
        request (HttpRequest): Объект запроса, содержащий информацию о сессии и пользователе.

        Возвращает:
        Order: Объект заказа, сохранённый в базе данных, с дополнительными связанными данными.
        """
        from django.utils.translation import get_language

        products_cart = ProductCart(
            session=request.session, session_key=ProductCart.session_key
        )
        bouquets_cart = BouquetCart(
            session=request.session, session_key=BouquetCart.session_key
        )
        language_code = get_language()
        return self.save_order_in_db(
            form,
            products_cart,
            bouquets_cart,
            request.user,
            request.session.session_key,
            language_code,
        )

    @staticmethod
    def save_order_in_db(
        form: OrderForm,
        products_cart: ProductCart,
        bouquets_cart: BouquetCart,
        user: User | AnonymousUser,
        session_key: Any,
        language_code: str,
    ) -> Order:
        """
        Сохраняет заказ в базе данных и извлекает дополнительные данные о заказе.

        Эта функция сохраняет заказ в базе данных, используя данные из формы, корзины продуктов и букетов,
        а также налоговый процент, сессионный ключ, язык и пользователя. После сохранения заказа в базу,
        она извлекает и возвращает заказ с предзагруженными и оптимизированными связанными данными для дальнейшего использования.

        Параметры:
        form (OrderForm): Форма, содержащая информацию о заказе.
        products_cart (ProductCart): Корзина продуктов для заказа.
        bouquets_cart (BouquetCart): Корзина букетов для заказа.
        user (User): Пользователь, совершивший заказ.
        session_key (Any): Сессионный ключ, связанный с текущим заказом.
        language_code (str): Код языка, используемый для оформления заказа.

        Возвращает:
        Order: Сохранённый объект заказа с предзагруженными и оптимизированными связанными данными.
        """
        order = form.save(
            products_cart=products_cart,
            bouquets_cart=bouquets_cart,
            session_key=session_key,
            language_code=language_code,
            user=user,
        )
        order = (
            Order.objects.prefetch_related(
                "products",
                "products__product",
                "bouquets",
                "bouquets__product",
                "products__product__tax_percent",
                "bouquets__product__tax_percent",
                "products__product__subcategory",
                "bouquets__product__subcategory",
                "products__product__images",
                "bouquets__product__images",
                "bouquets__product__colors",
                "bouquets__product__subcategory__category",
                "products__product__subcategory__category",
            )
            .only(
                "code",
                "name",
                "email",
                "address_form",
                "name",
                "country",
                "city",
                "street",
                "building",
                "postal_code",
                "flat",
                "delivery_date",
                "delivery_time",
                "message_card",
                "instructions",
                "tax",
                "sub_total",
                "grand_total",
                "created_at",
                "recipient_address_form",
                "recipient_name",
                "recipient_phonenumber",
                "products__quantity",
                "bouquets__quantity",
                "products__product__name",
                "products__product__discount",
                "products__product__price",
                "products__product__discount_expiration_datetime",
                "products__product__tax_percent__value",
                "products__product__tax_percent__stripe_id",
                "products__product__slug",
                "products__product__subcategory__slug",
                "products__product__subcategory__category__slug",
                "bouquets__product__name",
                "bouquets__product__discount",
                "bouquets__product__price",
                "bouquets__product__discount_expiration_datetime",
                "bouquets__product__tax_percent__value",
                "bouquets__product__tax_percent__stripe_id",
                "bouquets__product__slug",
                "bouquets__product__subcategory__slug",
                "bouquets__product__subcategory__category__slug",
                "bouquets__product__colors__name",
            )
            .get(pk=order.pk)
        )
        return order

    def get_context_data(self, *args, **kwargs):
        """
        Формирует контекст для страницы корзины, включая информацию о товарах в корзине,
        рекомендуемых товарах и букетах, а также расчетах налогов и итоговой суммы.

        Эта функция извлекает данные о корзине пользователя
        (как для продуктов, так и для букетов), рассчитывает налог,
        итоговую и предварительную сумму заказа, а также получает
        рекомендуемые товары и букеты на основе различных критериев.

        Параметры:
        *args: Дополнительные позиционные аргументы.
        **kwargs: Дополнительные именованные аргументы.

        Возвращает:
        dict: Контекст, содержащий:
            - "products_cart": Объект корзины с продуктами для текущего пользователя.
            - "bouquets_cart": Объект корзины с букетами для текущего пользователя.
            - "recommended_products": Список рекомендованных товаров для пользователя.
            - "recommended_bouquets": Список рекомендованных букетов для пользователя.
            - "tax": Сумма налога для текущего заказа.
            - "sub_total": Сумма заказа без налога.
            - "grand_total": Итоговая сумма заказа с учетом налога.
        """
        context = super().get_context_data(*args, **kwargs)
        context["products_cart"] = ProductCart(
            True, self.request.session, session_key=ProductCart.session_key
        )
        context["bouquets_cart"] = BouquetCart(
            True, self.request.session, session_key=BouquetCart.session_key
        )
        related_models = [
            RelatedModel(model="subcategory", fields=["slug", "name"]),
            RelatedModel(model="subcategory__category", fields=["slug"]),
            RelatedModel(model="tax_percent", fields=["value"]),
        ]
        context["recommended_products"] = get_recommended_items_with_first_image(
            model=Product,
            image_model=ProductImage,
            related_models=related_models,
            order_fields=[
                "-amount_of_orders",
                "-amount_of_savings",
            ],
            limit=6,
        )
        context["recommended_bouquets"] = get_recommended_items_with_first_image(
            model=Bouquet,
            image_model=BouquetImage,
            related_models=related_models,
            order_fields=[
                "-amount_of_orders",
                "-amount_of_savings",
            ],
            limit=6,
        )
        context["agb_url"] = reverse_lazy("mainpage:agb")
        context["privacy_policy_url"] = reverse_lazy("mainpage:privacy-and-policy")

        products_cart: ProductCart = context["products_cart"]
        bouquets_cart: BouquetCart = context["bouquets_cart"]
        grand_total = products_cart.total + bouquets_cart.total
        tax = products_cart.total_tax_amount + bouquets_cart.total_tax_amount
        sub_total = grand_total - tax
        context["tax"] = tax
        context["sub_total"] = sub_total
        context["grand_total"] = grand_total
        return context


class CartBouquetAddView(
    CartItemAddMixin,
    CartBouquetEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Букет "{product_name}" успешно добавлен в корзину.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка добавления букета в корзину.")


class CartProductAddView(
    CartItemAddMixin,
    CartProductEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Продукт "{product_name}" успешно добавлен в корзину.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка добавления продукта в корзину.")


class CartBouquetRemoveView(
    CartItemRemoveMixin,
    CartBouquetEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Букет "{product_name}" успешно убран из корзины.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка удаления букета из корзины.")


class CartProductRemoveView(
    CartItemRemoveMixin,
    CartProductEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Продукт "{product_name}" успешно убран из корзины.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка удаления продукта из корзины.")


class CartBouquetRemoveSingleView(
    CartItemRemoveSingleMixin,
    CartBouquetEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Количество букета "{product_name}" успешно уменьшено.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка уменьшения количества букета в корзине.")


class CartProductRemoveSingleView(
    CartItemRemoveSingleMixin,
    CartProductEditMixin,
    CartEditAbstractMixin,
    BaseFormView,
):
    def get_success_message(self, product):
        return _('Количество продукта "{product_name}" успешно уменьшено.').format(
            product_name=product.name
        )

    def get_error_message(self):
        return _("Ошибка уменьшения количества продукта в корзине.")


def cart_clear(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        product_cart = ProductCart(
            session=request.session, session_key=ProductCart.session_key
        )
        bouquet_cart = BouquetCart(
            session=request.session, session_key=BouquetCart.session_key
        )
        for cart in (product_cart, bouquet_cart):
            cart.clear()
        return JsonResponse(
            {
                "detail": _("Корзина очищена"),
                "status": "success",
                "grand_total": product_cart.total + bouquet_cart.total,
                "count": product_cart.count + bouquet_cart.count,
            },
            status=200,
        )
    return JsonResponse(
        {
            "detail": _("Метод не разрешен. Используйте POST."),
            "status": "error",
        },
        status=405,
    )


class SuccessOrderView(CommonContextMixin, TemplateView):
    template_name = "cart/success_order.html"
    http_method_names = [
        "get",
    ]

    def get(self, request, *args, **kwargs):
        order_code = self.kwargs["order_code"]
        try:
            self.order = Order.objects.only(
                "created_at",
                "code",
                "grand_total",
                "email",
                "status",
                "delivery_date",
                "delivery_time",
            ).get(code=order_code)
        except Order.DoesNotExist:
            return HttpResponseForbidden()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["order"] = self.order
        return context
