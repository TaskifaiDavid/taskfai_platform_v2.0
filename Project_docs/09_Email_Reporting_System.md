# 9. Email and Reporting System

This document describes the email notification and report generation capabilities that keep users informed about data processing and enable scheduled analytics delivery.

## 9.1. Core Purpose

The email and reporting system automates communication with users about upload processing and delivers scheduled analytics reports directly to their inbox.

**Key Business Value:**
- Automated notifications eliminate manual status checking
- Scheduled reports enable routine business review
- Multiple export formats (PDF, CSV, Excel) support different workflows
- Email logging provides audit trail
- Error notifications enable quick issue resolution

## 9.2. System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Trigger Events                            │
│  ┌────────────────┬────────────────┬──────────────────────┐  │
│  │ Upload         │ Processing     │ Scheduled Report     │  │
│  │ Complete       │ Failed         │ Time Reached         │  │
│  └────────┬───────┴────────┬───────┴──────────┬───────────┘  │
└───────────┼────────────────┼──────────────────┼──────────────┘
            │                │                  │
            ↓                ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│              Email Service Manager                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  • Email Queue Management                              │  │
│  │  • Template Selection & Rendering                      │  │
│  │  • Attachment Generation (PDF/CSV/Excel)               │  │
│  │  • SMTP Connection Management                          │  │
│  │  • Retry Logic & Error Handling                        │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┬───────────────────┐
         ↓                          ↓                   ↓
┌──────────────────┐    ┌──────────────────┐  ┌───────────────┐
│ Report Generator │    │  Email Logger    │  │  SMTP Server  │
│ (PDF/CSV/Excel)  │    │  (Audit Trail)   │  │  (SendGrid,   │
│                  │    │                  │  │   SMTP)       │
└──────────────────┘    └──────────────────┘  └───────────────┘
```

## 9.3. Email Notification Types

### 9.3.1. Upload Success Notification

**Trigger:** Data upload processed successfully

**Email Contents:**
- Subject: "Upload Successful: [filename]"
- Success confirmation message
- Summary statistics (rows processed, sales total, date range)
- Link to view data in dashboard
- Processing duration

**Example Email:**
```
Subject: Upload Successful: Galilu_Sales_May_2024.xlsx

Hello [User Name],

Your file "Galilu_Sales_May_2024.xlsx" has been successfully processed.

Processing Summary:
- Rows Processed: 1,234
- Total Sales: €45,678.90
- Date Range: May 1-31, 2024
- Processing Time: 12 seconds
- Vendor: Galilu (auto-detected)

View your data: [Link to Dashboard]

Best regards,
Bibbi Analytics Platform
```

### 9.3.2. Upload Failure Notification

**Trigger:** Data upload processing failed

**Email Contents:**
- Subject: "Upload Failed: [filename]"
- Error explanation
- Common causes and solutions
- Link to detailed error report
- Support contact information

**Example Email:**
```
Subject: Upload Failed: Invalid_Data.xlsx

Hello [User Name],

Your file "Invalid_Data.xlsx" could not be processed due to errors.

Error Summary:
- Total Errors: 45
- Critical Issues: Missing required columns (Product, Sales Amount)
- Warning Issues: 12 rows with invalid dates

Common Solutions:
1. Ensure file contains required columns
2. Check date formatting (YYYY-MM-DD)
3. Verify numeric fields don't contain text

View Detailed Error Report: [Link to Error Page]

Need help? Contact support@bibbi-analytics.com

Best regards,
Bibbi Analytics Platform
```

### 9.3.3. Scheduled Report

**Trigger:** Scheduled time reached (daily, weekly, monthly)

**Email Contents:**
- Subject: "[Period] Sales Report - [Date Range]"
- Executive summary of key metrics
- Attached report file (PDF/CSV/Excel)
- Charts and visualizations (PDF only)
- Period-over-period comparisons

**Example Email:**
```
Subject: Weekly Sales Report - May 13-19, 2024

