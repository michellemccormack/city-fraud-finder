from __future__ import annotations
from typing import Dict, List
from sqlalchemy import select, func
from db.models import Entity, Payment
from scoring.modules import payment_volume_score, payments_per_capacity_score, multi_entity_address_score, missing_basics_score

def compute_scores(session, city_key: str) -> int:
    ents = session.execute(select(Entity).where(Entity.city_key == city_key)).scalars().all()

    addr_counts: Dict[str, int] = {}
    rows = session.execute(
        select(Entity.normalized_address, func.count(Entity.id))
        .where(Entity.city_key == city_key)
        .group_by(Entity.normalized_address)
    ).all()
    for a, c in rows:
        if a:
            addr_counts[a] = int(c)

    updated = 0
    for e in ents:
        pays = session.execute(select(Payment).where(Payment.entity_id == e.id)).scalars().all()
        total = sum(p.amount for p in pays)

        pts = 0.0
        notes: List[str] = []

        r1 = payment_volume_score(total); pts += r1.points; notes += r1.notes
        if e.entity_type == "childcare":
            r2 = payments_per_capacity_score(total, e.license_capacity); pts += r2.points; notes += r2.notes

        if e.normalized_address:
            r3 = multi_entity_address_score(addr_counts.get(e.normalized_address, 1)); pts += r3.points; notes += r3.notes

        missing_id = (e.entity_type == "health" and not e.npi) or (e.entity_type == "childcare" and not e.license_id)
        r4 = missing_basics_score(missing_address=not bool(e.address), missing_id=missing_id)
        pts += r4.points; notes += r4.notes

        e.score = float(pts)
        e.score_notes = "; ".join(notes)
        updated += 1

    session.commit()
    return updated
