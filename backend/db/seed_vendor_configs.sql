-- ============================================
-- TaskifAI - Seed Default Vendor Configurations
-- System-provided baseline configurations
-- ============================================

-- Run this script in each tenant database to seed default vendor configs

-- ============================================
-- BOXNOX (Europe - EUR)
-- ============================================

INSERT INTO vendor_configs (
    tenant_id,
    vendor_name,
    config_data,
    is_active,
    is_default
) VALUES (
    NULL,  -- System default
    'boxnox',
    '{
        "vendor_name": "boxnox",
        "currency": "EUR",
        "exchange_rate": 1.0,
        "file_format": {
            "type": "excel",
            "sheet_name": "Sell Out by EAN",
            "header_row": 0,
            "skip_rows": 0,
            "pivot_format": false
        },
        "column_mapping": {
            "product_ean": "Product EAN",
            "functional_name": "Functional Name",
            "quantity": "Sold Qty",
            "sales_eur": "Sales Amount (EUR)",
            "reseller": "Reseller",
            "month": "Month",
            "year": "Year"
        },
        "transformation_rules": {
            "currency_conversion": null,
            "date_format": "YYYY-MM-DD",
            "ean_cleanup": true,
            "price_rounding": 2
        },
        "validation_rules": {
            "ean_length": 13,
            "month_range": [1, 12],
            "year_range": [2000, 2100],
            "required_fields": ["product_ean", "quantity", "month", "year"],
            "nullable_fields": ["sales_eur"]
        },
        "detection_rules": {
            "filename_keywords": ["boxnox", "bnx"],
            "sheet_names": ["Sell Out by EAN"],
            "required_columns": ["Product EAN", "Sold Qty"],
            "confidence_threshold": 0.7
        },
        "metadata": {
            "description": "Standard Boxnox configuration for European markets",
            "version": "1.0"
        }
    }'::jsonb,
    true,
    true
) ON CONFLICT DO NOTHING;

-- ============================================
-- GALILU (Poland - PLN)
-- ============================================

INSERT INTO vendor_configs (
    tenant_id,
    vendor_name,
    config_data,
    is_active,
    is_default
) VALUES (
    NULL,
    'galilu',
    '{
        "vendor_name": "galilu",
        "currency": "PLN",
        "exchange_rate": 0.23,
        "file_format": {
            "type": "excel",
            "sheet_name": "Sheet1",
            "header_row": 0,
            "skip_rows": 0,
            "pivot_format": true
        },
        "column_mapping": {
            "product_ean": "EAN",
            "product_name": "Product",
            "month": "Month",
            "year": "Year",
            "quantity": "Qty",
            "sales_eur": "Sales"
        },
        "transformation_rules": {
            "currency_conversion": "PLN_to_EUR",
            "date_format": "YYYY-MM-DD",
            "ean_cleanup": true,
            "price_rounding": 2
        },
        "validation_rules": {
            "ean_length": 13,
            "month_range": [1, 12],
            "year_range": [2000, 2100],
            "required_fields": ["product_name", "month", "year"],
            "nullable_fields": ["product_ean", "sales_eur"]
        },
        "detection_rules": {
            "filename_keywords": ["galilu", "poland", "pl"],
            "sheet_names": ["Sheet1", "Data"],
            "required_columns": ["EAN", "Product", "Month"],
            "confidence_threshold": 0.6
        }
    }'::jsonb,
    true,
    true
) ON CONFLICT DO NOTHING;

-- ============================================
-- SKINS SA (South Africa - ZAR)
-- ============================================

INSERT INTO vendor_configs (
    tenant_id,
    vendor_name,
    config_data,
    is_active,
    is_default
) VALUES (
    NULL,
    'skins_sa',
    '{
        "vendor_name": "skins_sa",
        "currency": "ZAR",
        "exchange_rate": 0.05,
        "file_format": {
            "type": "excel",
            "sheet_name": "Sheet1",
            "header_row": 0,
            "skip_rows": 0,
            "pivot_format": false
        },
        "column_mapping": {
            "product_ean": "EAN",
            "quantity": "Qty",
            "sales_eur": "Amount",
            "order_date": "OrderDate",
            "reseller": "Reseller"
        },
        "transformation_rules": {
            "currency_conversion": "ZAR_to_EUR",
            "date_format": "YYYY-MM-DD",
            "ean_cleanup": true,
            "price_rounding": 2
        },
        "validation_rules": {
            "ean_length": 13,
            "month_range": [1, 12],
            "year_range": [2000, 2100],
            "required_fields": ["product_ean", "quantity", "order_date"],
            "nullable_fields": ["sales_eur"]
        },
        "detection_rules": {
            "filename_keywords": ["skins", "south africa", "sa", "zar"],
            "sheet_names": ["Sheet1"],
            "required_columns": ["EAN", "Qty", "OrderDate"],
            "confidence_threshold": 0.7
        }
    }'::jsonb,
    true,
    true
) ON CONFLICT DO NOTHING;

-- ============================================
-- ADDITIONAL VENDORS (Placeholders)
-- ============================================

-- CDLC
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'cdlc', '{"vendor_name": "cdlc", "currency": "EUR"}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Liberty
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'liberty', '{"vendor_name": "liberty", "currency": "GBP", "exchange_rate": 1.17}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Selfridges
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'selfridges', '{"vendor_name": "selfridges", "currency": "GBP", "exchange_rate": 1.17}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Ukraine
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'ukraine', '{"vendor_name": "ukraine", "currency": "UAH", "exchange_rate": 0.024}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Skins NL
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'skins_nl', '{"vendor_name": "skins_nl", "currency": "EUR"}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Continuity
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'continuity', '{"vendor_name": "continuity", "currency": "GBP", "exchange_rate": 1.17}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- Online/Ecommerce
INSERT INTO vendor_configs (tenant_id, vendor_name, config_data, is_active, is_default)
VALUES (NULL, 'online', '{"vendor_name": "online", "currency": "EUR"}'::jsonb, true, true)
ON CONFLICT DO NOTHING;

-- ============================================
-- VERIFICATION QUERY
-- ============================================

-- Run this to verify seeded configs
-- SELECT vendor_name, is_default, is_active
-- FROM vendor_configs
-- WHERE tenant_id IS NULL
-- ORDER BY vendor_name;
