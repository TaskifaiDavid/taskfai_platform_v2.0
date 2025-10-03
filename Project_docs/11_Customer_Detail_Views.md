# 11. Customer Detail Views & User Guide

This document provides comprehensive customer-facing documentation to give end users detailed visibility into system features, workflows, and best practices.

## 11.1. Purpose & Audience

**Who This Document Is For:**
- Business users (sales analysts, account managers, executives)
- New users onboarding to the platform
- Existing users wanting to maximize platform value
- Administrators training team members

**What You'll Learn:**
- Complete user journeys from login to insights
- How to use each feature effectively
- Understanding data and reports
- Troubleshooting common issues
- Best practices and tips

---

## 11.2. Getting Started: Your First Login

### Initial Access

**What You Need:**
1. Email address (provided by your administrator)
2. Password (set during account creation or via reset link)
3. Web browser (Chrome, Firefox, Safari, or Edge)

**Login Process:**
```
Step 1: Navigate to https://[your-platform-url].com
Step 2: Enter your email address
Step 3: Enter your password
Step 4: Click "Sign In"
Step 5: You're now on the Dashboard
```

**What You See After Login:**

```
┌─────────────────────────────────────────────────────────────┐
│  BIBBI                                    [Your Email] [⚙]  │
│  Data Analytics Platform                               [↗]  │
├─────────────────────────────────────────────────────────────┤
│  [Upload Files] [Processing Status] [Analytics] [Data Chat] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                  Main Content Area                           │
│           (Shows Upload interface by default)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Navigation Tabs:**
- **Upload Files**: Where you import your sales data
- **Processing Status**: Track your upload progress and history
- **Analytics**: View external dashboards and visualizations
- **Data Chat**: Ask questions about your data using AI

---

## 11.3. Complete Upload Workflow

### Understanding Upload Modes

The system supports TWO upload modes:

#### **Mode 1: Append (Add New Data)**
- **What It Does**: Adds new sales records to your existing data
- **When to Use**: Monthly sales reports, new data batches
- **Data Safety**: Never deletes existing data
- **Example**: You uploaded January sales, now adding February sales

#### **Mode 2: Replace (Start Fresh)**
- **What It Does**: Deletes ALL existing data and replaces with new upload
- **When to Use**: Year-end reset, correcting historical data, full data refresh
- **Data Safety**: ⚠️ Permanently removes all previous data
- **Example**: You need to reload all 2024 data with corrections

**Critical Decision Point:**
```
Before uploading, ask yourself:
- "Am I adding to what's already there?" → Use APPEND
- "Do I need to start completely over?" → Use REPLACE

When in doubt, use APPEND (safer option)
```

### Step-by-Step Upload Process

**Step 1: Prepare Your File**

✅ **Accepted Formats:**
- Excel files (.xlsx, .xls)
- CSV files (.csv)

✅ **Supported Vendors (Auto-Detected):**
- Galilu (Poland)
- Boxnox (Europe)
- Skins SA (South Africa)
- CDLC (Europe)
- Liberty / Selfridges (UK)
- Ukraine distributors
- Continuity suppliers
- And more...

❌ **Common File Issues:**
- Password-protected files
- Corrupted files
- Files with macros (may be blocked)
- Files larger than 100MB

**Step 2: Navigate to Upload Tab**

Click "Upload Files" in the top navigation.

**Step 3: Select Upload Mode**

```
┌────────────────────────────────────────┐
│  [  Append  ]  [  Replace  ]           │
│   (Selected)     (Inactive)            │
└────────────────────────────────────────┘
```

Click the mode you need. Selected mode is highlighted in blue.

**Step 4: Choose Your File**

```
┌────────────────────────────────────────┐
│  Drag & Drop Your File Here           │
│           OR                           │
│  [ Browse Files ]                      │
└────────────────────────────────────────┘
```

- **Drag & Drop**: Drag file from your computer onto this area
- **Browse**: Click button to select file from computer

**Step 5: Confirm Upload**

After selecting file, you'll see a confirmation:

```
┌────────────────────────────────────────┐
│  Selected File:                        │
│  Galilu_Sales_May_2024.xlsx            │
│  Size: 2.3 MB                          │
│  Mode: Append                          │
│                                        │
│  [Cancel]  [Upload File]               │
└────────────────────────────────────────┘
```

**Review Before Uploading:**
- Is the filename correct?
- Is the file size reasonable?
- Is the mode correct (Append vs Replace)?

Click "Upload File" to proceed.

**Step 6: Processing Begins**

You'll see a processing indicator:

```
┌────────────────────────────────────────┐
│  Uploading...                          │
│  [████████░░░░░░░░░░] 45%             │
│                                        │
│  Detecting vendor format...            │
└────────────────────────────────────────┘
```

**What Happens During Processing:**

1. **File Upload** (5-15 seconds)
   - File transfers to server

2. **Vendor Detection** (1-3 seconds)
   - System identifies vendor from filename and content
   - Example: "Galilu" detected from "Galilu_Sales.xlsx"

3. **Data Extraction** (10-30 seconds)
   - Reads Excel/CSV file
   - Handles multiple sheets if present

4. **Data Normalization** (20-60 seconds)
   - Converts vendor-specific format to standard format
   - Maps column names (e.g., "Sold Qty" → "quantity")
   - Converts currencies if needed
   - Validates product EANs

5. **Data Cleaning** (10-20 seconds)
   - Removes duplicates
   - Fixes formatting issues
   - Validates dates and numbers

6. **Database Import** (5-15 seconds)
   - Inserts cleaned data into database
   - Applies user-specific isolation

**Total Processing Time:** Usually 1-2 minutes for typical files (500-5000 rows)

**Step 7: Success or Error**

**Success:**
```
✅ Upload Complete!