Hello [User Name],

Here is your weekly sales performance report.

Key Highlights:
- Total Revenue: €23,450.75 (+12% vs last week)
- Units Sold: 1,876 (+8% vs last week)
- Top Product: Product A (€5,432.10)
- Top Reseller: Galilu (€8,901.20)

Attached Files:
- Weekly_Sales_Report_2024-05-19.pdf
- Raw_Data_Export.csv

View Interactive Dashboard: [Link]

Best regards,
Bibbi Analytics Platform
```

## 9.4. Report Generation

### 9.4.1. Report Formats

**PDF Reports:**
- Professional formatting with company branding
- Charts and visualizations
- Multi-page layout
- Executive summary + detailed tables
- Ideal for: Sharing with stakeholders, printing, presentations

**CSV Reports:**
- Raw data export
- All columns included
- UTF-8 encoding
- Ideal for: Excel analysis, data import, custom processing

**Excel Reports:**
- Formatted worksheets
- Multiple sheets (summary, details, charts)
- Formulas and conditional formatting
- Ideal for: Interactive analysis, further manipulation

### 9.4.2. Report Content

**Standard Report Sections:**

1. **Header Section**
   - Report title and period
   - Generation date and time
   - User information
   - Company branding/logo

2. **Executive Summary**
   - Total revenue
   - Units sold
   - Number of transactions
   - Period comparison (vs previous period, vs same period last year)
   - Growth percentages

3. **Sales by Reseller**
   - Table of reseller performance
   - Revenue and units per reseller
   - Market share percentages
   - Top 10 resellers

4. **Sales by Product**
   - Product performance ranking
   - Revenue and units per product
   - Top 20 products
   - Category breakdowns (if applicable)

5. **Time Analysis**
   - Sales by day/week/month
   - Trend visualization (PDF only)
   - Seasonal patterns
   - Growth trajectory

6. **Geographic Analysis (if online sales)**
   - Sales by country
   - Top cities
   - Regional performance

7. **Detailed Transaction List**
   - All individual transactions
   - Filterable and sortable (Excel)
   - Complete data export

### 9.4.3. Report Generation Process

```
Report Request Flow:

1. User Request/Schedule Trigger
   ↓
2. Query Database
   - Apply date range filter
   - Apply user-specific data isolation
   - Aggregate sales data
   ↓
3. Data Transformation
   - Calculate metrics
   - Group by reseller/product/time
   - Compute percentages and comparisons
   ↓
4. Format Selection
   - PDF: Render template with charts
   - CSV: Generate plain text
   - Excel: Create workbook with sheets
   ↓
5. File Generation
   - Write to temporary file
   - Optimize file size
   - Apply compression (if applicable)
   ↓
6. Attachment/Delivery
   - Attach to email
   - Or provide download link
   ↓
7. Cleanup
   - Delete temporary files after 24 hours
   - Log generation event
```

## 9.5. Scheduling System

### 9.5.1. Schedule Configuration

Users can configure automated report delivery:

**Frequency Options:**
- Daily (every day at specified time)
- Weekly (specific day of week)
- Monthly (first/last day of month, or specific date)
- Custom (cron expression for advanced users)

**Schedule Configuration Model:**
```
EmailSchedule:
- user_id: Who receives the report
- report_name: Custom name for the schedule
- frequency: daily | weekly | monthly | custom
- frequency_config: Day of week, time, etc.
- report_format: pdf | csv | excel
- date_range: last_7_days | last_30_days | current_month | custom
- filters: Optional filters (specific resellers, products)
- recipients: Additional email addresses (CC)
- is_active: Enable/disable schedule
```

### 9.5.2. Schedule Processing

**Background Job:**
```
Cron Job: Runs every hour

Process:
1. Query all active schedules
2. Check if schedule should run now
3. For each matching schedule:
   a. Generate report
   b. Send email with attachment
   c. Update last_run timestamp
   d. Log execution result
