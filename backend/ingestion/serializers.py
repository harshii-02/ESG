from rest_framework import serializers

from .models import AuditEvent, EmissionActivity, SourceBatch, SourceRecord


class SourceBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceBatch
        fields = ["id", "source_type", "label", "status", "received_at", "total_rows", "failed_rows"]


class EmissionActivitySerializer(serializers.ModelSerializer):
    batch = SourceBatchSerializer(read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    facility_code = serializers.CharField(source="facility.code", read_only=True)

    class Meta:
        model = EmissionActivity
        fields = [
            "id",
            "batch",
            "facility_name",
            "facility_code",
            "scope",
            "category",
            "activity_date",
            "period_start",
            "period_end",
            "supplier",
            "description",
            "original_quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "emission_factor",
            "kg_co2e",
            "suspicious_flags",
            "review_status",
            "edited_from_source",
            "locked_at",
            "created_at",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "event_type", "actor", "object_type", "object_id", "details", "created_at"]


class SourceRecordSerializer(serializers.ModelSerializer):
    batch = SourceBatchSerializer(read_only=True)

    class Meta:
        model = SourceRecord
        fields = ["id", "batch", "row_number", "raw_payload", "status", "error"]