File: Galilu_Sales_May_2024.xlsx
Processed: 1,234 rows
Total Sales: €45,678.90
Date Range: May 1-31, 2024

[View in Dashboard] [Upload Another File]
```

**You'll also receive an email confirmation with the same details.**

**Error:**
```
❌ Upload Failed

File: Invalid_Data.xlsx
Errors Found: 45 issues

Common Issues:
- Missing required columns
- Invalid date formats
- Product EAN mismatches

[View Error Details] [Try Again]
```

**Click "View Error Details" to see specific row-by-row errors.**

### Understanding Vendor Detection

**How It Works:**

The system uses intelligent pattern matching:

1. **Filename Analysis**
   - Looks for vendor names in filename
   - Example: "Galilu_May.xlsx" → Galilu detected

2. **Sheet Name Analysis**
   - Checks Excel sheet names for patterns
   - Example: "Sell Out by EAN" → Boxnox format

3. **Content Analysis**
   - Examines column headers
   - Looks for vendor-specific structures

**What Happens When Detected:**

Each vendor has custom processing rules:

| Vendor | Special Processing |
|--------|-------------------|
| **Galilu** | Pivot table format, PLN currency conversion, NULL EAN support |
| **Boxnox** | Multiple sheet processing, "Sell Out by EAN" sheet |
| **Skins SA** | OrderDate column, ZAR currency, auto-detect latest month |
| **CDLC** | Header row at line 4, dynamic Total column detection |
| **Selfridges/Liberty** | GBP currency, specific column mappings |
| **Ukraine** | UAH currency, TDSheet tab processing |

**What To Do If Vendor Not Detected:**

```
System message: "Unknown vendor format detected"

Solutions:
1. Rename file to include vendor name
   Example: "May_Sales.xlsx" → "Galilu_May_Sales.xlsx"

2. Check if file matches known format
   - Does it have expected columns?
   - Is it in the same format as previous uploads?

3. Contact support with sample file
   - We can add support for new vendor formats
