import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from .models import AuditEvent, EmissionActivity, Facility, SourceRecord


SAMPLE_CSV = {
    "sap": """Buchungsdatum,Werk,Material,Materialart,Menge,ME,Lieferant,Belegart
2026-01-05,BLR01,Diesel for generator,FUEL,1250,L,Shell India,WA
14.01.2026,BLR01,Office laptops,PROCUREMENT,22,EA,Lenovo,RE
20260118,PNQ02,LPG canisters,FUEL,85,KG,Local Gas Co,WA
2026-01-20,UNKNOWN,Steel fixtures,PROCUREMENT,2.5,TON,Acme Metals,RE
""",
    "utility": """account_number,meter_number,facility_code,period_start,period_end,kwh,demand_kw,tariff
U-88210,MTR-BLR-01,BLR01,2026-01-01,2026-01-31,48210,218,HT Industrial
U-88210,MTR-BLR-01,BLR01,2026-02-01,2026-02-28,46110,205,HT Industrial
U-99012,MTR-MISSING,UNKNOWN,2026-01-15,2026-02-14,12800,71,Commercial
""",
    "travel": """trip_id,category,travel_date,origin,destination,distance,distance_unit,nights,vendor
T-1001,flight,2026-01-08,BLR,DEL,,,,IndiGo
T-1002,hotel,2026-01-09,Delhi,,,,3,Marriott
T-1003,ground,2026-01-10,Delhi,Gurgaon,34,km,,Uber
T-1004,flight,2026-01-22,BOM,LHR,4480,miles,,British Airways
""",
}

HEADER_ALIASES = {
    "date": ["date", "posting_date", "buchungsdatum", "travel_date"],
    "plant": ["plant", "werk", "facility_code"],
    "material": ["material", "description"],
    "material_type": ["material_type", "materialart", "type"],
    "quantity": ["quantity", "menge", "kwh", "distance", "nights"],
    "unit": ["unit", "me", "distance_unit"],
    "supplier": ["supplier", "lieferant", "vendor"],
}

FUEL_FACTORS = {
    "diesel": Decimal("2.68"),
    "lpg": Decimal("3.00"),
}

AIRPORT_DISTANCE_KM = {
    ("BLR", "DEL"): Decimal("1700"),
    ("DEL", "BLR"): Decimal("1700"),
    ("BOM", "LHR"): Decimal("7210"),
    ("LHR", "BOM"): Decimal("7210"),
}


def read_csv(text):
    return list(csv.DictReader(StringIO(text.strip())))


def normalize_key(row, canonical):
    lowered = {key.strip().lower(): value for key, value in row.items()}
    for alias in HEADER_ALIASES.get(canonical, [canonical]):
        if alias.lower() in lowered:
            return (lowered.get(alias.lower()) or "").strip()
    return ""


def parse_date(value):
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def dec(value):
    try:
        cleaned = str(value or "").strip().replace(",", "")
        if not cleaned:
            raise InvalidOperation
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid number: {value}") from exc


def convert_quantity(quantity, unit):
    unit_upper = (unit or "").strip().upper()
    if unit_upper in {"L", "LTR", "LITER", "LITRE"}:
        return quantity, "L"
    if unit_upper in {"GAL", "GALLON"}:
        return quantity * Decimal("3.78541"), "L"
    if unit_upper in {"KG", "KGS"}:
        return quantity, "kg"
    if unit_upper in {"TON", "TONNE", "T"}:
        return quantity * Decimal("1000"), "kg"
    if unit_upper in {"KWH"}:
        return quantity, "kWh"
    if unit_upper in {"KM", "KMS"}:
        return quantity, "km"
    if unit_upper in {"MI", "MILE", "MILES"}:
        return quantity * Decimal("1.60934"), "km"
    if unit_upper in {"EA", "EACH"}:
        return quantity, "each"
    if unit_upper in {"ROOM_NIGHT", "NIGHT", "NIGHTS"}:
        return quantity, "room_night"
    return quantity, unit or "unknown"


def find_facility(org, code):
    if not code:
        return None
    return Facility.objects.filter(organization=org, code=code.strip()).first()


def flag_if(condition, message, flags):
    if condition:
        flags.append(message)


def create_activity(org, batch, source_record, payload):
    activity = EmissionActivity.objects.create(
        organization=org,
        batch=batch,
        source_record=source_record,
        **payload,
    )
    AuditEvent.objects.create(
        organization=org,
        event_type="activity_created",
        object_type="EmissionActivity",
        object_id=str(activity.id),
        details={"source_batch": batch.id, "flags": activity.suspicious_flags},
    )
    return activity


