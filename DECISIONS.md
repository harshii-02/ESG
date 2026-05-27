# Decisions

## SAP Source

I chose flat CSV export from SAP rather than IDoc/BAPI/OData. Enterprise onboarding often starts with the lowest-friction extract a client can email or export, and a four-day prototype should prove normalization before integration plumbing.

Subset handled:

- Fuel purchases/consumption rows
- Procurement spend/quantity rows
- German and English header aliases
- Plant-code lookup to facilities
- Mixed date formats and units

Ignored:

- IDoc segment trees
- SAP material master enrichment
- Multi-currency procurement conversion
- OData authentication

PM question: which SAP module/export is the client actually offering first: MM purchase orders, FI invoices, PM plant maintenance, or a custom ALV report?

## Utility Source

I chose portal CSV exports for electricity bills. Most facilities teams can download bills or interval summaries before API access is approved.

Subset handled:

- Account/meter number
- Billing period start/end
- kWh
- demand kW when present
- tariff name
- billing periods that cross calendar months

Ignored:

- PDF bill OCR
- Interval meter data
- Renewable certificates
- Market-based vs location-based Scope 2 split

PM question: does the client need both location-based and market-based Scope 2 reporting in this first workflow?

## Travel Source

I modeled a Concur/Navan-style expense/travel export CSV. Travel platforms commonly expose expense type, route/airport codes, distance when available, dates, and merchant/supplier data.

Subset handled:

- Flights with origin/destination airport codes
- Flights with distance present or derived from airport lookup for common routes
- Hotel room-nights
- Ground transport distance

Ignored:

- API OAuth sync
- Multi-leg itinerary reconstruction
- Cabin class multipliers
- Radiative forcing multipliers

PM question: should emissions be calculated from booked itinerary, expensed receipt, or paid invoice?

## Analyst UX

The dashboard focuses on review work:

- totals by status/scope
- failed import visibility
- suspicious flags
- source batch traceability
- approval action

I did not build generic CRUD because the assignment emphasizes analyst sign-off over data entry.