```

---

## 11.4. Understanding Processing Status

### Status Tab Overview

The "Processing Status" tab shows all your uploads:

```
┌─────────────────────────────────────────────────────────────┐
│  Your Uploads                                   [Refresh]    │
├────────────┬───────────────┬──────────┬──────────────────────┤
│ Filename   │ Upload Date   │ Status   │ Actions              │
├────────────┼───────────────┼──────────┼──────────────────────┤
│ Galilu_May │ May 20, 14:30 │ ✅ Done  │ [View] [Details]     │
│ Boxnox_Q1  │ May 19, 09:15 │ ❌ Failed│ [Errors] [Retry]     │
│ CDLC_Apr   │ May 18, 16:45 │ ⏳ Processing... │ [Cancel]   │
└────────────┴───────────────┴──────────┴──────────────────────┘
```

### Status Indicators

**✅ Completed**
- Processing finished successfully
- Data now available in dashboards and chat
- Email confirmation sent

**❌ Failed**
- Processing encountered errors
- Data was NOT imported
- Click "Errors" to see what went wrong
- You can retry after fixing issues

**⏳ Processing**
- Currently being processed
- Wait for completion (usually 1-2 minutes)
- You can navigate away - processing continues
- You'll get email when done

**⏸ Pending**
- Queued for processing
- Will start automatically when server available
- Rare (only during high-volume periods)

### Understanding Upload Details

Click "Details" on any upload to see:

```
┌─────────────────────────────────────────────────────────────┐
│  Upload Details: Galilu_May_2024.xlsx                        │
├─────────────────────────────────────────────────────────────┤
│  Status: Completed ✅                                        │
│  Uploaded: May 20, 2024 at 14:30:25                         │
│  Processed: May 20, 2024 at 14:31:48 (1m 23s)               │
│  Mode: Append                                                │
│  Vendor: Galilu (auto-detected)                              │
│                                                              │
│  Processing Results:                                         │
│  - Rows in file: 1,250                                       │
│  - Rows imported: 1,234                                      │
│  - Rows skipped: 16 (duplicates)                             │
│  - Total sales: €45,678.90                                   │
│  - Products: 45 unique products                              │
│  - Date range: May 1-31, 2024                                │
│                                                              │
│  Data Available In:                                          │
│  - AI Chat: Yes                                              │
│  - Dashboards: Yes                                           │
│  - Email Reports: Yes                                        │
│                                                              │
│  [Download Original File] [View Data] [Delete Upload]        │
└─────────────────────────────────────────────────────────────┘
```

### Common Error Messages & Solutions

**Error: "Missing required columns"**
```
Problem: File doesn't have expected columns
Solution: Check your file has these columns:
- Product name or EAN
- Sales amount or revenue
- Quantity
- Date (month/year or full date)

Vendor-specific column names are okay (e.g., "Sold Qty" for Galilu)
```

**Error: "Invalid date format"**
```
Problem: Dates aren't in expected format
Solution: Dates should be:
- Excel date format (recommended)
- YYYY-MM-DD (e.g., 2024-05-20)
- DD/MM/YYYY (e.g., 20/05/2024)

Avoid: Text dates like "May 20th" or "20-May"
```

**Error: "Product EAN not found"**
```
Problem: Product EAN doesn't match products in database
Solution:
1. Verify EAN is correct in your file
2. Check if product exists in system
3. NULL EAN is allowed for some vendors (Galilu)
4. Contact admin to add new products
```

**Error: "Duplicate filename"**
```
Problem: You already uploaded a file with this name
Solution:
1. Rename your file if it's different data
2. Or use "Replace" mode if correcting previous upload
3. Or delete previous upload first
```

**Error: "File too large"**
```
Problem: File exceeds size limit (100MB)
Solution:
1. Split into smaller files by month
2. Remove unnecessary sheets from Excel
3. Compress file (zip) before upload
4. Contact admin for large file support
```

---

## 11.5. Using AI Data Chat

### What Is Data Chat?

Data Chat lets you ask questions about your sales data in plain English. No SQL, no complex filters - just natural conversation.

**Example Questions:**
- "What were total sales in May 2024?"
- "Which reseller sold the most this year?"
- "Compare online vs offline sales"
- "Show me top 5 products by revenue"
- "How did sales change from January to March?"

### Getting Started with Chat

**Step 1: Navigate to Data Chat Tab**

Click "Data Chat" in the top navigation.

**Step 2: Type Your Question**

```
┌─────────────────────────────────────────────────────────────┐
│  AI Data Assistant                             [Clear Chat]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Assistant] Hi! I'm your AI data assistant. Ask me         │
│  anything about your sales data.                             │
│                                                              │
│  [You] What were total sales in May 2024?                   │
│                                                              │
│  [Assistant] In May 2024, your total sales across all        │
│  channels were €45,320.50, representing 3,210 units sold...│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Type your question... [Send]                                │
└─────────────────────────────────────────────────────────────┘
```

**Step 3: Review the Answer**

The AI will:
- Analyze your question
- Query your data
- Provide detailed answer with numbers
- Include business insights

### Effective Questions: Best Practices

**✅ Good Questions (Specific & Clear):**

1. **Time-Specific:**
   - "What were sales in May 2024?"
   - "Show me Q1 2024 performance"
   - "Compare May vs June sales"

2. **Entity-Specific:**
   - "Which reseller had highest revenue?"
   - "What's our best-selling product?"
   - "Show me Galilu sales this year"

3. **Metric-Specific:**
   - "Total revenue this month"
   - "How many units sold in March?"
   - "Average order value for Product A"

4. **Comparative:**
   - "Compare 2024 vs 2023 sales"
   - "Which month had highest sales?"
   - "Online vs offline performance"

**❌ Avoid Vague Questions:**

1. **Too Broad:**
   - "Show me everything" → Too vague
   - Better: "Show me sales summary for May 2024"

2. **Missing Context:**
   - "How are we doing?" → Unclear timeframe
   - Better: "How are we doing in Q2 2024 vs Q1 2024?"

3. **Ambiguous:**
   - "What about Product A?" → What metric?
   - Better: "What were Product A sales in euros this month?"

### Understanding Chat Responses

**Response Structure:**

```
[Assistant] In May 2024, your total sales were €45,320.50.

