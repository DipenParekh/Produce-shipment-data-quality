import csv
import json
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pyodbc


ROOT = Path(__file__).resolve().parents[1]

SPECS = [
    (
        "products.csv",
        "product_id",
        ["product_id", "product_name", "unit"],
    ),
    (
        "shipments.csv",
        "shipment_id",
        ["shipment_id", "product_id", "shipment_date", "shipped_kg"],
    ),
    (
        "receipts.csv",
        "receipt_id",
        ["receipt_id", "shipment_id", "receipt_date", "received_kg"],
    ),
]

CONNECTION = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=ProduceDataQuality;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


def read_sources():
    sources = {}

    for filename, _, fields in SPECS:
        path = ROOT / "data" / "raw" / filename

        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != fields:
                raise ValueError(f"Unexpected CSV columns: {filename}")

            rows = list(reader)

            if any(None in row or None in row.values() for row in rows):
                raise ValueError(f"Malformed CSV row: {filename}")

            sources[filename] = rows

    return sources


def parse_date(value, field, issues):
    try:
        result = date.fromisoformat(value)

        if result.isoformat() != value:
            raise ValueError()

        return result

    except ValueError:
        issues.append(
            ("INVALID_DATE", f"{field}: expected YYYY-MM-DD")
        )
        return None


def parse_quantity(value, field, issues):
    try:
        result = Decimal(value)

        if not result.is_finite():
            raise ValueError()

        if result < 0:
            issues.append(
                ("NEGATIVE_QUANTITY", f"{field}: must be non-negative")
            )
            return None

        if result > Decimal("9999999999.99"):
            raise ValueError()

        if result != result.quantize(Decimal("0.01")):
            raise ValueError()

        return result

    except (InvalidOperation, ValueError):
        issues.append(
            ("INVALID_QUANTITY", f"{field}: invalid decimal quantity")
        )
        return None


