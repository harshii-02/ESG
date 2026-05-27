# Sources Researched

## SAP Fuel And Procurement

Format researched: SAP ALV/report flat exports and CSV extracts from SAP modules such as MM/FI, plus common SAP realities such as plant codes, material numbers, German labels, and inconsistent units.

What I learned:

- Exports often reflect local configuration, so headers are not stable.
- Plant codes require a lookup table.
- Dates may appear as `YYYYMMDD`, `DD.MM.YYYY`, or localized text.
- Units can be SAP-style abbreviations such as `L`, `GAL`, `KG`, or local-language variants.

Sample data shape:

- `Buchungsdatum`, `Werk`, `Material`, `Menge`, `ME`, `Belegart`
- Mix of diesel fuel and procurement items
- One unknown plant to demonstrate suspicious flagging

What would break in production:

- Custom material classifications
- Currency conversion
- Multiple company codes
- IDoc/OData structures instead of flat exports

## Utility Electricity

Format researched: utility portal billing CSVs and account/meter exports.

What I learned:

- Billing periods do not always align to calendar months.
- Meter/account numbers are the stable facility linkage.
- kWh and demand charges are often separate.
- Tariff/rate class matters for review even if not used in the first emission calculation.

Sample data shape:

- `account_number`, `meter_number`, `period_start`, `period_end`, `kwh`, `demand_kw`, `tariff`
- Includes a cross-month billing period and a missing meter mapping case.

What would break in production:

- PDF-only utilities
- Interval data with thousands of rows per meter
- Net metering and renewable tariffs
- Market-based Scope 2 claims

## Corporate Travel

Format researched: Concur/Navan-style travel and expense exports with transaction category, itinerary fields, and merchant data.

What I learned:

- Travel rows vary heavily by category.
- Flights may have airport codes without distance.
- Hotels use room-night logic rather than distance.
- Ground transport may have spend but no distance.

Sample data shape:

- `trip_id`, `category`, `travel_date`, `origin`, `destination`, `distance`, `distance_unit`, `nights`, `vendor`
- Includes flights, hotel, and ground transport.

What would break in production:

- Multi-leg trips
- Missing airport codes
- Cabin class handling
- Reconciliation between booking platform and expense platform

