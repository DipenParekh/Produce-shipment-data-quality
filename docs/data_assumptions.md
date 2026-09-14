# Sample data assumptions

- Fictional, synthetic data; no company records are used.
- Fixed random seed: 42. No external packages required.
- Shipment dates span June 1 through August 29, 2026.
- Quantities are whole kilograms.
- Each shipment contains one product and at most one final receipt.
- A missing receipt means pending at the demonstration snapshot.
- A valid short receipt is a reconciliation exception, not bad data.
- Ten deliberate error injections are defined in generate_data.py.
- Rejected parent shipments can also invalidate linked receipts.
- Every rerun regenerates the same files and replaces manual edits.
