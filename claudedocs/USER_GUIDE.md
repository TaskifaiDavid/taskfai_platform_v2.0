# TaskifAI User Guide

**How to Use TaskifAI for Sales Analytics**

**Last Updated**: 2025-10-25
**Version**: 2.0
**Audience**: Analysts, Managers, End-Users

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Uploading Sales Data](#uploading-sales-data)
3. [Understanding Your Dashboard](#understanding-your-dashboard)
4. [Using AI Chat](#using-ai-chat)
5. [Advanced Analytics](#advanced-analytics)
6. [Customizing Dashboards](#customizing-dashboards)
7. [Exporting Reports](#exporting-reports)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing TaskifAI

**Your Company's URL**: `your-company.taskifai.com`

Example:
- BIBBI Parfum: `bibbi.taskifai.com`
- Demo Account: `demo.taskifai.com`

### First-Time Login

1. **Visit your company's TaskifAI URL**
   - Open browser (Chrome, Firefox, Safari, Edge)
   - Enter: `your-company.taskifai.com`

2. **Enter your credentials**
   - Email address (provided by your administrator)
   - Password (set during account creation)

3. **Enable Two-Factor Authentication** (Recommended)
   - Click "Enable 2FA" on first login
   - Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
   - Enter 6-digit code to verify
   - Save backup codes in safe place

4. **Dashboard loads automatically**
   - You'll see your personalized dashboard
   - KPI cards show latest statistics
   - Charts display recent trends

### Understanding Your Role

TaskifAI has two user roles:

| Role | Access Level | What You Can Do |
|------|--------------|-----------------|
| **Analyst** | Standard user | Upload files, view analytics, use AI chat, create dashboards |
| **Admin** | Full access | All analyst features + manage users, configure settings, view all uploads |

*Your role was assigned by your administrator*

---

## Uploading Sales Data

### Supported File Formats

TaskifAI automatically detects and processes these vendor formats:

- **Liberty** - Excel (.xlsx)
- **Galilu** - CSV or Excel
- **Selfridges** - Excel (.xls, .xlsx)
- **BoxNox** - CSV
- **Skins SA** - Excel (.xlsx)
- **Skins NL** - Excel (.xlsx)
- **CDLC** - Excel (.xlsx)
- **Aromateque** - Excel (.xlsx)
- **Other vendors** - Contact support to add new vendors

**Maximum file size**: 100MB per file

### Step-by-Step Upload Process

#### Step 1: Navigate to Uploads

1. Click **"Upload Data"** in the left sidebar
2. You'll see your upload history (past uploads, status, row counts)

#### Step 2: Prepare Your File

**Best Practices**:
- ✅ Use the original file from vendor (don't manually edit)
- ✅ Remove any summary rows at top/bottom
- ✅ Ensure dates are in correct format
- ✅ Check file isn't corrupted

**Common Issues to Avoid**:
- ❌ Don't merge multiple vendor files into one
- ❌ Don't manually add/remove columns
- ❌ Don't use formulas (save as values)
- ❌ Don't include extra sheets with notes

#### Step 3: Upload File

**Method 1: Drag & Drop** (Easiest)
1. Open file location on your computer
2. Drag file into the upload area
3. Release mouse button

**Method 2: Click to Browse**
1. Click "Choose File" or "Browse"
2. Navigate to file location
3. Select file
4. Click "Open"

#### Step 4: Choose Upload Mode

**Three options**:

1. **Replace** (⚠️ Use Carefully)
   - Deletes ALL existing data for this vendor
   - Inserts new data from file
   - Use when: Starting fresh, correcting major errors

2. **Append** (✅ Recommended)
   - Keeps existing data
   - Adds new data from file
   - Use when: Adding monthly updates, new time periods

3. **Validate Only**
   - Checks file for errors
   - Does NOT insert data
   - Use when: Testing new vendor format, checking data quality

**Which mode should I use?**

| Scenario | Mode | Why |
|----------|------|-----|
| Monthly sales update | Append | Adds new month's data to existing |
| Correcting last month's data | Replace | Removes incorrect data, inserts corrected |
| Testing new vendor file | Validate Only | Check for errors before committing |
| Initial data load | Append or Replace | Either works for first upload |

#### Step 5: Monitor Processing

**What happens after clicking "Upload":**

```
1. File uploads to server (5-10 seconds)
2. Vendor auto-detection (2-3 seconds)
3. File processing (10-60 seconds, depending on size)
4. Data validation (checking for errors)
5. Database insertion (batched for speed)
6. Email notification sent
```

**Progress Indicators**:
- Progress bar: Shows processing status
- Row counter: "Processing 1,234 of 5,678 rows"
- Time estimate: "Estimated time remaining: 45 seconds"
- Status messages: "Validating EANs...", "Inserting records..."

#### Step 6: Review Results

**Success** ✅
```
Upload Complete!

File: liberty_september_2024.xlsx
Vendor: Liberty (auto-detected)
Total rows: 1,234
Successfully imported: 1,230
Errors: 4

[View Error Report] [Go to Dashboard]
```

**Partial Success** ⚠️
```
Upload Completed with Warnings

File: galilu_q3_2024.csv
Vendor: Galilu (auto-detected)
Total rows: 5,678
Successfully imported: 5,650
Errors: 28

⚠️ 28 rows had validation errors (invalid EANs, missing prices)

[Download Error Report] [Review Errors]
```

**Failure** ❌
```
Upload Failed

File: unknown_vendor.xlsx
Error: Could not detect vendor format

Possible reasons:
- File format not recognized
- Missing required columns
- Vendor not yet supported

[Contact Support] [Try Another File]
```

### Understanding Error Reports

**Common Errors and Solutions**:

| Error | Meaning | Solution |
|-------|---------|----------|
| "Invalid EAN format" | Product barcode is not 13 digits | Check product catalog, verify EAN is correct |
| "Missing required column" | File is missing expected column | Verify file is from correct vendor, check column names |
| "Invalid date" | Date format is incorrect | Ensure dates are in MM/YYYY or DD/MM/YYYY format |
| "Duplicate entry" | Record already exists | Normal if file contains historical data, can safely ignore |
| "Price is zero or negative" | Product price is invalid | Check vendor file for data errors |

**Downloading Error Report**:
1. Click "Download Error Report"
2. Opens Excel file with:
   - Row number in original file
   - Error description
   - Problematic value
   - Suggested fix

**Example Error Report**:
| Row | Column | Value | Error | Suggestion |
|-----|--------|-------|-------|------------|
| 45 | EAN | 12345678901 | Invalid EAN: must be 13 digits | Check product catalog for correct EAN |
| 67 | Price | -45.00 | Price cannot be negative | Verify vendor file for data error |

---

## Understanding Your Dashboard

### Dashboard Overview

Your dashboard is divided into sections:

```
┌─────────────────────────────────────────────────────────┐
│  Top Section: KPI Cards                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Total    │ │ Growth   │ │ Avg Order│ │ Units    │  │
│  │ Sales    │ │ YoY      │ │ Value    │ │ Sold     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────────────────┤
│  Middle Section: Charts                                 │
│  ┌────────────────────────┐ ┌────────────────────────┐│
│  │ Sales Trends           │ │ Channel Breakdown      ││
│  │ (Line Chart)           │ │ (Pie Chart)            ││
│  └────────────────────────┘ └────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│  Bottom Section: Data Tables                            │
│  ┌────────────────────────────────────────────────────┐│
│  │ Top Products (Sortable, Filterable)                ││
│  │ Recent Orders                                       ││
│  │ Store Performance                                   ││
│  └────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### KPI Cards Explained

**Total Sales**
- Shows: Total revenue in EUR
- Time Period: Selectable (MTD, QTD, YTD, All-Time)
- Click to: Drill down into sales details

**Growth YoY**
- Shows: Year-over-year growth percentage
- Calculation: (This Year - Last Year) / Last Year × 100
- Color: Green (positive), Red (negative)

**Average Order Value**
- Shows: Average revenue per order
- Calculation: Total Sales / Number of Orders
- Use for: Understanding customer spending patterns

**Units Sold**
- Shows: Total quantity of products sold
- Time Period: Same as Total Sales
- Click to: View product breakdown

### Interactive Charts

**Sales Trends (Line Chart)**

Features:
- Hover over points to see exact values
- Toggle between: Daily, Weekly, Monthly, Quarterly
- Compare: This Year vs Last Year (overlaid lines)
- Filter by: Channel, Vendor, Product Category

**How to Use**:
1. Hover over chart to see tooltips
2. Click legend to hide/show lines
3. Drag to zoom into specific time range
4. Right-click to export chart as image

**Channel Breakdown (Pie Chart)**

Shows distribution of sales across channels:
- Online (D2C website)
- Offline (Retail partners)
- Marketplace (Amazon, etc.)

**How to Use**:
1. Hover to see percentage and amount
2. Click slice to filter entire dashboard to that channel
3. Click again to reset filter

### Data Tables

**Top Products Table**

Columns:
- Product Name
- Total Sales (EUR)
- Units Sold
- Average Price
- Growth vs Last Period

**Actions**:
- **Sort**: Click column header to sort
- **Filter**: Use search box to find products
- **Export**: Click "Export" to download as Excel

**Recent Orders Table**

Shows latest sales transactions:
- Order Date
- Product
- Channel
- Quantity
- Price
- Total

Useful for: Checking recent activity, verifying uploads

---

## Using AI Chat

### What is AI Chat?

AI Chat is your personal data analyst. Ask questions in plain English, get instant insights.

**Example Questions**:
- "What were my top selling products last month?"
- "Compare Liberty sales to Galilu sales this quarter"
- "Show me sales trends for Midnight Rose EDP"
- "Which stores had highest growth in Q3?"
- "What's my average order value by channel?"

### How to Use AI Chat

#### Step 1: Open Chat Interface

1. Click **"AI Chat"** in left sidebar
2. Chat window opens with greeting message

#### Step 2: Ask Your Question

**Tips for Best Results**:

✅ **Good Questions** (Specific):
- "What were total sales for Liberty in September 2024?"
- "Show me top 10 products by revenue last quarter"
- "Compare online vs offline sales year-to-date"

❌ **Vague Questions**:
- "How are we doing?" (too broad)
- "Sales" (not a question)
- "Products" (unclear what you want)

✅ **Use Specific Terms**:
- Time periods: "last month", "Q3 2024", "year-to-date"
- Vendors: "Liberty", "Galilu", "Selfridges"
- Metrics: "revenue", "units sold", "average price"
- Channels: "online sales", "B2B sales", "retail partners"

#### Step 3: Review Results

AI Chat returns:
1. **Natural language answer**
   - Summary of findings
   - Key numbers and insights

2. **Data table** (if applicable)
   - Structured results
   - Sortable columns

3. **Follow-up suggestions**
   - Related questions you might ask

**Example Interaction**:

```
You: What were my top 5 selling products last quarter?

AI: Based on Q3 2024 data, your top 5 products by revenue were:

1. Midnight Rose EDP 50ml - €55,530 (1,234 units)
2. Citrus Bloom EDT 100ml - €40,095 (891 units)
3. Ocean Breeze Travel Set - €28,350 (567 units)
4. Vanilla Dream Body Lotion - €22,104 (876 units)
5. Lavender Night Cream 50ml - €20,344 (678 units)

Total revenue from top 5: €166,423
This represents 42% of your total Q3 sales.

[View Full Product List] [Compare to Q2]

You might also want to ask:
- "Show me Liberty-specific sales for these products"
- "What's the trend for Midnight Rose over the last 6 months?"
- "Compare online vs offline sales for top products"
```

### Advanced Chat Features

**Follow-Up Questions**

AI remembers conversation context:

```
You: What were Liberty sales last quarter?
AI: Liberty Q3 2024 sales were €123,456

You: And the quarter before?
AI: Liberty Q2 2024 sales were €108,234
     That's a 14.1% increase quarter-over-quarter.

You: What about Galilu for the same period?
AI: Galilu Q3 2024 sales were €98,765
     Galilu Q2 2024 sales were €95,432
     Growth: 3.5%

     Comparison: Liberty grew 4x faster than Galilu
```

**Comparative Analysis**

```
You: Compare Liberty to Galilu sales year-to-date

AI: Year-to-Date 2024 Comparison (Jan-Sep):

Liberty:
- Total Sales: €456,789
- Units Sold: 12,345
- Average Price: €37.02
- Growth vs 2023: +18.5%

Galilu:
- Total Sales: €321,654
- Units Sold: 9,876
- Average Price: €32.56
- Growth vs 2023: +12.3%

Key Insights:
- Liberty outsells Galilu by 42%
- Liberty has higher average price (+13.7%)
- Liberty growing faster (+6.2 percentage points)
```

**Time-Based Queries**

```
You: Show me sales trends for Midnight Rose EDP over the last 6 months

AI: Midnight Rose EDP Sales Trend (Apr-Sep 2024):

Apr 2024: €8,234 (183 units)
May 2024: €9,102 (202 units)
Jun 2024: €10,456 (232 units)
Jul 2024: €12,345 (274 units)
Aug 2024: €11,234 (249 units)
Sep 2024: €13,567 (301 units)

Trend Analysis:
- Overall growth: +64.7% (Apr to Sep)
- Average monthly growth: +10.8%
- Peak month: September (+20.8% vs Aug)
```

### Chat Best Practices

**Do**:
- ✅ Ask specific questions
- ✅ Specify time periods
- ✅ Use vendor/product names
- ✅ Ask follow-up questions for clarity

**Don't**:
- ❌ Ask about data you haven't uploaded yet
- ❌ Expect predictions (AI shows past data, not forecasts)
- ❌ Ask multiple unrelated questions at once
- ❌ Use slang or abbreviations AI might not understand

---

## Advanced Analytics

### Filtering Data

**Available Filters**:

1. **Date Range**
   - Predefined: Last 7 days, Last 30 days, Last quarter, Year-to-date
   - Custom: Select specific start and end dates

2. **Channel**
   - Online (D2C)
   - Offline (B2B resellers)
   - All channels

3. **Vendor/Reseller**
   - Select one or multiple vendors
   - Useful for partner-specific analysis

4. **Product Category**
   - Filter by product type (EDP, EDT, Body Care, etc.)
   - Requires product categories to be set up

5. **Country/Region**
   - Filter by geographic market
   - Useful for international brands

**How to Apply Filters**:

1. Click "Filters" button (top right of dashboard)
2. Select desired filters
3. Click "Apply"
4. Dashboard updates to show filtered data
5. Click "Reset" to clear all filters

---

## Customizing Dashboards

### Creating a Custom Dashboard

**Scenario**: You want a Liberty-specific dashboard

1. **Click "Create Dashboard"**
   - Button in top right corner

2. **Name Your Dashboard**
   - Example: "Liberty Performance Dashboard"
   - Description: "Monthly Liberty sales and trends"

3. **Add Widgets**

   **KPI Card**:
   - Click "+ Add Widget"
   - Select "KPI Card"
   - Choose metric: Total Sales
   - Add filter: Vendor = Liberty
   - Set position: Top left

   **Line Chart**:
   - Click "+ Add Widget"
   - Select "Line Chart"
   - X-Axis: Month
   - Y-Axis: Total Sales
   - Filter: Vendor = Liberty
   - Time Range: Last 12 months
   - Set position: Top right

   **Product Table**:
   - Click "+ Add Widget"
   - Select "Data Table"
   - Data: Top Products
   - Filter: Vendor = Liberty
   - Limit: Top 20 products
   - Set position: Bottom

4. **Arrange Layout**
   - Drag widgets to desired positions
   - Resize by dragging corners

5. **Save Dashboard**
   - Click "Save"
   - Dashboard appears in "My Dashboards" list

### Setting Primary Dashboard

Your primary dashboard loads automatically when you log in.

**To set**:
1. Go to "My Dashboards"
2. Find desired dashboard
3. Click ⭐ star icon
4. Confirmation: "Set as primary dashboard"

---

## Exporting Reports

### Export Options

**1. Export to Excel**
- Full data export with all filters applied
- Includes calculated fields (totals, averages)
- Useful for: Further analysis in Excel, sharing with colleagues

**How to Export**:
1. Apply desired filters
2. Click "Export" → "Excel"
3. File downloads: `sales_report_2024-10-25.xlsx`

**2. Export to PDF**
- Formatted report with charts and tables
- Professional appearance for presentations
- Useful for: Management reports, presentations

**How to Export**:
1. Apply desired filters
2. Click "Export" → "PDF"
3. Select report template:
   - Executive Summary (1 page)
   - Detailed Report (multi-page)
   - Custom (select widgets to include)
4. File downloads: `sales_report_2024-10-25.pdf`

**3. Export Charts as Images**
- Individual charts as PNG images
- Useful for: Presentations, documents

**How to Export**:
1. Right-click on any chart
2. Select "Save as Image"
3. Choose format: PNG (recommended) or SVG
4. File downloads: `sales_trend_chart.png`

---

## Troubleshooting

### Common Issues

#### "No Data to Display"

**Possible Causes**:
1. No files uploaded yet
2. Filters too restrictive (no data matches)
3. Upload still processing

**Solutions**:
1. Check "Upload History" - any completed uploads?
2. Reset filters (click "Reset")
3. Wait for upload processing to complete

#### "Upload Failed"

**Possible Causes**:
1. File format not recognized
2. Missing required columns
3. File corrupted

**Solutions**:
1. Verify file is from supported vendor
2. Check file isn't manually edited
3. Try re-downloading file from vendor
4. Contact support with file sample

#### "AI Chat Not Responding"

**Possible Causes**:
1. No data uploaded yet
2. Question too vague
3. System maintenance

**Solutions**:
1. Verify you have uploaded data
2. Rephrase question to be more specific
3. Try again in a few minutes
4. Contact support if issue persists

#### "Dashboard Loading Slowly"

**Possible Causes**:
1. Large dataset (millions of records)
2. Complex filters applied
3. Network connection slow

**Solutions**:
1. Narrow date range filter
2. Reduce number of widgets on dashboard
3. Check internet connection
4. Clear browser cache

### Getting Help

**Support Channels**:

1. **In-App Help**
   - Click "?" icon (top right)
   - Search help articles
   - View tutorials

2. **Email Support**
   - support@taskifai.com
   - Response time: 24-48 hours

3. **Administrator**
   - Your company's TaskifAI administrator
   - Can help with account issues, permissions

**When Contacting Support, Include**:
- Your company name (tenant)
- Email address
- Screenshot of error (if applicable)
- Steps to reproduce issue
- Upload batch ID (if related to upload)

---

## Best Practices

### Data Upload Best Practices

1. **Upload Regularly**
   - Monthly uploads for monthly data
   - Keep data fresh for accurate insights

2. **Verify Before Uploading**
   - Check file isn't corrupted
   - Ensure dates are correct
   - Verify file is from correct vendor

3. **Use Consistent Naming**
   - Example: `liberty_september_2024.xlsx`
   - Helps track upload history

4. **Review Error Reports**
   - Fix data quality issues
   - Improve future uploads

### Dashboard Best Practices

1. **Create Role-Specific Dashboards**
   - Executive Dashboard (high-level KPIs)
   - Analyst Dashboard (detailed metrics)
   - Vendor-Specific Dashboards

2. **Use Meaningful Names**
   - ✅ "Liberty Q3 Performance"
   - ❌ "Dashboard 1"

3. **Keep It Simple**
   - 5-8 widgets per dashboard
   - Too many widgets = information overload

4. **Update Filters Regularly**
   - Change date ranges as time progresses
   - Review quarterly to ensure relevance

### AI Chat Best Practices

1. **Start Broad, Then Narrow**
   - "Show me Q3 sales" → "Show me Liberty Q3 sales" → "Show me Liberty EDP sales in Q3"

2. **Learn from Examples**
   - Review "Sample Questions" in chat interface
   - Copy and adapt to your needs

3. **Ask Follow-Up Questions**
   - AI remembers context
   - Faster than starting new conversation

4. **Save Useful Queries**
   - Screenshot or copy important results
   - Create dashboard widgets for frequent queries

---

## Related Documentation

- [Platform Overview](./PLATFORM_GUIDE.md) - Complete platform guide
- [FAQ](./FAQ.md) - Frequently asked questions
- [Video Tutorials](./tutorials/) - Step-by-step videos

---

**Questions?** Contact your administrator or email support@taskifai.com

**Last Updated**: 2025-10-25
**Next Review**: Quarterly