Breakdown by channel:
- Offline/Wholesale: €32,140.25 (71%)
- Online: €13,180.25 (29%)

Top performing resellers:
1. Galilu: €12,340.50
2. Boxnox: €8,920.30
3. Skins SA: €7,100.15

This represents a 15% increase from April 2024.
```

**What's Included:**
1. **Direct Answer**: Main metric requested
2. **Breakdown**: Detailed segmentation
3. **Context**: Comparisons and trends
4. **Insights**: Business implications

### Follow-Up Questions

The chat remembers context from previous questions:

```
[You] What were sales in May 2024?
[Assistant] May 2024 sales were €45,320.50...

[You] How does that compare to June?
[Assistant] June 2024 had €52,180.75 in sales, which is
€6,860.25 higher than May (15% growth)...

[You] Which products drove that growth?
[Assistant] The growth was primarily driven by:
1. Product A: +€2,340
2. Product B: +€1,890
3. Product C: +€1,230
```

**Memory Features:**
- Remembers last 5 conversation exchanges
- Understands references like "that", "it", "previous month"
- Maintains context for follow-up questions
- Click "Clear Chat" to start fresh conversation

### Online vs Offline Sales Questions

The system understands TWO separate sales channels:

**Offline/Wholesale (B2B):**
- Sales through reseller partners
- Examples: Galilu, Boxnox, Skins SA
- Monthly aggregated data
- Keywords: "offline", "wholesale", "reseller", "B2B"

**Online Sales (D2C):**
- Direct-to-consumer e-commerce
- Individual order data
- Daily transaction details
- Keywords: "online", "ecommerce", "website", "direct"

**Channel-Specific Questions:**

```
Online Sales:
- "What were online sales in Germany?"
- "Which marketing source converts best?"
- "Show me sales by device type"
- "What's the top-selling country online?"

Offline Sales:
- "Which reseller sold the most?"
- "Show me wholesale performance"
- "What's Galilu's total this year?"
- "B2B sales trend analysis"

Combined:
- "Total sales across all channels"
- "Compare online vs offline"
- "What percentage comes from online?"
```

### Data Chat Limitations

**What Chat CAN Do:**
✅ Answer questions about your data
✅ Perform calculations and aggregations
✅ Compare time periods, products, resellers
✅ Provide trends and insights
✅ Remember conversation context

**What Chat CANNOT Do:**
❌ Predict future sales (no forecasting yet)
❌ Modify or delete data
❌ Access other users' data
❌ Generate visual charts (text responses only)
❌ Upload new data
❌ Change system settings

### Troubleshooting Chat

**Issue: "I don't have enough data to answer"**
```
Cause: No data exists for requested time period
Solution:
1. Check if you've uploaded data for that period
2. Try broader time range
3. Verify date format in question
```

**Issue: "Please be more specific"**
```
Cause: Question too ambiguous
Solution:
1. Add time period: "in May 2024"
2. Specify metric: "revenue" vs "units"
3. Specify channel: "online" or "offline"
```

**Issue: Response seems wrong**
```
Cause: Possible data issues or misunderstanding
Solution:
1. Rephrase question more clearly
2. Ask for breakdown to verify numbers
3. Check uploaded data is correct
4. Contact support if numbers don't match expectations
```

---

## 11.6. Understanding Analytics Dashboards

### What Are Analytics Dashboards?

Analytics dashboards are external visualization tools (like Looker, Tableau, Power BI) that you can embed directly into the platform for visual data exploration.

### Connecting Your First Dashboard

**Prerequisites:**
- External dashboard URL (from Looker, Tableau, etc.)
- Dashboard must allow iframe embedding
- Dashboard should be publicly accessible or have authentication

**Step-by-Step:**

1. **Get Your Dashboard URL**
   - Go to your external analytics tool
   - Find the "Share" or "Embed" option
   - Copy the embed/iframe URL
   - Example: `https://lookerstudio.google.com/embed/reporting/abc123...`

