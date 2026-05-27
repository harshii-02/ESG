from django.contrib import admin

from .models import AuditEvent, EmissionActivity, Facility, Organization, SourceBatch, SourceRecord

admin.site.register(Organization)
admin.site.register(Facility)
admin.site.register(SourceBatch)
admin.site.register(SourceRecord)
admin.site.register(EmissionActivity)
admin.site.register(AuditEvent)

