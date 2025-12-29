# Troubleshooting Guide

## Quick Health Check

Before starting the server, run:
```bash
./check_health.py
```

This will catch common issues like:
- Missing files
- Import errors
- Port conflicts
- Python version issues

## Common Issues

### Port 8000 Already in Use
```bash
lsof -ti:8000 | xargs kill -9
# Or use the start script which handles this automatically
./start_server.sh
```

### Import Errors (SSL/Permissions)
The app now uses lazy imports for `requests` to avoid SSL permission errors. If you see import errors, check:
1. Virtual environment is activated: `source .venv/bin/activate`
2. Dependencies installed: `pip install -r requirements.txt`

### CSV Data Not Loading
1. Check CSV files have proper headers (no duplicates)
2. Check file paths in `city_config.json` match actual files
3. Run ingestion and check browser console for errors
4. Check server logs for Python errors

### Entities Not Showing
1. Make sure you clicked "Ingest configured sources"
2. Click "Recompute scores"
3. Click "Refresh"
4. Check browser console (F12) for API errors

## Starting the Server

Always use:
```bash
./start_server.sh
```

Or manually:
```bash
source .venv/bin/activate
python3 -m uvicorn app:app --reload
```

## Testing Endpoints

Check if server is running:
```bash
curl http://127.0.0.1:8000/meta/cities
```

Test ingestion:
```bash
curl -X POST "http://127.0.0.1:8000/ingest/configured?city_key=boston_ma"
```

List entities:
```bash
curl "http://127.0.0.1:8000/entities?city_key=boston_ma"
```

## Code Changes

- **Error handling**: Each connector now fails independently - CSV ingestion works even if USAspending fails
- **Lazy imports**: `requests` is only imported when needed to avoid SSL issues
- **Health check script**: Run before starting to catch issues early