2. **Navigate to Analytics Tab**
   - Click "Analytics" in top navigation

3. **Click "Connect Dashboard" Button**
   - You'll see a floating (+) button
   - Or "Connect Your First Dashboard" if none exist

4. **Fill in Connection Form**
   ```
   Dashboard Name: Sales Performance Q2 2024
   Dashboard URL: https://lookerstudio.google.com/embed/...
   □ Set as primary dashboard
   ```

5. **Click "Connect Dashboard"**
   - Dashboard appears immediately
   - URL loaded in iframe

6. **Interact with Dashboard**
   - Fully interactive within platform
   - Click elements, change filters
   - Exactly like viewing in original tool

### Managing Multiple Dashboards

**Tab Navigation:**
```
[Sales Dashboard*] [Marketing Analytics] [Operations]
──────────────────

[Dashboard content displays here]

[Fullscreen] [Open External] [•••] [+]
```

**Switching Dashboards:**
- Click any tab to switch views
- Active dashboard highlighted
- Primary dashboard marked with asterisk (*)

**Dashboard Actions:**

1. **Fullscreen Mode**
   - Click fullscreen button
   - Dashboard expands to fill screen
   - Perfect for presentations
   - Press ESC to exit

2. **Open External**
   - Opens dashboard in new browser tab
   - Useful for multi-monitor setups
   - Access full platform features

3. **More Options (•••)**
   - Disconnect dashboard
   - Confirmation required before deletion

4. **Add New (+)**
   - Connect additional dashboards
   - No limit on quantity

### Dashboard Best Practices

**Organization:**
- Name dashboards clearly (e.g., "Sales Q1 2024" not "Dashboard 1")
- Set most-used dashboard as primary
- Remove unused dashboards to reduce clutter

**Performance:**
- Choose optimized dashboards (fast loading)
- Limit to 5-7 dashboards for best performance
- Complex dashboards may load slowly in iframe

**Security:**
- Only connect dashboards you trust
- Avoid embedding dashboards with sensitive external data
- Use HTTPS URLs only

### Troubleshooting Dashboards

**Issue: Dashboard won't load**
```
Possible Causes:
1. URL doesn't allow iframe embedding
2. Dashboard requires authentication
3. Firewall/corporate network blocking

Solutions:
1. Check URL allows embedding (some tools block iframes)
2. Use "Open External" to verify dashboard works
3. Try accessing from different network
4. Contact dashboard provider support
```

**Issue: Dashboard loads but shows error**
```
Possible Causes:
1. Dashboard was deleted in external tool
2. Permissions changed
3. Dashboard URL expired

Solutions:
1. Verify dashboard still exists in external tool
2. Generate new embed URL
3. Update dashboard configuration
```

**Issue: Can't interact with dashboard elements**
```
Possible Causes:
1. Sandbox restrictions
2. Dashboard requires login

Solutions:
1. Use "Open External" for full functionality
2. Check if external tool requires active login
```

---

## 11.7. Email Reports & Notifications

### Automatic Upload Notifications

**Success Notification:**
```
Subject: Upload Successful: Galilu_Sales_May_2024.xlsx

Your file has been successfully processed!

Summary:
- Rows Processed: 1,234
- Total Sales: €45,678.90
- Date Range: May 1-31, 2024
- Processing Time: 1m 23s

[View Data in Dashboard]
```

**When You Get It:** Immediately after processing completes

