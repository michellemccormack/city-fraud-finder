from __future__ import annotations
import csv
from typing import Dict, Any, Iterable

class CSVSeedConnector:
    def fetch(self, city_key: str, cfg: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        filepath = cfg["filepath"]
        mapping = cfg["mapping"]
        source = cfg.get("source_name", "csv_seed")

        out = []
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = {"source": source, "raw": row}
                for norm_field, col in mapping.items():
                    rec[norm_field] = row.get(col)
                out.append(rec)
        return out
