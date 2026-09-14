import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

FILES = {
    "products.csv": ("product_id", None),
    "shipments.csv": ("shipment_id", "shipped_kg"),
    "receipts.csv": ("receipt_id", "received_kg"),
}

profiles = {}

for filename, (id_column, quantity_column) in FILES.items():
    with (SOURCE / filename).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames
        rows = list(reader)

    missing = {
        column: sum(
            not (row.get(column) or "").strip()
            for row in rows
        )
        for column in columns
    }

    ids = Counter(
        row[id_column].strip()
        for row in rows
        if (row.get(id_column) or "").strip()
    )

    profile = {
        "record_count": len(rows),
        "missing_values_by_column": missing,
        "duplicate_ids": {
            key: count for key, count in ids.items()
            if count > 1
        },
        "extra_duplicate_rows": sum(
            count - 1 for count in ids.values() if count > 1
        ),
    }

    if quantity_column:
        quantities = []
        invalid_count = 0

        for row in rows:
            try:
                value = Decimal(row[quantity_column])
                if not value.is_finite():
                    raise ValueError("Non-finite quantity")
                quantities.append(value)
            except (InvalidOperation, ValueError, TypeError):
                invalid_count += 1

        profile["quantity_profile"] = {
            "column": quantity_column,
            "minimum": str(min(quantities)) if quantities else None,
            "maximum": str(max(quantities)) if quantities else None,
            "negative_count": sum(q < 0 for q in quantities),
            "invalid_numeric_count": invalid_count,
        }

    profiles[filename] = profile

    print(f"\n{filename}: {len(rows)} records")
    print("Missing values:",
          {key: value for key, value in missing.items() if value})
    print("Duplicate IDs:", profile["duplicate_ids"])

    if quantity_column:
        print("Quantity profile:", profile["quantity_profile"])

output = REPORTS / "source_profile.json"
output.write_text(
    json.dumps(profiles, indent=2),
    encoding="utf-8",
)
print("\nProfile saved:", output)
