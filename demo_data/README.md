# AURORA LUXE Demo Sales Data

Demo e-commerce sales data for TaskifAI platform showcase and testing.

## Brand Story

**AURORA LUXE** is a premium Scandinavian skincare brand inspired by the natural beauty of Nordic landscapes. Our tagline "Nordic Beauty, Global Reach" reflects our commitment to bringing the purity of Scandinavian ingredients to customers worldwide.

Founded in 2019, AURORA LUXE has grown from a small Stockholm-based startup to a globally recognized brand, shipping to 10 countries across Europe, North America, and Asia-Pacific.

## Product Catalog

### Flagship Collection (2024)

1. **Hydrating Serum Arctic Dew**
   - EAN: 5901234567890
   - Price: €89.00
   - COGS: €32.00
   - Margin: 64%
   - Best seller in winter months

2. **Anti-Aging Cream Nordic Pearl**
   - EAN: 5901234567891
   - Price: €129.00
   - COGS: €48.00
   - Margin: 63%
   - Premium product, peaks during holiday season

3. **Vitamin C Booster Midnight Sun**
   - EAN: 5901234567892
   - Price: €79.00
   - COGS: €28.00
   - Margin: 65%
   - Popular in spring months

4. **Eye Treatment Fjord Essence**
   - EAN: 5901234567893
   - Price: €69.00
   - COGS: €24.00
   - Margin: 65%
   - Steady year-round performer

5. **Face Mask Aurora Glow**
   - EAN: 5901234567894
   - Price: €39.00
   - COGS: €12.00
   - Margin: 69%
   - Summer best seller

6. **Body Lotion Scandinavian Mist**
   - EAN: 5901234567895
   - Price: €49.00
   - COGS: €18.00
   - Margin: 63%
   - Winter demand driver

## Market Presence

### Geographic Distribution (10 Countries)

- **Germany** (20%) - Largest European market
- **United States** (18%) - Primary North American market
- **France** (15%) - Strong luxury segment
- **United Kingdom** (12%) - Premium retail presence
- **Canada** (10%) - Growing North American market
- **Netherlands** (8%) - Benelux hub
- **Sweden** (7%) - Home market
- **Australia** (5%) - Asia-Pacific entry point
- **Japan** (3%) - Emerging luxury market
- **Singapore** (2%) - Southeast Asian flagship

## 2024 Sales Performance

### Monthly Revenue Trajectory

| Month | Revenue | Orders | Avg Order Value |
|-------|---------|--------|-----------------|
| January | €65,017 | 631 | €103.07 |
| February | €72,165 | 698 | €103.39 |
| March | €85,024 | 839 | €101.34 |
| April | €92,124 | 903 | €102.00 |
| May | €88,175 | 841 | €104.85 |
| June | €95,062 | 961 | €98.92 |
| July | €95,126 | 923 | €103.06 |
| August | €88,115 | 900 | €97.91 |
| September | €98,061 | 882 | €111.16 |
| October | €115,010 | 1,041 | €110.48 |
| November | €135,152 | 1,244 | €108.65 |
| December | €160,300 | 1,495 | €107.22 |
| **TOTAL** | **€1,189,331** | **11,358** | **€104.71** |

### Key Metrics

- **Total Revenue**: €1,189,331
- **Total Orders**: 11,358
- **Total Units Sold**: ~14,700 units
- **Gross Profit**: €475,732 (40% margin)
- **Profit Margin**: 38-42%
- **Unique Countries**: 10
- **Average Order Value**: €104.71
- **Payment Processing**: Stripe (2.9% + €0.30 per transaction)

### Growth Story

- **Q1 Performance**: Strong start with winter skincare demand (€222K)
- **Q2 Growth**: Spring vitamin C products drive 10% increase (€275K)
- **Q3 Stability**: Summer maintenance with lighter products (€281K)
- **Q4 Surge**: Holiday season and gift sets push 47% growth (€410K)

**Year-over-Year Projection**: +146% growth from Q1 to Q4

## Demo Files

### Location
`demo_data/2024_online_sales/`

### File Naming Convention
`AURORA_LUXE_Online_2024_{MM}_{Month_Name}.xlsx`

Examples:
- `AURORA_LUXE_Online_2024_01_January.xlsx`
- `AURORA_LUXE_Online_2024_12_December.xlsx`

### File Structure

**Sheet Name**: `Orders`