def ingest_sap(org, batch, text):
    rows = read_csv(text)
    failed = 0
    for index, row in enumerate(rows, start=1):
        record = SourceRecord.objects.create(batch=batch, row_number=index, raw_payload=row)
        try:
            date = parse_date(normalize_key(row, "date"))
            facility = find_facility(org, normalize_key(row, "plant"))
            material = normalize_key(row, "material")
            material_type = normalize_key(row, "material_type").lower()
            quantity = dec(normalize_key(row, "quantity"))
            original_unit = normalize_key(row, "unit")
            normalized_quantity, normalized_unit = convert_quantity(quantity, original_unit)
            supplier = normalize_key(row, "supplier")
            flags = []
            flag_if(facility is None, "Plant code has no facility mapping", flags)
            flag_if(normalized_unit == "unknown", "Unrecognized unit", flags)

            if "fuel" in material_type or "diesel" in material.lower() or "lpg" in material.lower():
                scope = "Scope 1"
                category = "fuel_combustion"
                factor = FUEL_FACTORS["lpg"] if "lpg" in material.lower() else FUEL_FACTORS["diesel"]
            else:
                scope = "Scope 3"
                category = "purchased_goods"
                factor = Decimal("12.50") if normalized_unit == "each" else Decimal("1.90")
                flag_if(normalized_unit == "each", "Procurement row uses item count; spend or mass would be better", flags)

            kg_co2e = normalized_quantity * factor
            create_activity(
                org,
                batch,
                record,
                {
                    "facility": facility,
                    "scope": scope,
                    "category": category,
                    "activity_date": date,
                    "supplier": supplier,
                    "description": material,
                    "original_quantity": quantity,
                    "original_unit": original_unit,
                    "normalized_quantity": normalized_quantity,
                    "normalized_unit": normalized_unit,
                    "emission_factor": factor,
                    "kg_co2e": kg_co2e,
                    "suspicious_flags": flags,
                },
            )
        except Exception as exc:
            failed += 1
            record.status = "failed"
            record.error = str(exc)
            record.save(update_fields=["status", "error"])
    return len(rows), failed


def ingest_utility(org, batch, text):
    rows = read_csv(text)
    failed = 0
    for index, row in enumerate(rows, start=1):
        record = SourceRecord.objects.create(batch=batch, row_number=index, raw_payload=row)
        try:
            period_start = parse_date(row.get("period_start"))
            period_end = parse_date(row.get("period_end"))
            quantity = dec(row.get("kwh"))
            facility = find_facility(org, row.get("facility_code"))
            flags = []
            flag_if(facility is None, "Meter/facility code has no mapping", flags)
            flag_if((period_end - period_start).days > 35, "Billing period is longer than expected", flags)
            factor = Decimal("0.716")
            create_activity(
                org,
                batch,
                record,
                {
                    "facility": facility,
                    "scope": "Scope 2",
                    "category": "purchased_electricity",
                    "activity_date": period_end,
                    "period_start": period_start,
                    "period_end": period_end,
                    "supplier": row.get("account_number", ""),
                    "description": f"Electricity bill {row.get('meter_number', '')} - {row.get('tariff', '')}",
                    "original_quantity": quantity,
                    "original_unit": "kWh",
                    "normalized_quantity": quantity,
                    "normalized_unit": "kWh",
                    "emission_factor": factor,
                    "kg_co2e": quantity * factor,
                    "suspicious_flags": flags,
                },
            )
        except Exception as exc:
            failed += 1
            record.status = "failed"
            record.error = str(exc)
            record.save(update_fields=["status", "error"])
    return len(rows), failed


def ingest_travel(org, batch, text):
    rows = read_csv(text)
    failed = 0
    for index, row in enumerate(rows, start=1):
        record = SourceRecord.objects.create(batch=batch, row_number=index, raw_payload=row)
        try:
            category = (row.get("category") or "").strip().lower()
            date = parse_date(row.get("travel_date"))
            flags = []
            supplier = row.get("vendor") or ""
            if category == "flight":
                if row.get("distance", "").strip():
                    quantity = dec(row.get("distance"))
                    unit = row.get("distance_unit") or "km"
                    normalized_quantity, normalized_unit = convert_quantity(quantity, unit)
                else:
                    route = ((row.get("origin") or "").strip(), (row.get("destination") or "").strip())
                    normalized_quantity = AIRPORT_DISTANCE_KM.get(route)
                    if normalized_quantity is None:
                        raise ValueError("Flight distance missing and airport pair is unknown")
                    normalized_unit = "km"
                    quantity = normalized_quantity
                    unit = "derived_km"
                    flags.append("Distance derived from airport lookup")
                factor = Decimal("0.158")
                description = f"Flight {row.get('origin')} to {row.get('destination')}"
                normalized_category = "business_travel_flight"
            elif category == "hotel":
                quantity = dec(row.get("nights"))
                normalized_quantity, normalized_unit = convert_quantity(quantity, "nights")
                unit = "nights"
                factor = Decimal("22.00")
                description = f"Hotel stay in {row.get('origin')}"
                normalized_category = "business_travel_hotel"
            elif category == "ground":
                quantity = dec(row.get("distance"))
                unit = row.get("distance_unit") or "km"
                normalized_quantity, normalized_unit = convert_quantity(quantity, unit)
                factor = Decimal("0.192")
                description = f"Ground transport {row.get('origin')} to {row.get('destination')}"
                normalized_category = "business_travel_ground"
            else:
                raise ValueError(f"Unsupported travel category: {category}")
            create_activity(
                org,
                batch,
                record,
                {
                    "facility": None,
                    "scope": "Scope 3",
                    "category": normalized_category,
                    "activity_date": date,
                    "supplier": supplier,
                    "description": description,
                    "original_quantity": quantity,
                    "original_unit": unit,
                    "normalized_quantity": normalized_quantity,
                    "normalized_unit": normalized_unit,
                    "emission_factor": factor,
                    "kg_co2e": normalized_quantity * factor,
                    "suspicious_flags": flags,
                },
            )
        except Exception as exc:
            failed += 1
            record.status = "failed"
            record.error = str(exc)
            record.save(update_fields=["status", "error"])
    return len(rows), failed


INGESTERS = {
    "sap": ingest_sap,
    "utility": ingest_utility,
    "travel": ingest_travel,
}
