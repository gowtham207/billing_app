"""Compare the API catalog with the generated OpenAPI paths."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402

CATALOG = ROOT / "backend" / "catalog" / "crm_billing_inventory_api_catalog.csv"


def variants(path: str) -> set[str]:
    trimmed = path.rstrip("/") or "/"
    return {path, trimmed, trimmed + "/"}


def main() -> int:
    spec = app.openapi()["paths"]
    missing = []
    with CATALOG.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            method = row["Method"].lower()
            path = row["Endpoint"]
            matched = next((item for item in variants(path) if item in spec and method in spec[item]), None)
            if matched is None:
                missing.append(f"{row['Method']} {path}")
    print(f"catalog rows checked against {len(spec)} paths")
    if missing:
        print("missing:")
        print("\n".join(missing))
        return 1
    print("every catalog endpoint is present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
