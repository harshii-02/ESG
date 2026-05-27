# Data Model

## Core Idea

The app separates the uploaded source file from normalized emission activity rows. That is the most important design decision: auditors need to know what source produced a row, analysts need to edit/review normalized rows, and ingestion errors should not disappear when a file is reprocessed.

## Models

### Organization

Tenant boundary. Every batch, facility, and activity belongs to an organization. In production this would be enforced through authenticated user membership; the prototype seeds one demo organization.

### Facility

Represents a plant, office, meter location, or cost-center location. SAP plant codes and utility meters are not meaningful by themselves, so facilities hold the business-readable name, country, and optional metadata.

### SourceBatch

One ingestion attempt. Stores:

- organization
- source type: SAP, utility, or travel
- filename / label
- status
- row counts
- timestamp

This is the source-of-truth anchor for auditability. Re-importing the same CSV should create a new batch instead of silently overwriting history.

### SourceRecord

One raw row from a SourceBatch. Stores:

- raw JSON payload
- parser status
- error message
- source row number

SourceRecord keeps evidence even when the row fails normalization. Analysts can see what failed and why.

### EmissionActivity

The normalized review row. Stores:

- tenant and source references
- scope: Scope 1, Scope 2, or Scope 3
- category: fuel combustion, purchased electricity, flight, hotel, ground transport, purchased goods
- activity date and optional period start/end
- facility
- supplier/vendor
- original quantity/unit
- normalized quantity/unit
- emission factor
- kgCO2e
- suspicious flags
- review status: needs_review, approved, rejected
- locked_at
- edited_from_source boolean

The row keeps both original and normalized quantities because unit conversion can be challenged later.

### AuditEvent

Append-only event log for import, edit, approve, and reject actions. For each action it stores actor, timestamp, event type, object id, and a small JSON diff/details payload.

## Multi-Tenancy

All business objects carry `organization_id`. API querysets filter by the demo organization. In a real deployment, middleware would resolve organization from the authenticated user or subdomain, and database constraints would prevent cross-tenant references.

## Scope Mapping

- SAP fuel: Scope 1
- SAP procurement: Scope 3, purchased goods/services
- Utility electricity: Scope 2
- Travel flights/hotels/ground: Scope 3

## Unit Normalization

The prototype normalizes:

- liters, gallons, and kWh for fuels/electricity
- kg, tonnes, and spend for procurement
- km and miles for travel distance
- room-nights for hotels

Each normalized row retains the original value and unit.

## Audit Trail

Approval locks an EmissionActivity by setting `locked_at`. Locked rows cannot be approved again or modified through the review endpoint. AuditEvent records the import and approval history.