**Columns**:
1. Order ID - Unique identifier (ALX-YYYY-MM-XXXX)
2. Product EAN - 13-digit barcode
3. Functional Name - Product name
4. Product Name - Display name (same as functional)
5. Quantity - Units per order (1-3)
6. Sales EUR - Revenue in Euros
7. Cost of Goods - Manufacturing cost
8. Stripe Fee - Payment processing fee
9. Order Date - ISO format (YYYY-MM-DD)
10. Country - Customer country
11. City - (Optional, mostly empty)
12. Reseller - Always "Online"

### Upload Instructions

#### For Demo Account (test@demo.com)

1. **Login to TaskifAI**
   - URL: https://demo.taskifai.com/login
   - Email: test@demo.com
   - Password: [provided separately]

2. **Navigate to Uploads**
   - Click "Uploads" in sidebar
   - Or go to: https://demo.taskifai.com/uploads

3. **Upload Files**
   - Click "Upload File" button
   - Select one or more Excel files
   - Files will be auto-detected as "online" vendor
   - Processing starts automatically via Celery

4. **Monitor Processing**
   - Watch upload status (pending → processing → completed)
   - Typical processing time: 10-30 seconds per file
   - Check for errors in upload history

5. **View Dashboard**
   - Navigate to Dashboard
   - All 8 KPIs should now show populated data
   - Charts will display 2024 trends

#### Recommended Upload Order

For best demonstration:
1. Upload January first (baseline)
2. Upload all Q1 files (Jan-Mar) to show winter trends
3. Upload remaining months chronologically
4. Or upload all 12 at once for full-year view

## Expected Dashboard KPIs

After uploading all 12 files, the dashboard should display:

### Primary KPIs (Grid)

1. **Total Revenue**: €1,189,331
   - Source: Sum of all Sales EUR

2. **Total Units**: ~14,700 units
   - Source: Sum of all Quantity

3. **Avg Price**: €80.87/unit
   - Source: Total Revenue ÷ Total Units

4. **Total Uploads**: 12 batches
   - Source: Count of completed upload_batches

5. **Gross Profit**: €475,732
   - Source: Revenue - Cost of Goods - Stripe Fees

6. **Profit Margin**: 40.0%
   - Source: (Gross Profit ÷ Revenue) × 100

7. **Unique Countries**: 10 countries
   - Source: Distinct count of Country field

8. **Order Count**: 11,358 orders
   - Source: Count of rows in ecommerce_orders table

### Charts & Analytics

- **Revenue Trend**: Shows growth from €65K (Jan) to €160K (Dec)
- **Seasonal Patterns**: Winter spike (hydration), Spring boost (Vitamin C), Holiday surge (Q4)
- **Geographic Distribution**: Top 3 markets (Germany 20%, USA 18%, France 15%)
- **Top Products**: Anti-Aging Cream and Hydrating Serum lead revenue
- **Profit Analysis**: Consistent 38-42% margins across all months

## Technical Details

### Processor

Files are processed by `backend/app/services/vendors/online_processor.py`

**Target Table**: `ecommerce_orders`

**Detection**: Auto-detected via filename keywords ("online", "ecommerce", "web") and sheet name ("Orders")

### Database Schema

```sql
CREATE TABLE ecommerce_orders (
    order_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    upload_batch_id UUID,
    product_ean VARCHAR(13),
    functional_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255),
    sales_eur DECIMAL(12, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    cost_of_goods DECIMAL(12, 2),
    stripe_fee DECIMAL(12, 2),
    order_date DATE NOT NULL,
    country VARCHAR(100),
    city VARCHAR(255),
    reseller VARCHAR(255) DEFAULT 'Online'
);
```

### KPI Calculation

All KPIs are calculated in `backend/app/services/analytics/kpis.py`:

- **Offline KPIs** (from sellout_entries2): total_revenue, total_units, avg_price, total_uploads
- **Online KPIs** (from ecommerce_orders): gross_profit, profit_margin, unique_countries, order_count

For demo data, online KPIs are the primary showcase metrics.

## Regenerating Data

To regenerate the demo files:

```bash
cd backend
source venv/bin/activate  # If using venv
python scripts/generate_online_demo_data.py
```

This will:
1. Create fresh `demo_data/2024_online_sales/` directory
2. Generate 12 new Excel files with randomized orders
3. Maintain same revenue targets and product mix
4. Apply seasonal weighting to product distribution

## Support

For issues with demo data:
1. Check file format matches expected structure
2. Verify sheet name is "Orders" (case-sensitive)
3. Ensure filename contains "online" keyword
4. Review Celery worker logs for processing errors
5. Check RLS policies for demo user access

---

**AURORA LUXE** - Where Nordic beauty meets global excellence.
