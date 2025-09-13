import hashlib
from collections import defaultdict

from django.core.cache import caches
from django.http import HttpRequest, JsonResponse

from catalogue.models import Bouquet, Product

cache = caches["default"]


def generate_cache_key(query: str) -> str:
    """
    Генерирует уникальный ключ для кеширования на основе строки поиска.

    Используется хэширование MD5 для получения уникального идентификатора
    для каждого поискового запроса, чтобы предотвратить конфликт кешированных данных.

    Args:
        query (str): Строка запроса для поиска.

    Returns:
        str: Уникальный ключ для кеширования результатов поиска.
    """
    query_hash = hashlib.md5(query.encode("utf-8")).hexdigest()
    return f"search_results_{query_hash}"


def perform_search(query: str) -> dict:
    """
    Выполняет поиск по товарам и букетам по строке запроса.

    Выполняет фильтрацию товаров и букетов по совпадению с именем, используя
    запрос из строки и возвращает данные о первых 10 результатах.

    Args:
        query (str): Строка запроса для поиска.

    Returns:
        dict: Результаты поиска в формате словаря, содержащего разделение на продукты и букеты
              по категориям.
    """
    data = {"results": {"products": defaultdict(list), "bouquets": defaultdict(list)}}

    for model, key in [(Product, "products"), (Bouquet, "bouquets")]:
        results = (
            model.objects.select_related("subcategory__category", "subcategory")
            .only(
                "name",
                "subcategory__category__name",
                "subcategory__slug",
                "subcategory__category__slug",
                "slug",
            )
            .filter(
                name__icontains=query,
                is_active=True,
                subcategory__is_active=True,
                subcategory__category__is_active=True,
            )[:10]
        )
        for item in results:
            category_name = item.subcategory.category.name
            data["results"][key][category_name].append(
                {"name": item.name, "url": item.get_relative_url()}
            )

    return data


def live_search(request: HttpRequest) -> JsonResponse:
    """
    Обрабатывает запрос на поиск и возвращает результаты в формате JSON.

    Если запрос уже кеширован, возвращает данные из кеша. Если нет, выполняет поиск и кеширует
    результаты для дальнейших запросов.

    Args:
        request (HttpRequest): Объект запроса, содержащий строку поиска.

    Returns:
        JsonResponse: Ответ с результатами поиска в формате JSON.
    """
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"results": {"products": {}, "bouquets": {}}})

    cache_key = generate_cache_key(query)
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    data = perform_search(query)
    cache.set(cache_key, data, timeout=60 * 60)
    return JsonResponse(data)
