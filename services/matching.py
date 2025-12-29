from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy import select
from db.models import Entity
from core.utils import normalize_name, normalize_address, similarity

def propose_match(session, city_key: str, entity_type: str, candidate_name: str, candidate_address: Optional[str]) -> Tuple[Optional[int], float, str]:
    nname = normalize_name(candidate_name)
    naddr = normalize_address(candidate_address) if candidate_address else ""

    q = select(Entity).where(Entity.city_key == city_key)
    if entity_type:
        q = q.where(Entity.entity_type == entity_type)
    ents = session.execute(q).scalars().all()

    best_id, best_score, best_reason = None, 0.0, ""
    for e in ents:
        name_sim = similarity(nname, e.normalized_name or "")
        addr_sim = similarity(naddr, e.normalized_address or "") if naddr and e.normalized_address else 0.0
        score = 0.75 * name_sim + 0.25 * addr_sim
        if naddr and not e.normalized_address:
            score = 0.85 * name_sim
        if score > best_score:
            best_score, best_id = score, e.id
            best_reason = f"name_sim={name_sim:.2f}, addr_sim={addr_sim:.2f}"

    if best_score < 0.72:
        return None, float(best_score), f"Low confidence ({best_score:.2f}) best={best_reason}"
    return best_id, float(best_score), best_reason
