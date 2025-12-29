from __future__ import annotations
import requests
from typing import Dict, Any, Iterable, List

class USAspendingConnector:
    BASE = "https://api.usaspending.gov"

    def fetch(self, city_key: str, cfg: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        recipients: List[str] = cfg.get("recipient_keywords", [])
        fiscal_years: List[int] = cfg.get("fiscal_years", [])
        limit = int(cfg.get("limit_per_query", 50))
        if not recipients:
            return []
        out = []
        for kw in recipients:
            url = f"{self.BASE}/api/v2/recipient/awards/"
            payload = {"recipient_search_text": [kw], "fy": fiscal_years, "page": 1, "limit": limit}
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            for row in data.get("results", []):
                out.append({
                    "source": "usaspending",
                    "evidence_type": "payment",
                    "name": row.get("recipient_name"),
                    "amount": float(row.get("total_obligation") or 0.0),
                    "fiscal_year": str(row.get("fy")) if row.get("fy") else None,
                    "payer": "US Federal",
                    "program": "federal_awards",
                    "raw": row,
                    "title": "USAspending awards summary",
                    "url": None
                })
        return out