**What To Do:**
- Verify summary statistics match expectations
- Click link to view data
- If numbers seem wrong, check source file

**Failure Notification:**
```
Subject: Upload Failed: Invalid_File.xlsx

Your file encountered errors during processing.

Error Summary:
- Total Errors: 45
- Critical: Missing required columns

[View Detailed Error Report]
```

**When You Get It:** Immediately after processing fails

**What To Do:**
- Click "View Error Report" link
- Review specific errors
- Fix issues in source file
- Re-upload corrected file

### Scheduled Reports (Future Feature)

**Coming Soon:**
- Daily/weekly/monthly automated reports
- Delivered to your inbox
- PDF, CSV, or Excel format
- Customizable metrics and filters

---

## 11.8. Understanding Your Data

### Data Hierarchy

Your sales data has a clear structure:

```
Sales Transaction
├── Who: Reseller/Channel
│   ├── Offline: Galilu, Boxnox, Skins SA, etc.
│   └── Online: Direct customers
├── What: Product
│   ├── Product Name
│   ├── Product EAN
│   └── Category (if available)
├── When: Time
│   ├── Year
│   ├── Month
│   └── Specific Date (online orders)
├── How Much: Financial
│   ├── Quantity Sold
│   ├── Unit Price
│   ├── Total Revenue
│   └── Currency
└── Where: Geography (online only)
    ├── Country
    ├── City
    └── Region
```

### Key Metrics Explained

**Total Revenue:**
- Sum of all sales in euros (€)
- Includes both online and offline
- Currency converted automatically
- Example: €45,678.90

**Units Sold:**
- Total quantity of products sold
- Count of individual items
- Example: 1,234 units

**Number of Transactions:**
- How many sales records
- Offline: Monthly aggregates per reseller/product
- Online: Individual orders
- Example: 567 transactions

**Average Order Value (AOV):**
- Total Revenue ÷ Number of Transactions
- Higher for wholesale, lower for retail
- Example: €80.50 average

**Best-Selling Product:**
- Product with highest revenue or units
- Can differ based on metric
- Example: Product A (€12,340 revenue)

**Top Reseller:**
- Reseller with highest sales
- B2B partners only (offline)
- Example: Galilu (€23,450)

### Data Freshness

**What "Fresh" Means:**
- Your data is as current as your last upload
- System doesn't auto-sync with external sources
- You control when data updates

**Keeping Data Current:**
```
Recommended Upload Frequency:
- Monthly: Most common (end-of-month reports)
- Weekly: For fast-moving business
- Daily: For online sales tracking

Always Use APPEND Mode for Regular Updates
Only Use REPLACE When Starting Over
```

---

## 11.9. Common Use Cases & Workflows

### Use Case 1: Monthly Sales Review

**Goal:** Analyze performance for the past month

**Workflow:**
```
1. Upload month's data (Append mode)
   ↓
2. Wait for "Upload Successful" email
   ↓
3. Go to Data Chat tab
   ↓
4. Ask: "What were total sales last month?"
   ↓
5. Ask: "Which resellers performed best?"
   ↓
6. Ask: "Compare to previous month"
   ↓
7. Review insights, take action
```

**Time Required:** 5-10 minutes

### Use Case 2: Product Performance Analysis

**Goal:** Identify best and worst performing products

**Workflow:**
```
1. Go to Data Chat
   ↓
2. Ask: "Show me top 10 products by revenue this year"
   ↓
3. Ask: "Which products have declining sales?"
   ↓
4. Ask: "Compare Product A vs Product B performance"
   ↓
5. Document findings for product team
```

**Time Required:** 5 minutes

### Use Case 3: Reseller Performance Review

**Goal:** Evaluate partner performance

**Workflow:**
```
1. Go to Data Chat
   ↓
2. Ask: "Show me sales by reseller for Q2 2024"
   ↓
3. Ask: "Which reseller grew the most?"
   ↓
4. Ask: "What products does Galilu sell best?"
   ↓
5. Use insights for account management
```

**Time Required:** 5 minutes

### Use Case 4: Online vs Offline Comparison

**Goal:** Understand channel performance

**Workflow:**
```
1. Go to Data Chat
   ↓
2. Ask: "Compare online vs offline sales this year"
   ↓
3. Ask: "What percentage comes from each channel?"
   ↓
4. Ask: "Which products sell better online?"
   ↓
5. Adjust marketing strategy based on findings
```

