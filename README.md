# City Fraud Finder

Evidence-first anomaly lead finder.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

UI: http://127.0.0.1:8000/
Docs: http://127.0.0.1:8000/docs

## Boston workflow

1) Fill:
- data/seeds/boston_childcare_providers.csv
- data/seeds/boston_health_providers.csv

2) Click **Ingest configured sources**
3) Click **Recompute scores**
