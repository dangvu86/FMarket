# FMarket Data Scraper
## What This Project Does
FMarket Data Scraper is a web automation tool that scrapes Vietnamese mutual fund NAV (Net Asset Value) data from FMarket and syncs it to Google Sheets. It eliminates manual data entry by automating the entire collection and storage process.
**Main Purpose:** Automatically extract fund performance data without manual work
**Workflow:**
1. User clicks "Get Data" button in Streamlit UI
2. Playwright logs into FMarket website  
3. JavaScript extracts fund table data
4. Pandas processes and transforms the data
5. gspread syncs to Google Sheets
6. Results displayed and CSV provided for download
**Business Value:** Dragon Capital automates fund monitoring for analysis and reporting.
---
## Key Technologies and Frameworks
### Web Application Framework
- **Streamlit** - Creates interactive Python web applications
  - UI components: buttons, spinners, data tables
  - Real-time user interactions
  - Results and error message display
### Browser Automation
- **Playwright** (sync API) - Automates web browser interactions
  - Headless Chromium for server execution
  - Login and form filling on FMarket
  - Page load completion waiting
  - JavaScript execution for data extraction
  - Subprocess execution for resource isolation
### Data Processing
- **Pandas** - Data manipulation and analysis
  - Raw array to DataFrame conversion
  - String parsing (names, values, dates)
  - Type conversion (float, datetime)
  - Date arithmetic and formatting
  - CSV export
### Google Cloud Integration
- **gspread** - Google Sheets API client
  - Read existing sheet data
  - Update specific rows
  - Append new rows
- **google-auth** - OAuth2 authentication
  - Service account credentials
### Standard Libraries
- subprocess - Process execution
- json - JSON parsing
- datetime - Date/time operations
---
## High-Level Architecture
### Component Interaction
Streamlit UI -> [Get Data] -> Playwright -> FMarket -> Data Extraction -> Pandas Processing -> gspread Google Sheets -> Display Results
### Data Processing Flow
**Phase 1: Web Scraping** (lines 13-43)
- Playwright runs in subprocess
- Logs into FMarket
- Waits for network idle
- Clicks fund filter
- Executes JavaScript to extract table
- Returns JSON array
**Phase 2: Data Transformation** (lines 52-88)
- Extract fund name from column 0
- Parse NAV and date from column 2
- Remove commas from NAV, convert to float
- Format dates as DD/MM/YYYY
- Handle year adjustment for edge cases
- Calculate NAV date as report date minus 1 day
**Phase 3: Google Sheets Sync** (lines 99-155)
- Read existing sheet data
- Create dedup dictionary: (Fund, Date NAV) -> Row Index
- Update existing records or append new ones
- Track operation counts
**Phase 4: Display & Export** (lines 157-158)
- Show processed data in table
- Display sync results
- Generate CSV with UTF-8 BOM
- Provide download button
---
## Important Commands
### Installation
pip install streamlit pandas gspread google-auth-oauthlib google-auth-httplib2 playwright
playwright install chromium
### Running
streamlit run app.py
Access at: http://localhost:8501
---
## Configuration Files
### .env File
**Path:** D:\OneDrive - DRAGON CAPITAL\Claude\test\.env
Contains credentials (currently UNUSED - hardcoded in app.py):
- FIIN_USERNAME=amiresearch@dragoncapital.com
- FIIN_PASSWORD=FiinProX@123
- FMARKET_EMAIL=dangvu@dragoncapital.com
- FMARKET_PASS=
**Note:** Should refactor to use environment variables instead of hardcoding.
### .streamlit/secrets.toml
**Path:** D:\OneDrive - DRAGON CAPITAL\Claude\test\.streamlit\secrets.toml
Google service account JSON:
- type: service_account
- project_id: dangvu-n8n
- private_key: RSA private key
- client_email: dc-324@dangvu-n8n.iam.gserviceaccount.com
Loaded via st.secrets["gcp_service_account"] in app.py line 102
**Security:** Never commit to version control
### .claude/settings.local.json
Claude tool configuration for allowed commands.
---
## Data Flow & External Integrations
### FMarket Website
- **URL:** https://fmarket.vn/trade/auth/login
- **Authentication:** Email + Password
- **Data Source:** HTML table #table-products
- **Process:** Login -> Filter -> Extract via JavaScript -> Return JSON
### Google Sheets API
- **Service:** Google Sheets Cloud
- **Auth:** OAuth2 service account
- **Spreadsheet:** https://docs.google.com/spreadsheets/d/19H1Tvyy1Of36PIqonFM2OQGYBFjhDHHSxGWPMlb1RBc
- **Operations:** Read, Update rows, Append rows
- **Schema:** Date report | Date NAV | Fund | NAV
- **Dedup Key:** (Fund, Date NAV)
### Data Transformation
- Input: Raw HTML table
- Process: Parse strings, convert types, date arithmetic
- Output: Structured DataFrame
---
## Architecture Patterns
### Separation of Concerns
- UI: Streamlit
- Scraping: Playwright subprocess
- Processing: Pandas
- Integration: gspread
### Error Handling
- Try-catch around Google Sheets (lines 100-155)
- User-friendly error messages
- Graceful empty data fallback
### Data Validation
- Non-empty DataFrame check
- Existing data verification
- Operation tracking
### Efficiency
- Subprocess isolation
- O(1) dedup lookup
- Single batch sheet read
- Headless browser mode
---
## Key Developer Notes
1. **Credentials Hardcoded** (lines 22-23)
   - Should use environment variables
   - os.environ.get("FMARKET_EMAIL")
2. **Year Adjustment** (lines 73-78)
   - December dates in January: subtract 1 year
   - Handles year-end edge case
3. **NAV Date** (line 81)
   - Report date minus 1 day
   - Previous trading day assumption
4. **Deduplication** (line 128-129)
   - Key: (Fund, Date NAV)
   - Updates existing, appends new
5. **CSV Export** (line 157)
   - UTF-8 BOM encoding
   - Excel/Windows compatibility
6. **Browser** (line 18)
   - Headless=True
   - Server deployment ready
7. **Wait** (line 26)
   - wait_for_load_state("networkidle")
   - Full page load assurance
---
## Project Files
- app.py: Main application (161 lines)
- .env: Credentials
- .streamlit/secrets.toml: Google auth
- .claude/settings.local.json: Tool config
- CLAUDE.md: This documentation
---
## Summary
Automates Vietnamese fund data collection using Streamlit, Playwright, Pandas, and gspread. Demonstrates good architecture with separation of concerns. Main improvement: move credentials to environment variables.
