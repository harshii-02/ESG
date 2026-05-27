from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=2, default="IN")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("organization", "code")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceBatch(models.Model):
    SAP = "sap"
    UTILITY = "utility"
    TRAVEL = "travel"
    SOURCE_CHOICES = [(SAP, "SAP"), (UTILITY, "Utility"), (TRAVEL, "Travel")]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    label = models.CharField(max_length=180)
    status = models.CharField(max_length=30, default="processed")
    received_at = models.DateTimeField(default=timezone.now)
    total_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.source_type} {self.label}"


class SourceRecord(models.Model):
    batch = models.ForeignKey(SourceBatch, on_delete=models.CASCADE, related_name="records")
    row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField(default=dict)
    status = models.CharField(max_length=30, default="parsed")
    error = models.TextField(blank=True)


class EmissionActivity(models.Model):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"

    REVIEW_CHOICES = [
        (NEEDS_REVIEW, "Needs review"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    batch = models.ForeignKey(SourceBatch, on_delete=models.CASCADE, related_name="activities")
    source_record = models.OneToOneField(SourceRecord, on_delete=models.CASCADE, related_name="activity")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    scope = models.CharField(max_length=10)
    category = models.CharField(max_length=80)
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=160, blank=True)
    description = models.CharField(max_length=240)
    original_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    original_unit = models.CharField(max_length=40)
    normalized_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    normalized_unit = models.CharField(max_length=40)
    emission_factor = models.DecimalField(max_digits=12, decimal_places=6)
    kg_co2e = models.DecimalField(max_digits=14, decimal_places=4)
    suspicious_flags = models.JSONField(default=list, blank=True)
    review_status = models.CharField(max_length=30, choices=REVIEW_CHOICES, default=NEEDS_REVIEW)
    edited_from_source = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_locked(self):
        return self.locked_at is not None


class AuditEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=40)
    actor = models.CharField(max_length=120, default="demo.analyst@breatheesg.com")
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

