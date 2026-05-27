from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import AuditEvent, EmissionActivity, Organization, SourceBatch, SourceRecord
from .parsers import INGESTERS, SAMPLE_CSV
from .serializers import AuditEventSerializer, EmissionActivitySerializer, SourceRecordSerializer


def demo_org():
    return Organization.objects.get_or_create(name="Breathe Demo Client", slug="breathe-demo")[0]


@api_view(["GET"])
def sample_csv(request, source_type):
    if source_type not in SAMPLE_CSV:
        return Response({"error": "Unknown source type"}, status=404)
    response = HttpResponse(SAMPLE_CSV[source_type], content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{source_type}_sample.csv"'
    return response


@api_view(["POST"])
def ingest(request, source_type):
    if source_type not in INGESTERS:
        return Response({"error": "Unknown source type"}, status=404)
    org = demo_org()
    upload = request.FILES.get("file")
    text = upload.read().decode("utf-8-sig") if upload else request.data.get("csv", "")
    if not text.strip():
        text = SAMPLE_CSV[source_type]
    batch = SourceBatch.objects.create(
        organization=org,
        source_type=source_type,
        label=upload.name if upload else f"{source_type} sample import",
    )
    total, failed = INGESTERS[source_type](org, batch, text)
    batch.total_rows = total
    batch.failed_rows = failed
    batch.status = "processed_with_errors" if failed else "processed"
    batch.save(update_fields=["total_rows", "failed_rows", "status"])
    AuditEvent.objects.create(
        organization=org,
        event_type="batch_imported",
        object_type="SourceBatch",
        object_id=str(batch.id),
        details={"source_type": source_type, "total_rows": total, "failed_rows": failed},
    )
    return Response({"batch_id": batch.id, "total_rows": total, "failed_rows": failed})


@api_view(["GET"])
def activities(request):
    org = demo_org()
    queryset = EmissionActivity.objects.filter(organization=org).select_related("batch", "facility")
    status_filter = request.GET.get("status")
    if status_filter:
        queryset = queryset.filter(review_status=status_filter)
    return Response(EmissionActivitySerializer(queryset, many=True).data)


@api_view(["POST"])
def approve_activity(request, pk):
    org = demo_org()
    try:
        activity = EmissionActivity.objects.get(id=pk, organization=org)
    except EmissionActivity.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if activity.is_locked:
        return Response({"error": "Activity is already locked"}, status=409)
    activity.review_status = EmissionActivity.APPROVED
    activity.locked_at = timezone.now()
    activity.save(update_fields=["review_status", "locked_at"])
    AuditEvent.objects.create(
        organization=org,
        event_type="activity_approved",
        object_type="EmissionActivity",
        object_id=str(activity.id),
        details={"kg_co2e": str(activity.kg_co2e), "scope": activity.scope},
    )
    return Response(EmissionActivitySerializer(activity).data)


@api_view(["GET"])
def summary(request):
    org = demo_org()
    activities_qs = EmissionActivity.objects.filter(organization=org)
    status_counts = dict(activities_qs.values_list("review_status").annotate(count=Count("id")))
    scope_totals = activities_qs.values("scope").annotate(kg_co2e=Sum("kg_co2e"), rows=Count("id"))
    flagged = activities_qs.exclude(suspicious_flags=[]).count()
    return Response(
        {
            "total_rows": activities_qs.count(),
            "total_kg_co2e": activities_qs.aggregate(total=Sum("kg_co2e"))["total"] or 0,
            "status_counts": status_counts,
            "scope_totals": list(scope_totals),
            "flagged_rows": flagged,
            "failed_rows": SourceBatch.objects.filter(organization=org).aggregate(total=Sum("failed_rows"))["total"] or 0,
        }
    )


@api_view(["GET"])
def audit_events(request):
    org = demo_org()
    events = AuditEvent.objects.filter(organization=org)[:50]
    return Response(AuditEventSerializer(events, many=True).data)


@api_view(["GET"])
def failed_records(request):
    org = demo_org()
    records = SourceRecord.objects.filter(batch__organization=org, status="failed").select_related("batch")[:50]
    return Response(SourceRecordSerializer(records, many=True).data)
