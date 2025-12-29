from __future__ import annotations
import os, json, re
from datetime import date
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Body
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, delete
import io
import csv

from db.models import Base, make_engine, make_session, Entity, Payment, EvidenceItem, Alias, Identifier, ReviewMatch
from core.utils import normalize_name, normalize_address, safe_int, safe_float, best_effort_zip
from scoring.engine import compute_scores
from services.matching import propose_match
from services.records_requests import build_request
from services.entity_networks import find_name_based_clusters
from connectors.csv_seed import CSVSeedConnector

DB_URL = os.getenv("DB_URL", "sqlite:///./city_fraud_finder.db")
ENGINE = make_engine(DB_URL)
Base.metadata.create_all(ENGINE)

def load_city_config() -> Dict[str, Any]:
    with open("city_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

CITY_CONFIG = load_city_config()

app = FastAPI(title="City Fraud Finder", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/meta/cities")
def meta_cities():
    return {"cities": [{"city_key": k, "display_name": v.get("display_name", k)} for k, v in CITY_CONFIG.items()]}

def get_city_cfg(city_key: str) -> Dict[str, Any]:
    if city_key not in CITY_CONFIG:
        raise HTTPException(404, f"Unknown city_key: {city_key}")
    return CITY_CONFIG[city_key]

def add_identifier(session, entity_id: int, id_type: str, value: str, source: Optional[str]):
    value = str(value).strip()
    if not value:
        return
    exists = session.execute(
        select(Identifier).where(Identifier.entity_id==entity_id, Identifier.id_type==id_type, Identifier.value==value)
    ).scalar_one_or_none()
    if not exists:
        session.add(Identifier(entity_id=entity_id, id_type=id_type, value=value, source=source))

def add_alias(session, entity_id: int, alias: str, source: Optional[str]):
    alias = alias.strip()
    if not alias:
        return
    norm = normalize_name(alias)
    exists = session.execute(select(Alias).where(Alias.entity_id==entity_id, Alias.normalized_alias==norm)).scalar_one_or_none()
    if not exists:
        session.add(Alias(entity_id=entity_id, alias=alias, normalized_alias=norm, source=source))

def upsert_entity(session, city_key: str, entity_type: str, name: str, address: Optional[str], city: Optional[str], state: Optional[str], zip_code: Optional[str], **kwargs) -> Entity:
    nname = normalize_name(name)
    naddr = normalize_address(address) if address else None
    zip5 = best_effort_zip(zip_code)

    ent = session.execute(
        select(Entity).where(
            Entity.city_key == city_key,
            Entity.entity_type == entity_type,
            Entity.normalized_name == nname,
            Entity.normalized_address == naddr
        )
    ).scalar_one_or_none()

    if not ent:
        ent = Entity(
            city_key=city_key, entity_type=entity_type,
            name=name, normalized_name=nname,
            address=address, normalized_address=naddr,
            city=city, state=state, zip=zip5
        )
        session.add(ent)
        session.flush()
    else:
        ent.name = ent.name or name
        ent.address = ent.address or address
        ent.normalized_address = ent.normalized_address or naddr
        ent.city = ent.city or city
        ent.state = ent.state or state
        ent.zip = ent.zip or zip5

    if kwargs.get("license_status"):
        ent.license_status = kwargs["license_status"]
    if kwargs.get("license_capacity") is not None:
        ent.license_capacity = kwargs["license_capacity"]
    if kwargs.get("license_id"):
        ent.license_id = kwargs["license_id"]
    if kwargs.get("npi"):
        ent.npi = str(kwargs["npi"]).strip()

    if ent.license_id:
        add_identifier(session, ent.id, "LICENSE_ID", ent.license_id, kwargs.get("id_source"))
    if ent.npi:
        add_identifier(session, ent.id, "NPI", ent.npi, kwargs.get("id_source"))

    return ent

@app.post("/ingest/configured")
def ingest_configured(city_key: str = "boston_ma"):
    try:
        city_cfg = get_city_cfg(city_key)
        connectors = city_cfg.get("connectors", {})

        session = make_session(ENGINE)
        added_entities = added_payments = added_evidence = review_queue = 0

        for cname, cfg in connectors.items():
            ctype = cfg.get("type")
            
            try:
                if ctype == "csv_seed":
                    rows = CSVSeedConnector().fetch(city_key, cfg)
                    etype = cfg.get("entity_type", "other")
                    for r in rows:
                        if not r.get("name"):
                            continue
                        ent = upsert_entity(
                            session, city_key, etype,
                            r.get("name"),
                            r.get("address"), r.get("city"), r.get("state"), r.get("zip"),
                            license_status=r.get("license_status"),
                            license_capacity=safe_int(r.get("license_capacity")),
                            license_id=r.get("license_id"),
                            npi=r.get("npi"),
                            id_source=cname
                        )
                        added_entities += 1
                        session.add(EvidenceItem(
                            entity_id=ent.id,
                            evidence_type="license" if etype=="childcare" else "directory",
                            source=cname,
                            confidence=0.85,
                            title=f"Ingested from {cname}",
                            extracted_json=json.dumps({k: r.get(k) for k in ["license_status","license_capacity","license_id","npi"] if r.get(k) is not None})[:200000],
                            raw_json=json.dumps(r.get("raw", {}))[:200000]
                        ))
                        added_evidence += 1

                if ctype == "usaspending":
                    try:
                        from connectors.usaspending import USAspendingConnector
                        rows = USAspendingConnector().fetch(city_key, cfg)
                        for r in rows:
                            cand_name = r.get("name")
                            if not cand_name:
                                continue
                            ent_id, conf, reason = propose_match(session, city_key, entity_type="", candidate_name=cand_name, candidate_address=None)
                            if not ent_id:
                                ent = upsert_entity(session, city_key, "other", cand_name, None, None, None, None)
                                add_alias(session, ent.id, cand_name, source="usaspending")
                                ent_id = ent.id
                                added_entities += 1

                            session.add(Payment(
                                entity_id=ent_id,
                                source="usaspending",
                                data_source="usa-spending",
                                category="Payer",
                                fiscal_year=r.get("fiscal_year"),
                                amount=safe_float(r.get("amount")),
                                payer=r.get("payer"),
                                program=r.get("program"),
                                match_confidence=float(conf),
                                match_reason=reason,
                                raw_json=json.dumps(r.get("raw", {}))[:200000]
                            ))
                            added_payments += 1
                            session.add(EvidenceItem(
                                entity_id=ent_id,
                                evidence_type="payment",
                                source="usaspending",
                                confidence=float(conf),
                                title=r.get("title"),
                                url=r.get("url"),
                                extracted_json=json.dumps({k: r.get(k) for k in ["amount","fiscal_year","payer","program"]})[:200000],
                                raw_json=json.dumps(r.get("raw", {}))[:200000]
                            ))
                            added_evidence += 1

                            if conf < 0.85:
                                session.add(ReviewMatch(
                                    city_key=city_key,
                                    candidate_name=cand_name,
                                    candidate_address=None,
                                    candidate_source="usaspending",
                                    entity_id=ent_id,
                                    confidence=float(conf),
                                    reason=reason,
                                    resolved=False
                                ))
                                review_queue += 1
                    except Exception as usaspending_error:
                        # USAspending failed but don't break the whole ingestion
                        print(f"Warning: USAspending connector failed: {usaspending_error}")
                        continue
            except Exception as e:
                # Log error but continue with other connectors
                import traceback
                print(f"Error processing connector {cname}: {e}")
                print(traceback.format_exc())
                continue

        session.commit()
        return {"city_key": city_key, "added_entities_estimate": added_entities, "added_payments": added_payments, "added_evidence": added_evidence, "review_queue_added": review_queue}
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/score/recompute")
def score_recompute(city_key: str = "boston_ma"):
    session = make_session(ENGINE)
    updated = compute_scores(session, city_key)
    return {"city_key": city_key, "updated": updated}

@app.get("/entities")
def list_entities(city_key: str = "boston_ma", entity_type: Optional[str] = None, payment_tag: Optional[str] = None, data_source: Optional[str] = None, limit: int = 200):
    session = make_session(ENGINE)
    q = select(Entity).where(Entity.city_key == city_key)
    if entity_type:
        q = q.where(Entity.entity_type == entity_type)
    
    # If filtering by payment tag or data_source, only include entities that have matching payments
    if payment_tag or data_source:
        payment_filter = select(Payment.entity_id).distinct()
        if payment_tag:
            payment_filter = payment_filter.where(Payment.tag == payment_tag)
        if data_source:
            payment_filter = payment_filter.where(Payment.data_source == data_source)
        # Join with entities to filter by city_key
        payment_filter = payment_filter.join(Entity).where(Entity.city_key == city_key)
        entity_ids = session.execute(payment_filter).scalars().all()
        if entity_ids:
            q = q.where(Entity.id.in_(entity_ids))
        else:
            # No matching payments, return empty list
            return []
    
    q = q.order_by(Entity.score.desc()).limit(limit)
    ents = session.execute(q).scalars().all()
    out = []
    for e in ents:
        payments = e.payments
        if payment_tag:
            payments = [p for p in payments if p.tag == payment_tag]
        if data_source:
            payments = [p for p in payments if p.data_source == data_source]
        total = sum(p.amount for p in payments)
        out.append({
            "id": e.id,
            "name": e.name,
            "type": e.entity_type,
            "address": e.address,
            "score": float(e.score or 0.0),
            "notes": e.score_notes or "",
            "total_public_amount": float(total)
        })
    return out

@app.get("/entities/{entity_id}")
def entity_detail(entity_id: int):
    session = make_session(ENGINE)
    e = session.execute(select(Entity).where(Entity.id == entity_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Not found")
    pays = session.execute(select(Payment).where(Payment.entity_id == entity_id).order_by(Payment.amount.desc())).scalars().all()
    evs = session.execute(select(EvidenceItem).where(EvidenceItem.entity_id == entity_id).order_by(EvidenceItem.created_at.desc())).scalars().all()
    total = sum(p.amount for p in pays)
    
    return {
        "id": e.id,
        "name": e.name,
        "type": e.entity_type,
        "address": e.address,
        "city": e.city,
        "state": e.state,
        "zip": e.zip,
        "license_status": e.license_status,
        "license_capacity": e.license_capacity,
        "license_id": e.license_id,
        "npi": e.npi,
        "score": float(e.score or 0.0),
        "score_notes": e.score_notes or "",
        "total_public_amount": float(total),
        "payments": [{"source": p.source, "fiscal_year": p.fiscal_year, "amount": float(p.amount or 0.0), "payer": p.payer, "program": p.program} for p in pays],
        "evidence": [{"evidence_type": ev.evidence_type, "source": ev.source, "confidence": float(ev.confidence or 0.0), "title": ev.title, "url": ev.url} for ev in evs]
    }

@app.get("/records-request/{entity_id}")
def records_request(entity_id: int, city_key: str = "boston_ma", years_back: int = 2):
    session = make_session(ENGINE)
    city_cfg = get_city_cfg(city_key)
    e = session.execute(select(Entity).where(Entity.id == entity_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(404, "Not found")
    als = session.execute(select(Alias).where(Alias.entity_id == entity_id)).scalars().all()
    alias_str = ", ".join(a.alias for a in als) if als else ""
    end = date.today().isoformat()
    start = date(date.today().year - years_back, 1, 1).isoformat()
    return {"text": build_request(city_cfg.get("display_name", city_key), e.name, alias_str, start, end)}

@app.get("/entity-networks")
def entity_networks(city_key: str = "boston_ma", entity_type: Optional[str] = None):
    """Find clusters of connected entities (same names, addresses, etc.)"""
    session = make_session(ENGINE)
    clusters = find_name_based_clusters(session, city_key, entity_type)
    return {"clusters": clusters, "cluster_count": len(clusters)}

@app.get("/payments/categories")
def list_payment_categories(city_key: str = "boston_ma"):
    """List all data sources and tags used in payments"""
    session = make_session(ENGINE)
    from sqlalchemy import distinct, func
    data_sources = session.execute(
        select(distinct(Payment.data_source))
        .join(Entity).where(Entity.city_key == city_key)
        .where(Payment.data_source.isnot(None), Payment.data_source != "")
    ).scalars().all()
    tags = session.execute(
        select(distinct(Payment.tag))
        .join(Entity).where(Entity.city_key == city_key)
        .where(Payment.tag.isnot(None), Payment.tag != "")
    ).scalars().all()
    return {"data_sources": [d for d in data_sources if d], "tags": [t for t in tags if t]}

@app.get("/payments/tags")
def list_payment_tags(city_key: str = "boston_ma"):
    """List all tags used in payments (deprecated, use /payments/categories)"""
    return list_payment_categories(city_key)

class TagPaymentsRequest(BaseModel):
    payment_ids: str
    tag: str
    city_key: str = "boston_ma"

@app.post("/payments/tag")
def tag_payments(req: TagPaymentsRequest):
    """Tag multiple payments (comma-separated IDs)"""
    session = make_session(ENGINE)
    ids = [int(i.strip()) for i in req.payment_ids.split(",") if i.strip()]
    if not ids:
        raise HTTPException(400, "No payment IDs provided")
    
    payments = session.execute(
        select(Payment).where(Payment.id.in_(ids))
        .join(Entity).where(Entity.city_key == req.city_key)
    ).scalars().all()
    
    updated = 0
    for p in payments:
        p.tag = req.tag.strip() if req.tag.strip() else None
        updated += 1
    
    session.commit()
    return {"updated": updated, "tag": req.tag}

@app.get("/payments/recent")
def recent_payments(city_key: str = "boston_ma", limit: int = 20, category: Optional[str] = None):
    """Get recent payments for tagging"""
    session = make_session(ENGINE)
    q = select(Payment).join(Entity).where(Entity.city_key == city_key)
    if category:
        q = q.where(Payment.category == category)
    q = q.order_by(Payment.created_at.desc()).limit(limit)
    payments = session.execute(q).scalars().all()
    
    return {
        "payments": [
            {
                "id": p.id,
                "entity_id": p.entity_id,
                "entity_name": p.entity.name if p.entity else None,
                "amount": float(p.amount or 0),
                "source": p.source,
                "category": p.category,
                "tag": p.tag,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in payments
        ]
    }

@app.get("/payments/by-source")
def payments_by_source(city_key: str = "boston_ma"):
    """Get all sources (payments and evidence items) grouped by source"""
    session = make_session(ENGINE)
    from sqlalchemy import func
    
    # Get payment sources
    payment_results = session.execute(
        select(Payment.source, func.count(Payment.id).label("count"), func.min(Payment.created_at).label("first_created"))
        .join(Entity).where(Entity.city_key == city_key)
        .group_by(Payment.source)
    ).all()
    
    # Get evidence item sources (entity uploads)
    evidence_results = session.execute(
        select(EvidenceItem.source, func.count(EvidenceItem.id).label("count"), func.min(EvidenceItem.created_at).label("first_created"))
        .join(Entity).where(Entity.city_key == city_key)
        .where(EvidenceItem.source.like("uploaded_%"))
        .group_by(EvidenceItem.source)
    ).all()
    
    # Combine both types
    all_sources = {}
    
    for r in payment_results:
        source = r.source
        if source not in all_sources:
            all_sources[source] = {
                "source": source,
                "count": 0,
                "first_created": r.first_created
            }
        all_sources[source]["count"] += r.count
        if r.first_created and (not all_sources[source]["first_created"] or r.first_created < all_sources[source]["first_created"]):
            all_sources[source]["first_created"] = r.first_created
    
    for r in evidence_results:
        source = r.source
        if source not in all_sources:
            all_sources[source] = {
                "source": source,
                "count": 0,
                "first_created": r.first_created
            }
        all_sources[source]["count"] += r.count
        if r.first_created and (not all_sources[source]["first_created"] or r.first_created < all_sources[source]["first_created"]):
            all_sources[source]["first_created"] = r.first_created
    
    # Sort by first created date
    sources_list = sorted(all_sources.values(), key=lambda x: x["first_created"] if x["first_created"] else "")
    
    return {
        "sources": [
            {
                "source": s["source"],
                "count": s["count"],
                "first_created": s["first_created"].isoformat() if s["first_created"] else None
            }
            for s in sources_list
        ]
    }

@app.post("/payments/set-tag")
def set_payment_tag(source: str = Form(...), tag: str = Form(...), city_key: str = Form("boston_ma")):
    """Set tag for all payments from a source"""
    session = make_session(ENGINE)
    
    # Update payments
    payments = session.execute(
        select(Payment)
        .join(Entity).where(Entity.city_key == city_key)
        .where(Payment.source == source)
    ).scalars().all()
    
    updated = 0
    tag_value = tag.strip() if tag.strip() else None
    for p in payments:
        p.tag = tag_value
        updated += 1
    
    session.commit()
    return {"updated": updated, "source": source, "tag": tag}

@app.post("/payments/set-category")
def set_payment_category(source: str = Form(...), category: str = Form(...), city_key: str = Form("boston_ma")):
    """Set category for all payments from a source"""
    session = make_session(ENGINE)
    payments = session.execute(
        select(Payment)
        .join(Entity).where(Entity.city_key == city_key)
        .where(Payment.source == source)
    ).scalars().all()
    
    updated = 0
    for p in payments:
        p.category = category
        updated += 1
    
    session.commit()
    return {"updated": updated, "source": source, "category": category}

@app.post("/cleanup/duplicate-payments")
def cleanup_duplicate_payments(source_pattern: str = "EEC", city_key: str = "boston_ma"):
    """Remove duplicate payments from a source (keeps earliest copy of each unique payment)"""
    session = make_session(ENGINE)
    
    # Find all payments matching source pattern, ordered by ID (earliest first)
    payments = session.execute(
        select(Payment).where(Payment.source.like(f"%{source_pattern}%"))
        .order_by(Payment.id.asc())
    ).scalars().all()
    
    # Group by entity_id, amount, fiscal_year to find duplicates
    # Keep first occurrence, delete rest
    seen = set()
    to_delete = []
    
    for p in payments:
        # Create key from entity, amount, and fiscal year
        key = (p.entity_id, round(float(p.amount or 0), 2), p.fiscal_year or "")
        if key in seen:
            to_delete.append(p.id)
        else:
            seen.add(key)
    
    # Delete duplicate payments
    deleted_payments = 0
    if to_delete:
        # Delete the duplicate payments
        result = session.execute(
            delete(Payment).where(Payment.id.in_(to_delete))
        )
        deleted_payments = result.rowcount if result.rowcount else len(to_delete)
        session.commit()
    
    return {"deleted": deleted_payments, "remaining": len(payments) - deleted_payments, "total_found": len(payments)}

@app.get("/review-queue")
def review_queue_list(city_key: str = "boston_ma", limit: int = 100):
    session = make_session(ENGINE)
    matches = session.execute(
        select(ReviewMatch)
        .where(ReviewMatch.city_key == city_key, ReviewMatch.resolved == False)
        .order_by(ReviewMatch.confidence.asc(), ReviewMatch.created_at.desc())
        .limit(limit)
    ).scalars().all()
    
    out = []
    for m in matches:
        entity = session.execute(select(Entity).where(Entity.id == m.entity_id)).scalar_one_or_none() if m.entity_id else None
        out.append({
            "id": m.id,
            "candidate_name": m.candidate_name,
            "candidate_address": m.candidate_address,
            "candidate_source": m.candidate_source,
            "confidence": float(m.confidence or 0.0),
            "reason": m.reason or "",
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "entity_id": m.entity_id,
            "entity_name": entity.name if entity else None,
            "entity_address": entity.address if entity else None,
            "entity_type": entity.entity_type if entity else None
        })
    return {"matches": out}

@app.post("/review-queue/{match_id}/approve")
def review_queue_approve(match_id: int):
    session = make_session(ENGINE)
    match = session.execute(select(ReviewMatch).where(ReviewMatch.id == match_id)).scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Review match not found")
    if match.resolved:
        raise HTTPException(400, "Match already resolved")
    
    # Approve means keeping the match as-is (entity_id is correct)
    match.resolved = True
    match.resolution = "approved"
    session.commit()
    return {"status": "approved", "match_id": match_id, "entity_id": match.entity_id}

@app.post("/review-queue/{match_id}/reject")
def review_queue_reject(match_id: int, create_new_entity: bool = False):
    session = make_session(ENGINE)
    match = session.execute(select(ReviewMatch).where(ReviewMatch.id == match_id)).scalar_one_or_none()
    if not match:
        raise HTTPException(404, "Review match not found")
    if match.resolved:
        raise HTTPException(400, "Match already resolved")
    
    if create_new_entity and match.entity_id:
        # Create a new entity and move the payment/evidence to it
        # For now, just mark as rejected - full implementation would need to handle payment/evidence reassignment
        pass
    
    match.resolved = True
    match.resolution = "rejected"
    session.commit()
    return {"status": "rejected", "match_id": match_id}

@app.post("/upload/csv/preview")
async def upload_csv_preview(file: UploadFile = File(...)):
    """Preview CSV file and return column names"""
    try:
        contents = await file.read()
        # Handle BOM and encoding
        text = contents.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        columns = reader.fieldnames or []
        # Read first few rows for preview
        rows = []
        for i, row in enumerate(reader):
            if i >= 3:  # Preview first 3 data rows
                break
            rows.append(dict(row))
        return {"columns": list(columns), "preview_rows": rows, "row_count": sum(1 for _ in csv.DictReader(io.StringIO(text))) - 1}
    except Exception as e:
        raise HTTPException(400, f"Error reading CSV: {str(e)}")

@app.post("/upload/csv/ingest")
async def upload_csv_ingest(
    file: UploadFile = File(...),
    city_key: str = Form(...),
    entity_type: str = Form(...),
    name_column: str = Form(...),
    address_column: str = Form(default=""),
    city_column: str = Form(default=""),
    state_column: str = Form(default=""),
    zip_column: str = Form(default=""),
    license_status_column: str = Form(default=""),
    license_capacity_column: str = Form(default=""),
    license_id_column: str = Form(default=""),
    npi_column: str = Form(default="")
):
    """Upload and ingest a CSV file with column mappings"""
    try:
        contents = await file.read()
        text = contents.decode('utf-8-sig')
        
        # Build mapping dict from form data
        mapping = {}
        if name_column:
            mapping["name"] = name_column
        if address_column:
            mapping["address"] = address_column
        if city_column:
            mapping["city"] = city_column
        if state_column:
            mapping["state"] = state_column
        if zip_column:
            mapping["zip"] = zip_column
        if license_status_column:
            mapping["license_status"] = license_status_column
        if license_capacity_column:
            mapping["license_capacity"] = license_capacity_column
        if license_id_column:
            mapping["license_id"] = license_id_column
        if npi_column:
            mapping["npi"] = npi_column
        
        # Create a config dict that CSVSeedConnector can use
        cfg = {
            "filepath": None,  # We'll read from memory instead
            "mapping": mapping,
            "entity_type": entity_type,
            "source_name": f"uploaded_{file.filename}"
        }
        
        # Read CSV into memory structure
        reader = csv.DictReader(io.StringIO(text))
        rows = []
        for row in reader:
            rec = {"source": cfg["source_name"], "raw": row}
            for norm_field, col in mapping.items():
                rec[norm_field] = row.get(col)
            rows.append(rec)
        
        # Process rows like CSVSeedConnector does
        session = make_session(ENGINE)
        added_entities = added_evidence = 0
        
        for r in rows:
            if not r.get("name"):
                continue
            ent = upsert_entity(
                session, city_key, entity_type,
                r.get("name"),
                r.get("address"), r.get("city"), r.get("state"), r.get("zip"),
                license_status=r.get("license_status"),
                license_capacity=safe_int(r.get("license_capacity")),
                license_id=r.get("license_id"),
                npi=r.get("npi"),
                id_source=cfg["source_name"]
            )
            added_entities += 1
            session.add(EvidenceItem(
                entity_id=ent.id,
                evidence_type="license" if entity_type=="childcare" else "directory",
                source=cfg["source_name"],
                category="Payees",
                confidence=0.85,
                title=f"Uploaded from {file.filename}",
                extracted_json=json.dumps({k: r.get(k) for k in ["license_status","license_capacity","license_id","npi"] if r.get(k) is not None})[:200000],
                raw_json=json.dumps(r.get("raw", {}))[:200000]
            ))
            added_evidence += 1
        
        session.commit()
        return {
            "status": "success",
            "added_entities": added_entities,
            "added_evidence": added_evidence,
            "filename": file.filename
        }
    except Exception as e:
        import traceback
        raise HTTPException(500, f"Error processing CSV: {str(e)}\n{traceback.format_exc()}")

@app.post("/upload/payments-csv/ingest")
async def upload_payments_csv_ingest(
    file: UploadFile = File(...),
    city_key: str = Form(...),
    vendor_column: str = Form(...),
    amount_column: str = Form(...),
    date_column: str = Form(default=""),
    fiscal_year_column: str = Form(default=""),
    program_column: str = Form(default=""),
    payer_column: str = Form(default=""),
    tag: str = Form(default=""),
    data_source: str = Form(default="")
):
    """Upload a CSV with vendor payments - matches vendors to entities and creates Payment records"""
    try:
        contents = await file.read()
        text = contents.decode('utf-8-sig')
        
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        
        session = make_session(ENGINE)
        added_payments = added_evidence = 0
        
        for row in rows:
            vendor_name = row.get(vendor_column, "").strip()
            if not vendor_name:
                continue
            
            amount = safe_float(row.get(amount_column, 0))
            if amount <= 0:
                continue
            
            # Try to match vendor to existing entity
            ent_id, conf, reason = propose_match(session, city_key, entity_type="", candidate_name=vendor_name, candidate_address=None)
            
            if not ent_id:
                # Determine entity type from tag
                entity_type = "other"  # default
                if tag:
                    tag_lower = tag.strip().lower()
                    if tag_lower in ["childcare"]:
                        entity_type = "childcare"
                    elif tag_lower in ["healthcare", "autism/mental", "autism", "mental"]:
                        entity_type = "health"
                    elif tag_lower == "education":
                        entity_type = "other"  # Keep as other unless we add education type
                
                # Create new entity for unmatched vendor
                ent = upsert_entity(session, city_key, entity_type, vendor_name, None, None, None, None)
                add_alias(session, ent.id, vendor_name, source=f"uploaded_payments_{file.filename}")
                ent_id = ent.id
                conf = 0.5  # Low confidence for new entity
                reason = f"New entity created from payment data (type: {entity_type})"
            
            # Extract fiscal year or date
            fiscal_year = None
            if fiscal_year_column and row.get(fiscal_year_column):
                fiscal_year = str(row.get(fiscal_year_column)).strip()
            elif date_column and row.get(date_column):
                date_val = str(row.get(date_column)).strip()
                # Try to extract year
                year_match = re.search(r'20\d{2}', date_val)
                if year_match:
                    fiscal_year = year_match.group(0)
            
            if not fiscal_year:
                fiscal_year = str(date.today().year)
            
            payer = row.get(payer_column, "").strip() if payer_column else "State of Massachusetts"
            program = row.get(program_column, "").strip() if program_column else "EEC"
            
            # Create payment record
            session.add(Payment(
                entity_id=ent_id,
                source=f"uploaded_{file.filename}",
                data_source=data_source.strip() if data_source else None,
                category="Payer",
                tag=tag.strip() if tag else None,
                fiscal_year=fiscal_year,
                amount=amount,
                payer=payer or "State of Massachusetts",
                program=program or "EEC",
                match_confidence=float(conf),
                match_reason=reason,
                raw_json=json.dumps(row)[:200000]
            ))
            added_payments += 1
            
            # Add evidence item
            session.add(EvidenceItem(
                entity_id=ent_id,
                evidence_type="payment",
                source=f"uploaded_{file.filename}",
                confidence=float(conf),
                title=f"Payment: ${amount:,.2f}",
                extracted_json=json.dumps({"amount": amount, "fiscal_year": fiscal_year, "payer": payer, "program": program})[:200000],
                raw_json=json.dumps(row)[:200000]
            ))
            added_evidence += 1
        
        session.commit()
        return {
            "status": "success",
            "added_payments": added_payments,
            "added_evidence": added_evidence,
            "filename": file.filename
        }
    except Exception as e:
        import traceback
        raise HTTPException(500, f"Error processing payments CSV: {str(e)}\n{traceback.format_exc()}")