```

**Error Handling:**
- Retry failed email sends (up to 3 attempts)
- Send admin notification if schedule consistently fails
- Automatically disable schedule after 5 consecutive failures
- Log all failures with detailed error messages

## 9.6. Email Logging and Audit Trail

### 9.6.1. Email Log Data Model

Every email sent is logged:

```
EmailLog:
- log_id: Unique identifier
- user_id: Recipient user
- email_type: success | failure | scheduled_report
- recipient_email: Email address
- subject: Email subject line
- sent_at: Timestamp
- status: sent | failed | pending
- error_message: If failed, why
- attachment_count: Number of files attached
- attachment_size: Total size in bytes
```

### 9.6.2. Log Retention

**Retention Policy:**
- Keep logs for 90 days
- Archive logs older than 90 days to compressed storage
- Purge archives after 1 year
- Critical error logs retained indefinitely

**Use Cases:**
- Audit who received what reports when
- Troubleshoot email delivery issues
- Verify compliance with data sharing policies
- Monitor email volume and costs

## 9.7. API Endpoints

### POST /api/reports/email

Generate and send a one-time email report.

**Request:**
```json
{
  "reportType": "sales_summary",
  "dateRange": {
    "start": "2024-05-01",
    "end": "2024-05-31"
  },
  "format": "pdf",
  "recipients": ["user@example.com"],
  "includeCharts": true,
  "filters": {
    "resellers": ["Galilu", "Boxnox"],
    "products": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report sent successfully",
  "emailLog": {
    "log_id": "email_789",
    "sent_at": "2024-05-20T14:30:00Z",
    "recipients": ["user@example.com"],
    "attachment_size": 245678
  }
}
```

### POST /api/email/notification

Send a notification email (upload success/failure).

**Request:**
```json
{
  "type": "upload_success",
  "upload_id": "upload_123",
  "filename": "Galilu_Sales_May.xlsx",
  "summary": {
    "rows_processed": 1234,
    "total_sales": 45678.90,
    "processing_time": 12
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Notification sent",
  "email_sent_to": "user@example.com"
}
```

### GET /api/email/logs

Retrieve email log history.

**Query Parameters:**
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `email_type`: Filter by type
- `status`: Filter by status
- `limit`: Number of results (default 50)

**Response:**
```json
{
  "logs": [
    {
      "log_id": "email_789",
      "email_type": "scheduled_report",
      "recipient_email": "user@example.com",
      "subject": "Weekly Sales Report",
      "sent_at": "2024-05-20T09:00:00Z",
      "status": "sent",
      "attachment_count": 2
    }
  ],
  "total": 125,
  "page": 1
}
```

### POST /api/reports/generate

Generate a report without sending (download only).

**Request:**
```json
{
  "reportType": "detailed_transactions",
  "format": "excel",
  "dateRange": {
    "start": "2024-05-01",
    "end": "2024-05-31"
  }
}
```

**Response:**
```json
{
  "success": true,
  "download_url": "/downloads/report_abc123.xlsx",
  "expires_at": "2024-05-21T14:30:00Z",
  "file_size": 1234567
}
```

## 9.8. Email Templates

### 9.8.1. Template System

**Template Engine:** Jinja2 (Python) or Handlebars (JavaScript)

**Template Variables:**
```
Available in all templates:
- {{ user.name }}: User's full name
- {{ user.email }}: User's email address
- {{ platform.name }}: Application name
- {{ platform.url }}: Application URL
- {{ current_date }}: Current date/time
```

**Template Customization:**
- Company branding (logo, colors)
- Custom footer text
- Legal disclaimers
- Unsubscribe links (for scheduled reports)

### 9.8.2. Sample Template Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    /* Inline CSS for email compatibility */
    body { font-family: Arial, sans-serif; }
    .header { background: #002FA7; color: white; padding: 20px; }
    .content { padding: 20px; }
    .button { background: #002FA7; color: white; padding: 10px 20px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>{{ email.subject }}</h1>
  </div>

  <div class="content">
    <p>Hello {{ user.name }},</p>

    {{ email.body | safe }}

    {% if email.cta_url %}
    <p>
      <a href="{{ email.cta_url }}" class="button">{{ email.cta_text }}</a>
    </p>
    {% endif %}

    <p>Best regards,<br>{{ platform.name }}</p>
  </div>

  <div class="footer">
    <p><small>© 2024 Bibbi Parfum Analytics. All rights reserved.</small></p>
  </div>
</body>
</html>
```

## 9.9. SMTP Configuration

### 9.9.1. Email Service Providers

**Supported Providers:**
- SendGrid (recommended for production)
- Amazon SES
- Gmail SMTP (development only)
- Custom SMTP server

**Configuration:**
```
Environment Variables:
- SMTP_HOST: mail.example.com
- SMTP_PORT: 587 (TLS) or 465 (SSL)
- SMTP_USERNAME: api_key or username
- SMTP_PASSWORD: api_secret or password
- SMTP_FROM_EMAIL: noreply@bibbi-analytics.com
- SMTP_FROM_NAME: Bibbi Analytics Platform
```

### 9.9.2. Delivery Optimization

**Rate Limiting:**
- Max 10 emails per second (to avoid provider throttling)
- Queue emails during high-volume periods
- Prioritize failure notifications over scheduled reports

**Retry Logic:**
```
Retry Strategy:
- Attempt 1: Immediate
- Attempt 2: 5 minutes later
- Attempt 3: 30 minutes later
- After 3 failures: Mark as failed, send admin alert
```

**Bounce Handling:**
- Track hard bounces (invalid email addresses)
- Track soft bounces (temporary failures)
- Automatically disable schedules for hard-bounced addresses
- Admin dashboard for bounce management

## 9.10. Security and Privacy

### 9.10.1. Data Privacy

**Principles:**
- Only send data user owns
- Never include other users' data in reports
- Encrypt sensitive information in email logs
- Provide opt-out for all scheduled emails
- Comply with GDPR/data protection regulations

### 9.10.2. Email Content Security

**Best Practices:**
- Don't include passwords or API keys in emails
- Use secure links (HTTPS only)
- Include unsubscribe links for scheduled emails
- Limit attachment size to prevent email blocks
- Sanitize user-generated content in templates

### 9.10.3. Authentication

**Link Security:**
```
Download links for reports:
- Include signed token: /download/report.pdf?token=signed_jwt
- Expire after 24 hours
- Single-use (optional)
- User-specific (can't share link)
```

## 9.11. Performance Considerations

**Async Processing:**
- All email sending happens in background jobs
- API returns immediately (doesn't wait for email to send)
- User sees "Email queued" confirmation

**Report Generation Caching:**
- Cache generated reports for 1 hour
- If multiple users request same report within hour, reuse file
- Reduces database load and generation time

**Attachment Size Limits:**
- PDF: Max 10 MB
- CSV: Max 25 MB
- Excel: Max 15 MB
- If exceeds limit, provide download link instead of attachment

## 9.12. Monitoring and Analytics

**Email Metrics:**
- Delivery rate (% successfully sent)
- Bounce rate (% bounced emails)
- Processing time (avg time to generate report)
- Queue depth (pending emails)
- Error rate by type

**Alerts:**
- Email delivery failure rate > 5%
- Queue depth > 100 emails
- SMTP connection failures
- Scheduled report generation failures

## 9.13. Future Enhancements

1. **Webhook Integration:** Trigger emails from external events
2. **A/B Testing:** Test different email templates for engagement
3. **Rich Formatting:** Interactive charts in email body (not just PDF)
4. **SMS Notifications:** Critical alerts via text message
5. **Slack/Teams Integration:** Send reports to team channels
6. **Custom Report Builder:** User-defined report templates
7. **Delivery Preferences:** User-specific email frequency controls
8. **Mobile Push Notifications:** Alert users via mobile app
