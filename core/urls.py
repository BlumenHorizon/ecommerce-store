"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path, re_path
from django.views.i18n import JavaScriptCatalog, set_language

service_urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("i18n/setlang/", set_language, name="set_language"),
    path("", include("wysiwyg.urls")),
    path("", include("seo.urls")),
    path("merchant/", include("merchant.urls")),
]

i18n_urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", include("mainpage.urls")),
    path("accounts/", include("accounts.urls")),
    path("catalog/", include("catalogue.urls")),
    path("search/", include("livesearch.urls")),
    path("cart/", include("cart.urls")),
    prefix_default_language=False,
)

urlpatterns = service_urlpatterns + i18n_urlpatterns

if settings.DEBUG and not settings.TEST_MODE:
    urlpatterns.extend(debug_toolbar_urls())

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [re_path(r"^rosetta/", include("rosetta.urls"))]

urlpatterns.extend(static(settings.STATIC_DEFAULTS_URL, document_root=settings.STATIC_DEFAULTS_ROOT))
urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
