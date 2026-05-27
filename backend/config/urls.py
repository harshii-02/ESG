from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("ingestion.urls")),
    re_path(
        r"^assets/(?P<path>.*)$",
        RedirectView.as_view(url="/static/assets/%(path)s", permanent=False),
    ),
    re_path(r"^(?!api/|admin/).*", TemplateView.as_view(template_name="index.html")),
]