def main():
    sources = read_sources()
    connection = pyodbc.connect(CONNECTION, timeout=10)
    run_id = None

    try:
        cursor = connection.cursor()

        # Suppress row-count messages from SQL statements.
        cursor.execute("SET NOCOUNT ON;")

        # Return the generated run ID directly from the INSERT.
        run_id = cursor.execute(
            "INSERT INTO dq.PipelineRun "
            "OUTPUT INSERTED.run_id "
            "DEFAULT VALUES;"
        ).fetchone()[0]

        connection.commit()

        accepted = 0
        rejected = 0
        valid_products = set()
        valid_shipments = {}

        # Rebuild the accepted snapshot within one transaction.
        # Raw records, validation issues and run history are retained.
        cursor.execute("DELETE FROM dq.Receipt;")
        cursor.execute("DELETE FROM dq.Shipment;")
        cursor.execute("DELETE FROM dq.Product;")

        for filename, id_field, fields in SPECS:
            rows = sources[filename]

            id_counts = Counter(
                row[id_field].strip()
                for row in rows
            )

            receipt_links = (
                Counter(
                    row["shipment_id"].strip()
                    for row in rows
                )
                if filename == "receipts.csv"
                else {}
            )

            for source_row, original in enumerate(rows, start=2):
                row = {
                    key: value.strip()
                    for key, value in original.items()
                }
                issues = []

                # Preserve the original values before validation.
                raw_id = cursor.execute(
                    "INSERT INTO dq.RawRecord "
                    "(run_id, source_file, source_row, payload) "
                    "OUTPUT INSERTED.raw_id "
                    "VALUES (?, ?, ?, ?);",
                    run_id,
                    filename,
                    source_row,
                    json.dumps(original),
                ).fetchone()[0]

                # Validate required fields and target column lengths.
                for field in fields:
                    if not row[field]:
                        issues.append(
                            ("MISSING_VALUE", f"{field}: required")
                        )

                    if field == "product_name":
                        limit = 100
                    elif field == "unit":
                        limit = 10
                    elif field.endswith("_id"):
                        limit = 20
                    else:
                        limit = None

                    if limit and len(row[field]) > limit:
                        issues.append(
                            (
                                "VALUE_TOO_LONG",
                                f"{field}: exceeds {limit} characters",
                            )
                        )

                # Reject every occurrence of a duplicated ID.
                if row[id_field] and id_counts[row[id_field]] > 1:
                    issues.append(
                        (
                            "DUPLICATE_ID",
                            f"{id_field}: {row[id_field]}",
                        )
                    )

                if filename == "products.csv":
                    if row["unit"] != "kg":
                        issues.append(
                            ("INVALID_UNIT", "Unit must be kg")
                        )

                elif filename == "shipments.csv":
                    event_date = parse_date(
                        row["shipment_date"],
                        "shipment_date",
                        issues,
                    )
                    quantity = parse_quantity(
                        row["shipped_kg"],
                        "shipped_kg",
                        issues,
                    )

                    if row["product_id"] not in valid_products:
                        issues.append(
                            (
                                "INVALID_PRODUCT",
                                "Product is missing or rejected",
                            )
                        )

                else:
                    event_date = parse_date(
                        row["receipt_date"],
                        "receipt_date",
                        issues,
                    )
                    quantity = parse_quantity(
                        row["received_kg"],
                        "received_kg",
                        issues,
                    )

                    shipment_id = row["shipment_id"]
                    parent = valid_shipments.get(shipment_id)

                    if (
                        shipment_id
                        and receipt_links[shipment_id] > 1
                    ):
                        issues.append(
                            (
                                "MULTIPLE_RECEIPTS",
                                "Only one final receipt per shipment",
                            )
                        )

                    if parent is None:
                        issues.append(
                            (
                                "INVALID_SHIPMENT",
                                "Shipment is missing or rejected",
                            )
                        )
                    else:
                        if (
                            event_date is not None
                            and event_date < parent["date"]
                        ):
                            issues.append(
                                (
                                    "DATE_SEQUENCE",
                                    "Receipt precedes shipment",
                                )
                            )

                        if (
                            quantity is not None
                            and quantity > parent["quantity"]
                        ):
                            issues.append(
                                (
                                    "OVER_RECEIPT",
                                    "Received quantity exceeds shipped quantity",
                                )
                            )

                if issues:
                    for code, description in issues:
                        cursor.execute(
                            "INSERT INTO dq.ValidationIssue "
                            "(raw_id, rule_code, issue_description) "
                            "VALUES (?, ?, ?);",
                            raw_id,
                            code,
                            description,
                        )

                    status = "REJECTED"
                    rejected += 1

                else:
                    if filename == "products.csv":
                        cursor.execute(
                            "INSERT INTO dq.Product "
                            "(product_id, product_name, unit, raw_id) "
                            "VALUES (?, ?, ?, ?);",
                            row["product_id"],
                            row["product_name"],
                            row["unit"],
                            raw_id,
                        )

                        valid_products.add(row["product_id"])

                    elif filename == "shipments.csv":
                        cursor.execute(
                            "INSERT INTO dq.Shipment "
                            "(shipment_id, product_id, shipment_date, "
                            "shipped_kg, raw_id) "
                            "VALUES (?, ?, ?, ?, ?);",
                            row["shipment_id"],
                            row["product_id"],
                            event_date,
                            quantity,
                            raw_id,
                        )

                        valid_shipments[row["shipment_id"]] = {
                            "date": event_date,
                            "quantity": quantity,
                        }

                    else:
                        cursor.execute(
                            "INSERT INTO dq.Receipt "
                            "(receipt_id, shipment_id, receipt_date, "
                            "received_kg, raw_id) "
                            "VALUES (?, ?, ?, ?, ?);",
                            row["receipt_id"],
                            row["shipment_id"],
                            event_date,
                            quantity,
                            raw_id,
                        )

                    status = "ACCEPTED"
                    accepted += 1

                cursor.execute(
                    "UPDATE dq.RawRecord "
                    "SET record_status = ? "
                    "WHERE raw_id = ?;",
                    status,
                    raw_id,
                )

        input_count = sum(
            len(rows)
            for rows in sources.values()
        )

        if input_count != accepted + rejected:
            raise RuntimeError("Record reconciliation failed")

        cursor.execute(
            "UPDATE dq.PipelineRun "
            "SET finished_at = SYSUTCDATETIME(), "
            "status = 'SUCCESS', "
            "input_count = ?, "
            "accepted_count = ?, "
            "rejected_count = ? "
            "WHERE run_id = ?;",
            input_count,
            accepted,
            rejected,
            run_id,
        )

        connection.commit()

        print(f"Run {run_id}: SUCCESS")
        print(
            f"Input: {input_count} | "
            f"Accepted: {accepted} | "
            f"Rejected: {rejected}"
        )
        print("Counts reconcile. Accepted snapshot committed.")

    except Exception as error:
        connection.rollback()

        if run_id is not None:
            try:
                connection.cursor().execute(
                    "UPDATE dq.PipelineRun "
                    "SET status = 'FAILED', "
                    "finished_at = SYSUTCDATETIME(), "
                    "error_message = ? "
                    "WHERE run_id = ?;",
                    str(error)[:2000],
                    run_id,
                )
                connection.commit()

            except Exception as log_error:
                print(f"Could not record failure status: {log_error}")

        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()