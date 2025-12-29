# Quick Test Guide - What to Upload

## 🎯 Recommended Testing Strategy

### Option 1: Test with Existing Data First (5 minutes) ✅ RECOMMENDED

**Why:** Verify the system works before investing time in finding real data.

**Steps:**
1. **Upload Entity Data First:**
   - Use `test_upload.csv` (already in your project)
   - Or use `data/seeds/boston_childcare_providers.csv`
   - Click "Upload CSV" → "Entity Data"
   - Map columns → Ingest
   - This creates entities to match payments against

2. **Create a Simple Payment CSV:**
   - Create a file called `test_payments.csv` with these columns:
   ```csv
   Vendor Name,Amount,Fiscal Year,Program
   Sunshine Daycare,50000,2024,Childcare Subsidy
   Happy Kids Center,75000,2024,Childcare Subsidy
   Little Learners,30000,2024,Early Education Grant
   ```
   - Click "Upload CSV" → "Payment Data"
   - Select data source: "ma-comptroller" (or type a new one)
   - Select tag: "childcare"
   - Map Vendor → Vendor Name, Amount → Amount
   - Ingest
   - System should match payments to entities you created in step 1

3. **Test Features:**
   - View entities → Should show your test entities
   - Click entity → See payments attached
   - Filter by tag "childcare" → Should filter correctly
   - Run validation on an entity → Should work
   - Recompute scores → Entities should get scores

### Option 2: Use Real Data (20-30 minutes) 🎯 PRODUCTION TEST

**Why:** See how the system works with real-world data and catch edge cases.

**Best Source:** Massachusetts Comptroller website

1. **Go to:** https://www.macomptroller.org/
2. **Look for:** "Checkbook" or "Vendor Payments" section
3. **Download:** CSV with vendor payments
4. **Filter/Prepare:** 
   - Ideally, filter for childcare-related vendors
   - Or download a small sample (100-200 rows) to test
   - Save as CSV

**What You Need in the CSV:**
- ✅ **Vendor/Payee Name** (required) - e.g., "ABC Daycare Center"
- ✅ **Amount** (required) - e.g., "$50,000"
- ⭐ **Date/Year** (helpful) - for fiscal year tracking
- ⭐ **Program/Department** (nice to have) - e.g., "EEC", "Childcare"
- ⭐ **Address** (optional) - helps with matching

**Example Real CSV Columns:**
```csv
Vendor Name,Payment Amount,Fiscal Year,Department,Program
ABC Childcare Center,45000,2024,EEC,Subsidy Program
XYZ Daycare Inc,67000,2024,EEC,Grant Program
```

**Upload Process:**
1. Click "Upload CSV" → "Payment Data"
2. Upload your real CSV
3. Map columns:
   - Vendor Name → Vendor column
   - Payment Amount → Amount column
   - Fiscal Year → Fiscal Year column (if you have it)
   - Program → Program column (if you have it)
4. Select data source: "ma-comptroller" (or create new)
5. Select tag: "childcare" (or appropriate tag)
6. Click "Ingest CSV"
7. System will:
   - Try to match vendors to existing entities
   - Create new entities if no match found
   - Auto-assign entity type based on tag

## 📋 Minimum CSV Template

If you want to create a quick test file, here's the minimum needed:

**For Payment Data:**
```csv
Vendor,Amount
Daycare Center ABC,50000
Childcare Provider XYZ,75000
```

**For Entity Data:**
```csv
Name,Address,City,State,Zip
ABC Daycare,123 Main St,Boston,MA,02110
XYZ Childcare,456 Oak Ave,Boston,MA,02111
```

## 🚀 Recommended First Test Workflow

1. **Start Simple (2 minutes):**
   - Create `test_payments.csv` with 3-5 rows
   - Upload as Payment Data
   - Verify entities created/matched

2. **Test Core Features (3 minutes):**
   - View entities → Should show your test entities
   - Click entity → See payments
   - Filter by tag → Should work
   - Run validation → Should complete

3. **Then Try Real Data:**
   - Once you know it works, get real CSV from MA Comptroller
   - Upload larger dataset
   - Test with real vendor names

## 💡 Pro Tips

- **Start small:** Test with 5-10 rows first
- **Check matches:** After uploading, verify payments matched to correct entities
- **Use tags:** Tag everything so you can filter later
- **Save your CSVs:** Keep the files you upload for reference
- **Check browser console:** Press F12 if something doesn't work

## 🎯 What to Look For

After uploading, verify:
- ✅ Entities appear in the list
- ✅ Payments are attached to entities
- ✅ Tags work for filtering
- ✅ Scores are computed (click "Recompute scores")
- ✅ Validation runs without errors
- ✅ Entity networks find connections (if you have related entities)

## ⚠️ Common Issues

- **No matches:** If payments don't match, entities might not exist yet → upload entity data first
- **Column mapping:** Make sure vendor name column is mapped correctly
- **Large files:** Start with small files (< 100 rows) to test, then scale up

