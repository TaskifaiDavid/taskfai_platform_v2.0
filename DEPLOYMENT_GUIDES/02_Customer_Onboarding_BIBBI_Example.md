# Customer Onboarding Guide - BIBBI Example

## Table of Contents
1. [Onboarding Overview](#onboarding-overview)
2. [Pre-Onboarding Checklist](#pre-onboarding-checklist)
3. [Step-by-Step Onboarding Process](#step-by-step-onboarding-process)
4. [Custom Vendor Processor Configuration](#custom-vendor-processor-configuration)
5. [Data Migration & Import](#data-migration--import)
6. [User Training & Handoff](#user-training--handoff)
7. [Post-Launch Support](#post-launch-support)

---

## Onboarding Overview

### Customer Profile: BIBBI

**Business Context:**
- Fashion/beauty brand with 10+ resellers
- Mix of B2B (wholesale) and D2C (online) sales
- Each reseller provides different file formats
- Requires custom data extraction beyond demo configuration

**Technical Requirements:**
- Dedicated subdomain: `bibbi.taskifai.com`
- Isolated Supabase database
- Custom vendor processors for 10+ reseller formats
- Initial data migration from historical files
- User onboarding for 3-5 team members

**Timeline:**
- Infrastructure setup: 1 day
- Vendor processor development: 3-5 days
- Data migration: 2-3 days
- Testing & training: 2 days
- **Total: 8-12 days**

---

## Pre-Onboarding Checklist

### 1. Information Gathering

Send BIBBI this questionnaire:

```markdown
# TaskifAI Onboarding Questionnaire

## Company Information
- [ ] Company name: BIBBI
- [ ] Primary contact: [Name, Email, Phone]
- [ ] Technical contact: [Name, Email]
- [ ] Preferred subdomain: bibbi.taskifai.com
- [ ] Number of users: [Estimate]

## Reseller/Vendor Information
For each reseller, provide:
- [ ] Reseller name
- [ ] Country/region
- [ ] File format (Excel, CSV, etc.)
- [ ] Sample file (anonymized if needed)
- [ ] Upload frequency (weekly, monthly)
- [ ] Special requirements

## Data Requirements
- [ ] Historical data to migrate (date range, volume)
- [ ] Custom fields beyond standard schema
- [ ] Specific analytics/reports needed
- [ ] Integration requirements (BI tools, exports)

## Security & Compliance
- [ ] Data residency requirements
- [ ] Compliance needs (GDPR, SOC2, etc.)
- [ ] Access control requirements
```

### 2. Technical Preparation

- [ ] Provision server for `bibbi.taskifai.com`
- [ ] Create Supabase project for BIBBI
- [ ] Register domain in DNS
- [ ] Setup SSL certificate
- [ ] Prepare development environment for vendor processors

### 3. Sample File Collection

Collect **2-3 sample files** from each reseller:
- Different time periods (to validate date handling)
- Mix of high/low volume (edge cases)
- Files with edge cases (missing data, special characters)

---

## Step-by-Step Onboarding Process

### Phase 1: Infrastructure Setup (Day 1)

#### 1.1 Create Supabase Project

```bash
# Login to Supabase dashboard
# Create new project: "BIBBI Production"
# Region: Choose closest to customer
# Database password: Generate strong password

# Save credentials
BIBBI_SUPABASE_URL=https://bibbi-xyz123.supabase.co
BIBBI_SUPABASE_ANON_KEY=eyJhbGc...
BIBBI_SUPABASE_SERVICE_KEY=eyJhbGc...
```

#### 1.2 Initialize Database Schema

```bash
# Navigate to Supabase SQL Editor
# Execute backend/db/schema.sql
# Then execute backend/db/seed_vendor_configs.sql

# Verify tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

#### 1.3 Register Tenant in Registry

```sql
-- Execute in tenant registry Supabase project
INSERT INTO tenants (subdomain, display_name, database_url, database_anon_key, is_active)
VALUES (
    'bibbi',
    'BIBBI Fashion Analytics',
    'https://bibbi-xyz123.supabase.co',
    'eyJhbGc...anon-key...',
    true
);

-- Get tenant_id for next step
SELECT tenant_id FROM tenants WHERE subdomain = 'bibbi';
```

#### 1.4 Deploy Tenant Server

Follow [Infrastructure Setup Guide](./01_Infrastructure_Setup.md) section 2 (Tenant Application Server), but replace "demo" with "bibbi":

```bash
# Key changes for BIBBI:
mkdir -p /var/www/taskifai-bibbi
cd /var/www/taskifai-bibbi

# .env configuration
cat > backend/.env << EOF
APP_NAME="TaskifAI Analytics Platform - BIBBI"
SUPABASE_URL=$BIBBI_SUPABASE_URL
SUPABASE_ANON_KEY=$BIBBI_SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY=$BIBBI_SUPABASE_SERVICE_KEY
# ... other configs
EOF

# Systemd services
# taskifai-bibbi-api.service
# taskifai-bibbi-worker.service

# Nginx configuration
# /etc/nginx/sites-available/bibbi.taskifai.com
```

#### 1.5 Verify Deployment

```bash
# Health check
curl https://bibbi.taskifai.com/api/health

# Test authentication (should return 401)
curl https://bibbi.taskifai.com/api/uploads

# Central login tenant discovery
curl -X POST https://app.taskifai.com/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email": "test@bibbi.com"}'
# Should return 404 (no users yet - expected)
```

---

### Phase 2: Vendor Processor Development (Days 2-6)

#### 2.1 Analyze Reseller File Formats

For each of BIBBI's 10 resellers, document:

**Example: Reseller "Fashion Store Nordic"**

```yaml
Reseller: Fashion Store Nordic
File Format: Excel (.xlsx)
Sheet Name: "Sales Report"
Columns:
  - Article Number (maps to product_ean)
  - Product Description (maps to functional_name)
  - Store Name (maps to reseller)
  - Sale Date (format: DD/MM/YYYY)
  - Quantity Sold
  - Net Sales (EUR)
  - VAT Amount
  - Gross Sales

Special Cases:
  - Article numbers are 8 digits (not standard EAN-13)
  - Multiple rows per product per day (aggregate needed)
  - VAT included in separate column (we need net sales only)

Data Extraction Logic:
  - Primary table: ecommerce_orders (if D2C) OR sellout_entries2 (if B2B)
  - Required transformations:
    * Convert 8-digit article to EAN-13 (add prefix "00000")
    * Parse DD/MM/YYYY dates
    * Aggregate quantities by product + month
    * Use net_sales for sales_eur
```

#### 2.2 Create Custom Vendor Processors

For each reseller, create a processor following this pattern:

```bash
# Create processor file
cd backend/app/services/vendors
touch fashion_store_nordic_processor.py
```

**Template: `fashion_store_nordic_processor.py`**

```python
"""
Fashion Store Nordic vendor data processor
Customer: BIBBI
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet


class FashionStoreNordicProcessor:
    """Process Fashion Store Nordic Excel files for BIBBI"""

    TARGET_SHEET = "Sales Report"

    COLUMN_MAPPING = {
        "Article Number": "product_ean",
        "Product Description": "functional_name",
        "Store Name": "reseller",
        "Sale Date": "order_date",
        "Quantity Sold": "quantity",
        "Net Sales (EUR)": "sales_eur"
    }

    def process(
        self,
        file_path: str,
        user_id: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Process Fashion Store Nordic file

        Args:
            file_path: Path to Excel file
            user_id: User identifier
            batch_id: Batch identifier

        Returns:
            Processing result with statistics
        """
        try:
            # Load workbook
            workbook = openpyxl.load_workbook(file_path, data_only=True)

            # Check if target sheet exists
            if self.TARGET_SHEET not in workbook.sheetnames:
                raise ValueError(f"Sheet '{self.TARGET_SHEET}' not found")

            sheet = workbook[self.TARGET_SHEET]

            # Extract raw rows
            raw_rows = self._extract_rows(sheet)

            # Transform data
            transformed_rows = []
            errors = []

            for row_num, raw_row in enumerate(raw_rows, start=2):
                try:
                    transformed = self._transform_row(raw_row, user_id, batch_id)
                    if transformed:
                        transformed_rows.append(transformed)
                except Exception as e:
                    errors.append({
                        "row_number": row_num,
                        "error": str(e),
                        "raw_data": raw_row
                    })

            workbook.close()

            return {
                "total_rows": len(raw_rows),
                "successful_rows": len(transformed_rows),
                "failed_rows": len(errors),
                "transformed_data": transformed_rows,
                "errors": errors
            }

        except Exception as e:
            raise Exception(f"Failed to process Fashion Store Nordic file: {str(e)}")

    def _extract_rows(self, sheet: Worksheet) -> List[Dict[str, Any]]:
        """Extract rows from worksheet"""
        # Get headers from first row
        headers = []
        for cell in sheet[1]:
            if cell.value:
                headers.append(str(cell.value).strip())

        # Extract data rows
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue

            row_dict = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    row_dict[header] = row[idx]

            rows.append(row_dict)

        return rows

    def _transform_row(
        self,
        raw_row: Dict[str, Any],
        user_id: str,
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """Transform raw row to standardized format"""

        transformed = {
            "user_id": user_id,
            "upload_batch_id": batch_id,
        }

        # Map and transform columns
        for source_col, target_col in self.COLUMN_MAPPING.items():
            value = raw_row.get(source_col)

            if target_col == "product_ean":
                # Convert 8-digit article to EAN-13
                transformed[target_col] = self._convert_to_ean13(value)

            elif target_col == "order_date":
                # Parse DD/MM/YYYY format
                transformed[target_col] = self._parse_date(value)

            elif target_col == "quantity":
                transformed[target_col] = self._to_int(value, "Quantity")

            elif target_col == "sales_eur":
                transformed[target_col] = self._to_float(value, "Net Sales")

            else:
                transformed[target_col] = str(value) if value else None

        # Determine if this is B2B or D2C
        # Fashion Store Nordic is B2B (wholesale)
        # So we extract year/month for sellout_entries2
        order_date = transformed.get("order_date")
        if order_date:
            transformed["year"] = order_date.year
            transformed["month"] = order_date.month

        transformed["created_at"] = datetime.utcnow().isoformat()

        return transformed

    def _convert_to_ean13(self, article_number: Any) -> str:
        """Convert 8-digit article number to EAN-13"""
        if not article_number:
            raise ValueError("Article number cannot be empty")

        article_str = str(article_number).strip()

        # Remove any decimal points
        if '.' in article_str:
            article_str = article_str.split('.')[0]

        # Pad to 13 digits (add 00000 prefix)
        if len(article_str) == 8:
            return "00000" + article_str
        elif len(article_str) == 13:
            return article_str
        else:
            raise ValueError(f"Invalid article number format: {article_str}")

    def _parse_date(self, value: Any) -> datetime:
        """Parse DD/MM/YYYY date format"""
        if isinstance(value, datetime):
            return value

        if not value:
            raise ValueError("Date cannot be empty")

        date_str = str(value).strip()

        # Try DD/MM/YYYY format
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            pass

        # Try other common formats
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _to_int(self, value: Any, field_name: str) -> int:
        """Convert value to integer"""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        try:
            return int(float(value))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer for {field_name}: {value}")

    def _to_float(self, value: Any, field_name: str) -> float:
        """Convert value to float"""
        if value is None or value == "":
            return 0.0

        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid float for {field_name}: {value}")
```

#### 2.3 Register Vendor Processor in Detector

```python
# backend/app/services/vendors/detector.py

class VendorDetector:
    VENDOR_PATTERNS = {
        # ... existing patterns ...

        "fashion_store_nordic": {
            "filename_keywords": ["fashion", "nordic", "fsn"],
            "sheet_names": ["Sales Report"],
            "required_columns": ["Article Number", "Product Description", "Net Sales"]
        },

        # Add patterns for other 9 BIBBI resellers
        "reseller_2": { ... },
        "reseller_3": { ... },
        # etc.
    }
```

#### 2.4 Register Processor in Factory

```python
# backend/app/services/vendors/__init__.py

from .fashion_store_nordic_processor import FashionStoreNordicProcessor
# ... other BIBBI processor imports ...

def get_vendor_processor(vendor_name: str):
    """Get processor instance for vendor"""
    processors = {
        "demo": DemoProcessor(),
        "boxnox": BoxnoxProcessor(),
        # ... existing processors ...

        # BIBBI processors
        "fashion_store_nordic": FashionStoreNordicProcessor(),
        "reseller_2": Reseller2Processor(),
        "reseller_3": Reseller3Processor(),
        # ... remaining BIBBI processors
    }

    return processors.get(vendor_name)
```

#### 2.5 Test Each Processor

```bash
# Create test script
cat > backend/test_bibbi_processors.py << 'EOF'
"""
Test BIBBI vendor processors
"""

import sys
from pathlib import Path
from app.services.vendors.fashion_store_nordic_processor import FashionStoreNordicProcessor

def test_processor(sample_file_path: str):
    """Test processor with sample file"""
    processor = FashionStoreNordicProcessor()

    result = processor.process(
        file_path=sample_file_path,
        user_id="test-user-123",
        batch_id="test-batch-456"
    )

    print(f"Total rows: {result['total_rows']}")
    print(f"Successful: {result['successful_rows']}")
    print(f"Failed: {result['failed_rows']}")

    if result['errors']:
        print("\nErrors:")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"  Row {error['row_number']}: {error['error']}")

    if result['transformed_data']:
        print("\nSample transformed row:")
        print(result['transformed_data'][0])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_bibbi_processors.py <sample_file.xlsx>")
        sys.exit(1)

    test_processor(sys.argv[1])
EOF

# Run test
cd backend
source venv/bin/activate
python test_bibbi_processors.py /path/to/sample_fashion_store_nordic.xlsx
```

---

### Phase 3: User Setup (Day 7)

#### 3.1 Create Admin User for BIBBI

```bash
# Use registration endpoint to create first admin user
curl -X POST https://bibbi.taskifai.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@bibbi.com",
    "password": "SecurePassword123!",
    "full_name": "BIBBI Admin",
    "role": "admin"
  }'

# Save returned token and user_id
```

#### 3.2 Register Users in Tenant Registry

```sql
-- Execute in tenant registry database
-- Get tenant_id first
SELECT tenant_id FROM tenants WHERE subdomain = 'bibbi';

-- Register admin user
INSERT INTO user_tenants (tenant_id, email)
VALUES ('tenant-id-from-above', 'admin@bibbi.com');

-- Add additional team members
INSERT INTO user_tenants (tenant_id, email)
VALUES
    ('tenant-id', 'analyst1@bibbi.com'),
    ('tenant-id', 'analyst2@bibbi.com'),
    ('tenant-id', 'manager@bibbi.com');
```

#### 3.3 Setup Vendor Configurations

```sql
-- Execute in BIBBI's Supabase project
-- Insert vendor configs for BIBBI's resellers

INSERT INTO vendor_configs (vendor_name, display_name, file_format, is_active, processing_notes)
VALUES
    ('fashion_store_nordic', 'Fashion Store Nordic', 'xlsx', true, 'Sales Report sheet, DD/MM/YYYY dates'),
    ('reseller_2', 'Reseller 2 Display Name', 'xlsx', true, 'Custom format notes'),
    ('reseller_3', 'Reseller 3 Display Name', 'csv', true, 'CSV with semicolon delimiter'),
    -- ... add all 10+ resellers
ON CONFLICT (vendor_name) DO UPDATE
SET display_name = EXCLUDED.display_name,
    file_format = EXCLUDED.file_format,
    is_active = EXCLUDED.is_active,
    processing_notes = EXCLUDED.processing_notes;
```

---

### Phase 4: Data Migration (Days 8-9)

#### 4.1 Prepare Historical Data

```bash
# Create migration directory
mkdir -p /tmp/bibbi-migration
cd /tmp/bibbi-migration

# Organize historical files by reseller
mkdir -p fashion_store_nordic reseller_2 reseller_3 ...

# Copy historical files to respective directories
# Files should be named chronologically for easy processing
```

#### 4.2 Bulk Upload Script

```python
# backend/scripts/bulk_upload_bibbi.py

"""
Bulk upload historical data for BIBBI
"""

import os
import requests
from pathlib import Path
from time import sleep

API_URL = "https://bibbi.taskifai.com/api"
TOKEN = "admin-token-from-registration"
UPLOAD_DIR = "/tmp/bibbi-migration"

def upload_file(file_path: Path, vendor: str):
    """Upload single file"""
    headers = {"Authorization": f"Bearer {TOKEN}"}

    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f)}
        data = {'upload_mode': 'append'}

        response = requests.post(
            f"{API_URL}/uploads",
            headers=headers,
            files=files,
            data=data
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Uploaded {file_path.name}: batch_id={result['upload_batch_id']}")
            return result['upload_batch_id']
        else:
            print(f"✗ Failed {file_path.name}: {response.text}")
            return None

def main():
    """Upload all historical files"""
    vendors = os.listdir(UPLOAD_DIR)

    for vendor in vendors:
        vendor_dir = Path(UPLOAD_DIR) / vendor
        if not vendor_dir.is_dir():
            continue

        print(f"\n=== Processing {vendor} ===")

        files = sorted(vendor_dir.glob("*.xlsx")) + sorted(vendor_dir.glob("*.csv"))

        for file_path in files:
            batch_id = upload_file(file_path, vendor)
            if batch_id:
                # Wait for processing to complete
                sleep(5)

                # Check status
                response = requests.get(
                    f"{API_URL}/uploads/{batch_id}",
                    headers={"Authorization": f"Bearer {TOKEN}"}
                )

                if response.status_code == 200:
                    status = response.json()
                    print(f"  Status: {status['processing_status']}")
                    print(f"  Rows processed: {status['rows_processed']}")
                    print(f"  Total sales: €{status['total_sales_eur']}")

if __name__ == "__main__":
    main()
```

```bash
# Run migration
cd backend
source venv/bin/activate
python scripts/bulk_upload_bibbi.py
```

#### 4.3 Verify Migration

```bash
# Check total uploaded batches
curl -H "Authorization: Bearer $TOKEN" \
  https://bibbi.taskifai.com/api/uploads | jq '.uploads | length'

# Check total sales records
curl -H "Authorization: Bearer $TOKEN" \
  https://bibbi.taskifai.com/api/analytics/summary | jq
```

---

### Phase 5: Testing & Training (Days 10-11)

#### 5.1 Functional Testing Checklist

- [ ] **Authentication**
  - [ ] Login from app.taskifai.com redirects to bibbi.taskifai.com
  - [ ] Multi-tenant users can select BIBBI tenant
  - [ ] Logout works correctly

- [ ] **File Upload**
  - [ ] Upload one file from each reseller (10+ files)
  - [ ] Verify auto-detection works
  - [ ] Check processing status updates
  - [ ] Verify data appears in database

- [ ] **Analytics**
  - [ ] Dashboard loads with correct data
  - [ ] Charts render properly
  - [ ] Filters work (date range, reseller, product)
  - [ ] Export functionality works

- [ ] **AI Chat**
  - [ ] Ask basic queries ("total sales this year")
  - [ ] Complex queries ("top products by reseller")
  - [ ] Verify security (can't access other tenants' data)

- [ ] **Admin Functions**
  - [ ] Bulk delete works
  - [ ] User management (if implemented)
  - [ ] Dashboard configuration

#### 5.2 User Training Session

**Agenda (2 hours):**

1. **Introduction (15 min)**
   - System overview
   - Navigation walkthrough

2. **File Upload Demo (30 min)**
   - Upload process demonstration
   - How to check upload status
   - Error handling and troubleshooting

3. **Analytics Features (30 min)**
   - Dashboard overview
   - Chart interpretations
   - Using filters
   - Exporting reports

4. **AI Chat Assistant (20 min)**
   - How to ask questions
   - Example queries
   - Interpreting results

5. **Q&A and Best Practices (25 min)**

**Training Materials:**
- Screen recordings of each feature
- PDF user guide
- FAQ document
- Support contact information

---

### Phase 6: Go-Live (Day 12)

#### 6.1 Pre-Launch Checklist

- [ ] All vendor processors tested and working
- [ ] Historical data migrated successfully
- [ ] Admin user trained and comfortable
- [ ] Additional users registered
- [ ] Documentation provided
- [ ] Support channels established
- [ ] Monitoring configured
- [ ] Backup strategy in place

#### 6.2 Launch Communication

Email to BIBBI team:

```markdown
Subject: TaskifAI Platform - Ready to Launch! 🚀

Hi BIBBI Team,

Your TaskifAI platform is ready to go live!

**Access Information:**
- URL: https://bibbi.taskifai.com
- Login: Use your registered email and password
- Central Login: https://app.taskifai.com (select BIBBI)

**What's Configured:**
✅ 10+ reseller file processors
✅ Historical data migrated (2020-2024)
✅ 5 team members registered
✅ Analytics dashboard customized
✅ AI chat assistant enabled

**Next Steps:**
1. Login and verify your data
2. Upload latest sales files
3. Explore analytics dashboard
4. Try the AI chat assistant

**Support:**
- Email: support@taskifai.com
- Response time: 24 hours
- Emergency: [Phone number]

**Documentation:**
- User Guide: [Link to PDF]
- Video Tutorials: [Link to playlist]
- FAQ: [Link]

Welcome to TaskifAI!
```

---

## Post-Launch Support

### Week 1: Intensive Support

- Daily check-in calls (15 min)
- Monitor upload success rates
- Address any issues immediately
- Collect feedback for improvements

### Month 1: Regular Support

- Weekly check-in calls
- Performance monitoring
- Feature enhancement requests
- Additional training if needed

### Ongoing Support

- Email support (24-hour response)
- Monthly system health reports
- Quarterly feature updates
- Annual contract review

---

## Success Metrics

Track these KPIs for BIBBI:

1. **Adoption Metrics**
   - Daily active users
   - Files uploaded per week
   - AI chat queries per day

2. **Technical Metrics**
   - Upload success rate (target: >95%)
   - Processing time (target: <2 min per file)
   - System uptime (target: 99.5%)

3. **Business Metrics**
   - Time saved vs manual processing
   - Insights generated
   - Decisions made using platform data

---

## Troubleshooting Common Issues

### Issue: File Upload Fails

**Symptoms:** Upload stuck at "processing" or "failed"

**Solutions:**
1. Check Celery worker is running: `systemctl status taskifai-bibbi-worker`
2. Check Redis connection: `redis-cli ping`
3. Review worker logs: `journalctl -u taskifai-bibbi-worker -n 50`
4. Verify file format matches processor expectations

### Issue: Vendor Detection Fails

**Symptoms:** File uploaded but vendor shows as "unknown"

**Solutions:**
1. Review detector patterns in `detector.py`
2. Check filename keywords match
3. Verify column headers in file
4. Manually test detection: `python test_vendor_detection.py`

### Issue: Data Not Appearing in Dashboard

**Symptoms:** Upload succeeds but no data in analytics

**Solutions:**
1. Check user_id filtering in queries
2. Verify RLS policies in Supabase
3. Check date range filters
4. Review SQL query logs

---

## Next Steps

After completing BIBBI onboarding:

1. Document lessons learned
2. Update onboarding templates
3. Create reusable processor patterns
4. Build onboarding automation tools
5. Plan for next customer onboarding

**Related Guides:**
- [Vendor Processor Customization Guide](./03_Vendor_Processor_Customization.md)
- [Deployment Checklist](./04_Deployment_Checklist.md)
- [Troubleshooting Guide](./05_Troubleshooting.md)
