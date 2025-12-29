# Entity Validation System

## Overview

The validation system checks the legitimacy of entities through multiple digital signals without requiring physical visits. All results are stored as `EvidenceItems` with confidence scores, and red flags contribute to anomaly scoring.

## Current Validation Checks

### ✅ Implemented (Free/Open Source)

1. **Address Geocoding** (`address_geocode`)
   - Uses OpenStreetMap Nominatim API (free, rate-limited)
   - Verifies addresses resolve to real locations
   - Confidence: 0.9 if valid, 0.3 if invalid

2. **Phone Format Validation** (`phone_format`)
   - Validates US phone number format (10 digits)
   - Confidence: 0.8 if valid format, 0.2 if invalid

3. **Website Existence** (`website_exists`)
   - Checks DNS resolution
   - Tests HTTP accessibility
   - Confidence: 0.85 if accessible, 0.2 if not

4. **Missing Digital Presence** (`missing_digital_presence`)
   - Flags entities with no website or phone number
   - Red flag indicator
   - Confidence: 0.7

5. **License ID Presence** (`has_license_id`)
   - Checks if regulated entity has license ID
   - Confidence: 0.6 if present

## How to Use

1. **Run Validation on an Entity:**
   - Click an entity in the list to view details
   - Click "🔍 Validate Entity" button
   - Results are stored as evidence items

2. **View Validation Results:**
   - Validation score (0-100) with color coding:
     - Green (≥70): Looks legitimate
     - Orange (50-69): Some concerns
     - Red (<50): Multiple red flags
   - Red flags are listed prominently
   - Individual check results shown with ✅/❌/⏸ icons

3. **Re-run Validation:**
   - Click "🔄 Re-run Validation" to refresh checks
   - New results stored with timestamp

## Future Enhancements (Not Yet Implemented)

### Free/Low-Cost Options

1. **Google Business Profile Check**
   - Search for business listing
   - Requires Google Places API key (paid, but reasonable rates)
   - Signals: Business hours, reviews, verified status

2. **Social Media Presence**
   - Facebook Business Page lookup
   - LinkedIn company profile
   - Twitter/X business account
   - Free via public APIs/web scraping (with rate limits)

3. **Domain WHOIS Lookup**
   - Check domain registration date
   - Registrant information
   - Free via WHOIS APIs (rate-limited)

4. **Business Registration (Secretary of State)**
   - MA Secretary of State business lookup
   - Free public search (would need web scraping)
   - Validates business is registered

5. **Property Records**
   - Check property ownership at address
   - Free via city assessor websites (requires scraping)
   - Verify business owns/leases the property

6. **Review Sites**
   - Google Reviews count
   - Yelp presence
   - Better Business Bureau rating
   - Free via public APIs/scraping

### Paid API Options (Higher Quality)

1. **Phone Number Validation**
   - Twilio Lookup API (~$0.005 per lookup)
   - Validates number is active/portable
   - Carrier information

2. **Address Validation**
   - SmartyStreets API (~$0.004 per validation)
   - USPS address verification
   - Residential vs commercial classification

3. **Business Data APIs**
   - Clearbit (~$0.10 per company lookup)
   - ZoomInfo (enterprise pricing)
   - Full company profiles, employees, revenue

4. **Email Domain Validation**
   - Check if email domain exists and accepts mail
   - Free via SMTP check or paid APIs

## Scoring Integration

Validation red flags can be integrated into the anomaly scoring system:

- Low validation score (<50) → Increase anomaly score
- Missing digital presence → Flag for investigation
- Failed address geocoding → Major red flag
- No website + no phone → Suspicious for businesses receiving funding

## Implementation Notes

- All validation results stored as `EvidenceItem` with `evidence_type="validation"`
- Results include JSON with check details and red flags
- Validation score calculated from weighted check results
- Can be re-run anytime to refresh results
- Non-blocking: Failures don't break the system

## Privacy & Ethics

- All checks use publicly available information
- No personal data collection
- Rate limits respected (free APIs)
- Results are evidence, not accusations
- Human review required for flagged entities

