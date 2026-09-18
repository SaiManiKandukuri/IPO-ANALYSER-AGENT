# Directive: Scrape IPO Data

**Goal:** Extract current and upcoming Mainboard IPO data from Investorgain and update the analytical database and JSON payloads.

**Inputs:**
- API Base URL: `https://webnodejs.investorgain.com/cloud/v2/report/data-read/`
- Report IDs: `331` (GMP) and `333` (Subscription)
- Parameters: `1/{month}/{year}/{fy}/0/all`

**Tools / Scripts to Use:**
- `execution/ipo_scraper_json_db.py`

**Outputs:**
- `ipo_data.json` (Deliverable, sorted by Open Date then Close Date descending)
- `ipo_data.db` (Deliverable, SQLite tracking database)

**Rules & Edge Cases:**
1. **API Over HTML:** Always use the backend JSON API endpoints for data extraction to bypass front-end pagination and dynamic rendering limits.
2. **SME Filtering:** The API returns both Mainboard and SME IPOs. Unless explicitly requested otherwise, filter out all SME IPOs using the `~ipo_category1` or `~IPO_Category` fields.
3. **Data Integrity (NaN Handling):** When joining GMP and Subscription data, upcoming IPOs will have missing subscription figures resulting in Pandas `NaN` values. These must be safely mapped to `0.0` to avoid corrupting downstream calculations.
4. **Current GMP vs Max GMP:** The field `~max_gmp1` contains historical maximums. Live GMP must be explicitly parsed from the first `<b>` tag inside the `GMP` HTML string payload.
