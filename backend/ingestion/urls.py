from django.urls import path

from . import views

urlpatterns = [
    path("summary/", views.summary),
    path("activities/", views.activities),
    path("activities/<int:pk>/approve/", views.approve_activity),
    path("audit/", views.audit_events),
    path("failed-records/", views.failed_records),
    path("ingest/<str:source_type>/", views.ingest),
    path("samples/<str:source_type>/", views.sample_csv),
]
