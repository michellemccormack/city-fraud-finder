# Actual Roadmap Status - Confirmed

## ✅ **COMPLETED**

### Phase 0: Core System

✅ **MVP scaffold** 
- **Status:** ✅ **DONE**
- FastAPI backend ✅
- SQLite database ✅
- Static HTML/JS UI ✅
- Data ingestion ✅
- Scoring system ✅
- Records request generation ✅

✅ **Evidence-first core**
- **Status:** ✅ **DONE**
- EvidenceItem model with provenance ✅
- Identifiers table ✅
- Aliases table ✅
- All facts stored with source/confidence ✅

✅ **Matching system**
- **Status:** ✅ **DONE**
- Fuzzy matching with confidence scores ✅
- Explainable reasons stored ✅
- `services/matching.py` implemented ✅

✅ **Review queue**
- **Status:** ✅ **DONE** (Roadmap says "Next" but it's complete)
- ReviewMatch table ✅
- `/review-queue` endpoint ✅
- `/review-queue/{id}/approve` endpoint ✅
- `/review-queue/{id}/reject` endpoint ✅
- Full UI with approve/reject buttons ✅
- Badge showing count in header ✅

### Phase 1: Upload Tools

✅ **Browser CSV upload**
- **Status:** ✅ **DONE** (Roadmap says "Planned" but it's complete)
- `/upload/csv/preview` endpoint ✅
- `/upload/csv/ingest` endpoint (Entity Data) ✅
- `/upload/payments-csv/ingest` endpoint (Payment Data) ✅
- Full UI with file upload ✅
- Column mapping interface ✅
- Auto-detection of common column names ✅
- Supports both Entity Data and Payment Data ✅

❌ **Portal adapters**
- **Status:** ❌ **NOT STARTED**
- Manual CSV download/upload works ✅
- No automated API connectors ❌

### Phase 2: Network Analysis

✅ **Entity networks**
- **Status:** ✅ **DONE** (Roadmap says "Planned" but it's complete)
- `/entity-networks` endpoint ✅
- Name-based clustering ✅
- UI panel showing connected entities ✅
- `services/entity_networks.py` implemented ✅

❌ **FOIA pipeline**
- **Status:** ❌ **NOT COMPLETE**
- ✅ Records request generation (`/records-request/{id}`)
- ❌ Request tracking (database table, CRUD endpoints)
- ❌ Response import functionality
- **Note:** Started building but removed per user request

---

## 📊 **Summary**

**Completed:** 6/8 roadmap items (75%)
- Phase 0: 4/4 (100%) ✅
- Phase 1: 1/2 (50%)
- Phase 2: 1/2 (50%)

**Plus Additional Features (not on original roadmap):**
- ✅ Tagging system (tags for payments/entities)
- ✅ Data source tracking (ma-comptroller, etc.)
- ✅ Smart entity type detection (from payment tags)
- ✅ Duplicate payment cleanup
- ✅ Source management UI
- ✅ Filtering by tag, data source, entity type

---

## 🎯 **What's Actually Working**

The system is **fully functional** for:
1. ✅ Uploading entity data (CSV)
2. ✅ Uploading payment data (CSV)
3. ✅ Matching payments to entities (fuzzy matching)
4. ✅ Scoring entities for anomalies
5. ✅ Review queue for low-confidence matches
6. ✅ Entity networks/clusters
7. ✅ Records request generation
8. ✅ Filtering and tagging

**Missing:**
- ❌ Automated portal connectors (manual CSV upload works fine)
- ❌ FOIA lifecycle tracking (request generation works, tracking doesn't)

---

## 📝 **Notes**

The roadmap status column is **outdated**. The actual implementation is ahead of what the roadmap says:
- Review queue: Says "Next" but is ✅ Done
- Browser CSV upload: Says "Planned" but is ✅ Done  
- Entity networks: Says "Planned" but is ✅ Done

The system is **production-ready for MVP** with all core functionality working.

