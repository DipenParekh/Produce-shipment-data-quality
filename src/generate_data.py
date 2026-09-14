import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
DATA.mkdir(parents=True, exist_ok=True)
rng = random.Random(42)

def write_csv(name, rows):
    with (DATA / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}: {len(rows)} records")

products = [
    {"product_id": "P001", "product_name": "Tomatoes", "unit": "kg"},
    {"product_id": "P002", "product_name": "Bell Peppers", "unit": "kg"},
    {"product_id": "P003", "product_name": "Cucumbers", "unit": "kg"},
    {"product_id": "P004", "product_name": "Strawberries", "unit": "kg"},
    {"product_id": "P005", "product_name": "Lettuce", "unit": "kg"},
]

shipments = []
receipts = []

for number in range(1, 501):
    shipped_date = date(2026, 6, 1) + timedelta(days=rng.randrange(90))
    quantity = rng.randrange(100, 1001)
    shipment_id = f"S{number:04d}"

    shipments.append({
        "shipment_id": shipment_id,
        "product_id": rng.choice(products)["product_id"],
        "shipment_date": shipped_date.isoformat(),
        "shipped_kg": quantity,
    })

    # Last 20 shipments have no receipt: pending as of the demo snapshot.
    if number <= 480:
        received = quantity - 10 if number % 25 == 0 else quantity
        receipts.append({
            "receipt_id": f"R{number:04d}",
            "shipment_id": shipment_id,
            "receipt_date": (shipped_date + timedelta(days=2)).isoformat(),
            "received_kg": received,
        })

# Inject known data-quality errors, leaving most records valid.
shipments[9]["product_id"] = "P999"       # Unknown product
shipments[19]["shipped_kg"] = -50         # Negative quantity
shipments[29]["shipment_id"] = ""        # Missing shipment ID
shipments[39]["shipment_date"] = "invalid-date"
shipments.append(dict(shipments[49]))    # Duplicate shipment ID

receipts[59]["shipment_id"] = "S9999"    # Unknown shipment
receipts[69]["received_kg"] = -10        # Negative quantity
receipts[79]["receipt_date"] = "2026-01-01"  # Before dispatch
receipts[89]["receipt_id"] = ""          # Missing receipt ID
receipts.append(dict(receipts[99]))      # Duplicate receipt ID

write_csv("products.csv", products)
write_csv("shipments.csv", shipments)
write_csv("receipts.csv", receipts)

docs = ROOT / "docs"
docs.mkdir(parents=True, exist_ok=True)
(docs / "data_assumptions.md").write_text(
    "# Sample data assumptions\n\n"
    "- Fictional, synthetic data; no company records are used.\n"
    "- Fixed random seed: 42. No external packages required.\n"
    "- Shipment dates span June 1 through August 29, 2026.\n"
    "- Quantities are whole kilograms.\n"
    "- Each shipment contains one product and at most one final receipt.\n"
    "- A missing receipt means pending at the demonstration snapshot.\n"
    "- A valid short receipt is a reconciliation exception, not bad data.\n"
    "- Ten deliberate error injections are defined in generate_data.py.\n"
    "- Rejected parent shipments can also invalidate linked receipts.\n"
    "- Every rerun regenerates the same files and replaces manual edits.\n",
    encoding="utf-8",
)

print("Synthetic data ready:", DATA)