**Time Required:** 5-10 minutes

### Use Case 5: Year-Over-Year Growth

**Goal:** Measure business growth

**Workflow:**
```
1. Ensure you have data for both years uploaded
   ↓
2. Go to Data Chat
   ↓
3. Ask: "Compare 2024 vs 2023 total sales"
   ↓
4. Ask: "Which products drove growth?"
   ↓
5. Ask: "What was the growth percentage?"
   ↓
6. Share results with leadership
```

**Time Required:** 5 minutes

---

## 11.10. Tips & Best Practices

### File Management

**Naming Convention:**
```
Good:
✅ Galilu_Sales_May_2024.xlsx
✅ Boxnox_Q2_2024.xlsx
✅ Online_Sales_2024-05.xlsx

Bad:
❌ data.xlsx
❌ sales.xlsx
❌ Report_Final_v2_updated.xlsx
```

**Benefit:** Easy to identify vendor and period in upload history

**Monthly Workflow:**
```
1st of Month:
- Download last month's data from each vendor
- Upload to platform using APPEND mode
- Verify processing success
- Run monthly analysis via Chat

Benefits:
- Data stays current
- Trends visible quickly
- Issues caught early
```

### Data Quality

**Before Uploading:**
- ✅ Check file opens correctly
- ✅ Verify data matches expected period
- ✅ Ensure no password protection
- ✅ Remove any summary/total rows at bottom
- ✅ Keep original vendor format

**After Uploading:**
- ✅ Review "Rows Processed" matches file
- ✅ Spot-check a few numbers in Chat
- ✅ Compare to previous month for sanity
- ✅ Investigate if something looks wrong

### Chat Efficiency

**Start Broad, Then Narrow:**
```
1. "What were total sales in May 2024?"
2. "Which resellers contributed most?"
3. "Show me Galilu's product breakdown"
```

**Use Follow-Ups:**
```
Instead of:
"What were May sales?"
"What were June sales?"
"What were July sales?"

Do:
"What were May sales?"
"How about June?"
"And July?"
(Chat remembers context)
```

**Save Common Questions:**
Keep a note file with your frequent questions for easy copy-paste.

### Dashboard Organization

**Primary Dashboard:**
- Set your most-used dashboard as primary
- It loads by default when visiting Analytics tab

**Naming Strategy:**
```
By Function:
- "Sales Overview"
- "Marketing Performance"
- "Operations Metrics"

By Period:
- "Q1 2024 Results"
- "2024 Annual Dashboard"

By Audience:
- "Executive Summary"
- "Sales Team Dashboard"
```

---

## 11.11. Troubleshooting Guide

### Upload Issues

**Problem:** "Vendor not detected"
```
Symptoms:
- Generic processing instead of vendor-specific
- Some data missing or incorrect

Fix:
1. Rename file to include vendor name
2. Verify file format matches previous uploads
3. Check if it's a new vendor format
4. Contact support to add vendor support
```

**Problem:** Upload stuck at "Processing..."
```
Symptoms:
- Status doesn't change after 5+ minutes
- No email received

Fix:
1. Refresh the page
2. Check email (might have completed)
3. If truly stuck, re-upload file
4. Contact support if recurring
```

**Problem:** "File already exists"
```
Symptoms:
- Can't upload file with same name

Fix:
1. Delete previous upload (if outdated)
2. OR rename new file (if different data)
3. OR use Replace mode (if correction)
```

### Chat Issues

**Problem:** Chat gives wrong answer
```
Symptoms:
- Numbers don't match your expectations
- Calculation seems incorrect

Fix:
1. Verify your uploaded data is correct
2. Ask more specific question with dates
3. Ask for breakdown to verify components
4. Clear chat and rephrase question
5. Contact support with specific example
```

**Problem:** Chat says "insufficient data"
```
Symptoms:
- "I don't have data for that period"

Fix:
1. Check you've uploaded data for that timeframe
2. Verify upload completed successfully
3. Try broader date range
4. Check spelling of months/years
```

**Problem:** Chat not understanding question
```
Symptoms:
- "Please be more specific" response
- Irrelevant answer

Fix:
1. Be more specific about time period
2. Specify metric (revenue, units, etc.)
3. Use clear keywords (online, offline, reseller name)
4. Try simpler question structure
```

