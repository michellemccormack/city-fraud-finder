# Testing Checklist - City Fraud Finder

## ✅ Features to Test

### 1. **Core Entity Management**
- [ ] **View Entities List**
  - Open http://127.0.0.1:8000/
  - Verify entities load and display in table
  - Check entity count shows at top
  - Test sorting by clicking column headers (Score, Name, Type, Total $, Notes)

- [ ] **Filter Entities**
  - Use "Type" dropdown (All, Childcare, Health, Other)
  - Use "Data Source" dropdown filter
  - Use "Tag" dropdown filter (e.g., "childcare", "healthcare", "autism/mental")
  - Use search box to filter by name/address
  - Verify filters work together (multiple filters applied)

- [ ] **View Entity Details**
  - Click on an entity row
  - Verify detail panel shows:
    - Entity name, type, address
    - Total public funding amount
    - Score and score notes
    - Payments list
    - Evidence items
    - Records request draft

### 2. **Data Ingestion**

- [ ] **Ingest Configured Sources**
  - Click "Ingest configured sources" button
  - Verify CSV seed files load (if configured in city_config.json)
  - Check for errors in browser console (F12)
  - Verify entities appear after ingestion

- [ ] **Upload Entity Data (CSV)**
  - Click "Upload CSV" button
  - Select "Entity Data" radio button
  - Upload a CSV with entity information (name, address, license info)
  - Use preview to verify column detection
  - Map columns (should auto-detect common names)
  - Select entity type (childcare, health, other)
  - Click "Ingest CSV"
  - Verify new entities appear in list

- [ ] **Upload Payment Data (CSV)**
  - Click "Upload CSV" button
  - Select "Payment Data" radio button
  - Upload a CSV with vendor names and payment amounts
  - Map columns (vendor → Vendor, amount → Amount, etc.)
  - Select data source (e.g., "ma-comptroller")
  - Select tag (e.g., "childcare", "healthcare", "autism/mental", "education")
  - Click "Ingest CSV"
  - Verify payments matched to existing entities or new entities created
  - Check that entity types are automatically set based on tag

### 3. **Tagging & Source Management**

- [ ] **Manage Sources**
  - Click "Manage Sources" button
  - Verify all uploaded sources appear (both payment uploads and entity uploads)
  - For each source, enter/update a tag
  - Click tag button to save
  - Verify tag updates across all records from that source

- [ ] **Filter by Tag**
  - Use "Tag" dropdown in main interface
  - Select a tag (e.g., "childcare")
  - Verify entities filtered to show only those with payments tagged with that tag

- [ ] **Filter by Data Source**
  - Use "Data Source" dropdown
  - Select a source (e.g., "ma-comptroller")
  - Verify entities filtered correctly

### 4. **Scoring System**

- [ ] **Recompute Scores**
  - Click "Recompute scores" button
  - Wait for completion message
  - Verify entities have scores displayed
  - Check score notes for explanation

- [ ] **Score Accuracy**
  - Review high-scoring entities
  - Verify score notes explain anomalies
  - Check that entities with:
    - High total funding → higher scores
    - Missing license IDs → flags in notes
    - Address clustering → noted in score

### 5. **Entity Validation** ⭐ NEW

- [ ] **Run Validation**
  - Click on an entity to view details
  - Click "🔍 Validate Entity" button
  - Wait for validation to complete
  - Verify validation score appears (0-100)
  - Check red flags displayed (if any)
  - Review individual check results:
    - ✅ Address geocoding
    - ✅ Phone format (if phone exists)
    - ✅ Website existence (if website exists)
    - Missing digital presence flags

- [ ] **Validation Results**
  - Verify validation score color coding:
    - Green (≥70): Looks legitimate
    - Orange (50-69): Some concerns
    - Red (<50): Multiple red flags
  - Check that red flags are prominently displayed
  - Verify results are stored (reload page, validation should persist)

- [ ] **Re-run Validation**
  - Click "🔄 Re-run Validation" on an entity with existing validation
  - Verify new results stored with timestamp

### 6. **Review Queue**

- [ ] **View Review Queue**
  - Click "Review Queue" button (with count badge if items exist)
  - Verify low-confidence matches appear
  - Check match details show:
    - Candidate name and source
    - Matched entity (if any)
    - Confidence score
    - Matching reason

- [ ] **Approve Match**
  - In review queue, click "✓ Approve" on a match
  - Verify match removed from queue
  - Verify match is marked as approved

- [ ] **Reject Match**
  - In review queue, click "✗ Reject" on a match
  - Verify match removed from queue
  - Verify match is marked as rejected

### 7. **Entity Networks**

- [ ] **View Entity Networks**
  - Click "Entity Networks" button
  - Verify clusters appear (entities sharing names, addresses, etc.)
  - Check cluster details show connected entities
  - Verify you can click to view individual entities in clusters

### 8. **Records Requests**

- [ ] **Generate Records Request**
  - Click on an entity
  - Scroll to "Records request draft" section
  - Verify FOIA request text is generated
  - Check request includes:
    - Entity name
    - Known aliases
    - Date range
    - Request for payments, contracts, vendor IDs

### 9. **Data Cleanup**

- [ ] **Cleanup Duplicate Payments**
  - Click "Cleanup Duplicates" button
  - Verify duplicates removed (if any exist)
  - Check message shows how many duplicates were removed
  - Verify payment totals update correctly

### 10. **UI/UX**

- [ ] **General Navigation**
  - Verify all buttons are clickable
  - Check panels open/close correctly
  - Verify modals/popups work
  - Test responsive design (resize browser)

- [ ] **Error Handling**
  - Try uploading invalid CSV
  - Try uploading without required columns
  - Verify helpful error messages appear
  - Check browser console (F12) for JavaScript errors

- [ ] **Performance**
  - Test with large entity list (100+ entities)
  - Verify filtering is fast
  - Check entity detail loads quickly
  - Verify validation doesn't hang

## 🔍 Quick Smoke Test (5 minutes)

If you're short on time, test these critical paths:

1. ✅ **View entities** - Page loads, entities display
2. ✅ **Upload payment CSV** - Can upload and ingest payments
3. ✅ **Filter by tag** - Tag filtering works
4. ✅ **View entity detail** - Details load correctly
5. ✅ **Run validation** - Validation completes and shows results
6. ✅ **Recompute scores** - Scoring works

## 📊 Expected Behavior

- **Entities**: Should show name, address, type, score, total funding
- **Scores**: Range from 0-100, higher = more anomalous
- **Validation**: Scores 0-100, green/yellow/red color coding
- **Filters**: Should work independently and together
- **Tags**: Should persist across page refreshes
- **Payments**: Should match to existing entities or create new ones

## 🐛 Known Issues to Watch For

- Port 8000 conflicts (use `bash start_server.sh`)
- CSV column mapping issues (check auto-detection works)
- Validation API timeouts (should fail gracefully)
- Large datasets slow loading (expected, but shouldn't hang)

## 📝 Notes

- All data persists in SQLite database (`city_fraud_finder.db`)
- Validation results stored as EvidenceItems
- Scores are computed based on funding, capacity, missing identifiers
- Entity types auto-detected from payment tags during upload

