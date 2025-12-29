# Where to Find Boston/MA Payment Data

## Top Sources to Check:

### 1. **Massachusetts Comptroller - Vendor Payments**
- Website: https://www.macomptroller.org/
- Look for: "Checkbook", "Vendor Payments", "Spending" section
- Download: CSV files with vendor names and amounts
- Search for: childcare provider names or filter by department (EEC)

### 2. **Boston Open Data Portal**
- Website: https://data.boston.gov/ (or search "Boston open data")
- Look for: "Vendor Payments", "Contracts", "Financial Data"
- Download: CSV format available

### 3. **Massachusetts EEC (Department of Early Education)**
- Website: https://www.mass.gov/orgs/department-of-early-education-and-care
- Look for: "Grants", "Contracts", "Public Records"
- Programs: C3 Grants, Capital Grants, Provider Payments
- May need to request via public records

### 4. **USAspending.gov** (Federal grants)
- Website: https://www.usaspending.gov/
- Download: CSV exports available
- Search: "Boston", "childcare", "early education"
- Note: System already configured but API failing - can download CSV manually

## What You Need in the CSV:

Essential columns:
- **Vendor/Payee Name** (to match entities)
- **Amount** (payment amount)
- **Date/Year** (when paid)

Nice to have:
- Address
- Program/Department
- Contract number

## How to Use:

1. Download CSV from any source above
2. Click "Upload CSV" in the UI
3. Map columns (name → vendor name, amount → amount)
4. Set entity type to "other" (system will match to childcare entities)
5. Click "Ingest CSV"
6. Click "Recompute scores" to see anomalies

## Quick Start:

**Best bet**: Start with Massachusetts Comptroller website - usually has the most comprehensive state spending data in CSV format.