### Dashboard Issues

**Problem:** Dashboard shows blank/white screen
```
Symptoms:
- Empty iframe
- No content visible

Fix:
1. Check URL is correct embed URL
2. Verify dashboard exists in external tool
3. Try "Open External" to test
4. URL might not allow iframe embedding
5. Use different dashboard URL format
```

**Problem:** Dashboard very slow to load
```
Symptoms:
- Long loading time
- Laggy interactions

Fix:
1. Dashboard may be complex
2. Try opening in new tab (Open External)
3. Check internet connection
4. Simplify dashboard in external tool
5. Consider replacing with lighter dashboard
```

---

## 11.12. Getting Help

### In-Platform Help

**Feature Tooltips:**
- Hover over (?) icons for quick explanations
- Click help buttons for detailed guides

**Error Messages:**
- Always read full error message
- Click "View Details" for more info
- Error messages suggest fixes

### Documentation

**Where to Find It:**
- Help menu (top right)
- Knowledge base articles
- Video tutorials (coming soon)

### Support Contact

**When to Contact Support:**
- Recurring upload failures
- Data doesn't look correct
- Feature not working as expected
- Need help with complex analysis
- Request new vendor format support

**What to Include:**
1. Description of issue
2. Steps to reproduce
3. Screenshot (if visual issue)
4. Sample file (if upload issue)
5. Your account email

**Response Time:**
- Standard: Within 24 hours
- Urgent: Within 4 hours
- Critical: Within 1 hour

### Training Resources

**New User Onboarding:**
- Guided tour on first login
- Interactive tutorials
- Sample data for practice

**Advanced Features:**
- Webinars (quarterly)
- Office hours (monthly)
- One-on-one training (on request)

---

## 11.13. Frequently Asked Questions

**Q: How often should I upload data?**
A: Monthly is typical. Upload when you receive vendor reports. Use APPEND mode for regular updates.

**Q: Can I upload data from multiple vendors at once?**
A: Yes! Upload each vendor file separately. System handles different formats automatically.

**Q: What happens if I accidentally use REPLACE mode?**
A: All previous data is deleted. Contact support immediately - we may be able to recover from backups.

**Q: Can I edit data after upload?**
A: Not directly in the platform. Fix your source file and re-upload using REPLACE mode.

**Q: How far back does my data go?**
A: As far back as you've uploaded. No automatic limit. Years of history supported.

**Q: Can multiple users access the same account?**
A: Each user needs their own account. Data is isolated per user for security.

**Q: Is my data secure?**
A: Yes. Bank-level encryption, user isolation, secure backups. Only you can see your data.

**Q: Can I export my data?**
A: Yes, via email reports (CSV/Excel format). Download functionality in reports section.

**Q: What if vendor changes file format?**
A: Contact support. We'll update vendor detection to handle new format.

**Q: Can I delete uploaded data?**
A: Yes. Use "Delete Upload" in Processing Status, or REPLACE mode for full reset.

**Q: Does AI Chat learn over time?**
A: It uses conversation memory during your session. Doesn't retain information between sessions for privacy.

**Q: Can I schedule automated uploads?**
A: Not currently. Manual upload required. API integration planned for future.

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, Edge (latest versions). Mobile browsers supported with limited features.

**Q: Can I use this on mobile/tablet?**
A: Yes, but optimized for desktop. Upload and chat work well on tablet. Mobile usable but limited.

**Q: What file size is the limit?**
A: 100MB per file. Contact support if you regularly need larger files.

---

## 11.14. Next Steps

**New Users:**
1. ✅ Complete first upload
2. ✅ Ask first chat question
3. ✅ Connect first dashboard
4. ✅ Review this guide's use cases
5. ✅ Set up monthly upload routine

**Experienced Users:**
- Explore advanced chat queries
- Set up multiple dashboards
- Optimize monthly workflow
- Train team members
- Request new features

**Administrators:**
- Add team members
- Establish data governance
- Create upload schedules
- Monitor usage patterns
- Provide user training

---

**Thank you for using Bibbi Analytics Platform!**

This guide will be continuously updated with new features and best practices. Your feedback helps us improve - please share suggestions with support.
