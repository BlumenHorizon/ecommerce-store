from abc import ABC, abstractmethod
from typing import Optional

from .types import (
    AbsoluteUrl,
    AlternateLink,
    AvailableLanguage,
    CanonicalLink,
    XDefaultLink,
)


class CanonicalLinksAbstract(ABC):
    """
    Абстрактный класс, который будет унаследован каждым
    контроллером с целью сгенерировал каноникалы и другие
    мета-ссылки для шаблонов.

    Гарантированно не влияет на локализацию генерируемой
    страницы.

    Методы:
    get_absolute_url(self) -> core.services.types.AbsoluteUrl
    get_canonical_link(self) -> core.services.types.CanonicalLink
    get_alternate_links(self) -> core.services.types.AlternateLink:
    get_xdefault_link(self) -> core.services.types.XDefaultLink:
    """

    @abstractmethod
    def get_canonical_link(self) -> CanonicalLink:
        """
        Генерирует canonical link для шаблона, абстрактный метод.
        Будет возвращать TypeError([пример](https://imgur.com/a/tmJFO1x))
        если его не реализовать на контроллере.
        """

    @abstractmethod
    def get_alternate_links(
        self,
        current_lang_code: str,
        available_languages: list[AvailableLanguage],
    ) -> list[AlternateLink]:
        """
        Генерирует alternate link для шаблона, абстрактный метод.
        Будет возвращать TypeError([пример](https://imgur.com/a/tmJFO1x))
        если его не реализовать на контроллере.
        """

    @abstractmethod
    def get_xdefault_link(
        self,
        default_lang_code: str,
    ) -> XDefaultLink:
        """
        Генерирует x-default link для шаблона, абстрактный метод.
        Будет возвращать TypeError([пример](https://imgur.com/a/tmJFO1x))
        если его не реализовать на контроллере.
        """

    @abstractmethod
    def get_absolute_url(self, lang_code: Optional[str] = None) -> AbsoluteUrl:
        """
        Генерирует абсолютный url для мета-ссылок шаблона для параметра href,
        опционально может менять язык для отображения требуемой странички
        взависимости от параметра lang_code, абстрактный метод.

        Будет возвращать TypeError([пример](https://imgur.com/a/tmJFO1x))
        если его не реализовать на контроллере.
        """

    @property
    @abstractmethod
    def relative_url(self) -> str:
        """
        Возвращает результат функции django.urls.reverse_lazy.
        Требуется для get_absolute_url.
        """
