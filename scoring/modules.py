from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class ScoreResult:
    points: float
    notes: List[str]

def payment_volume_score(total: float) -> ScoreResult:
    pts, notes = 0.0, []
    if total >= 250_000:
        pts += 1.5; notes.append(f"High public $ volume: ${total:,.0f}")
    if total >= 1_000_000:
        pts += 2.0; notes.append("Very high public $ volume")
    if total >= 5_000_000:
        pts += 1.0; notes.append("Extreme public $ volume")
    return ScoreResult(pts, notes)

def payments_per_capacity_score(total: float, capacity):
    if not capacity or capacity <= 0:
        return ScoreResult(0.0, [])
    per = total / capacity
    pts, notes = 0.0, []
    if per >= 20_000:
        pts += 1.5; notes.append(f"High $ per licensed capacity: ${per:,.0f}/slot")
    if per >= 40_000:
        pts += 1.0; notes.append("Very high $ per capacity")
    return ScoreResult(pts, notes)

def multi_entity_address_score(n: int) -> ScoreResult:
    pts, notes = 0.0, []
    if n >= 3:
        pts += 1.0; notes.append(f"{n} entities share the same address")
    if n >= 6:
        pts += 1.0; notes.append("Large cluster at same address")
    return ScoreResult(pts, notes)

def missing_basics_score(missing_address: bool, missing_id: bool) -> ScoreResult:
    pts, notes = 0.0, []
    if missing_address:
        pts += 0.5; notes.append("Missing address")
    if missing_id:
        pts += 0.5; notes.append("Missing key identifier")
    return ScoreResult(pts, notes)
