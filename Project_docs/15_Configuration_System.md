# 15. Configuration System

**Configuration-driven vendor processing for tenant-specific customization**

This document explains how TaskifAI's configuration system allows each tenant to customize vendor data processing rules without requiring code changes.

---

## 15.1. Architecture Overview

### Traditional vs Configuration-Driven

**❌ Traditional Hardcoded Approach:**
```python
# Separate processor class for each vendor
class BoxnoxProcessor:
    def process(self, file):
        # Hardcoded column mappings
        product_ean = row["Product EAN"]
        quantity = row["Sold Qty"]
        # ...hardcoded logic
```

**Problems:**
- ✗ Code deployment needed for each vendor change
- ✗ Cannot customize per tenant
- ✗ Difficult to maintain and scale
- ✗ Vendor logic scattered across codebase

**✅ TaskifAI Configuration-Driven Approach:**
```python
# Single generic processor
class ConfigurableProcessor:
    def process(self, file, config: VendorConfig):
        # Load column mappings from config
        product_ean = row[config.column_mapping["product_ean"]]
        quantity = row[config.column_mapping["quantity"]]
        # Apply rules from config
```

**Benefits:**
- ✅ No code deployment for vendor changes
- ✅ Per-tenant customization
- ✅ Centralized configuration management
- ✅ Easy to test and modify

---

## 15.2. Configuration Schema

### Vendor Configuration Structure

```json
{
  "vendor_name": "boxnox",
  "tenant_id": "customer1",
  "is_active": true,
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
    "required_fields": [
      "product_ean",
      "quantity",
      "month",
      "year"
    ],
    "nullable_fields": [
      "sales_eur"
    ]
  },
  "detection_rules": {
    "filename_keywords": ["boxnox", "bnx"],
    "sheet_names": ["Sell Out by EAN"],
    "required_columns": [
      "Product EAN",
      "Sold Qty"
    ],
    "confidence_threshold": 0.7
  },
  "metadata": {
    "created_at": "2025-10-06T10:00:00Z",
    "updated_at": "2025-10-06T10:00:00Z",
    "version": "1.0",
    "notes": "Standard Boxnox configuration"
  }
}
```

---

## 15.3. Database Schema

### vendor_configs Table

```sql
CREATE TABLE vendor_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID,                    -- NULL for defaults
    vendor_name VARCHAR(100) NOT NULL,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,  -- System default config
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,                   -- User who created config

    -- Ensure one active config per vendor per tenant
    UNIQUE(tenant_id, vendor_name, is_active)
    WHERE is_active = TRUE
);

CREATE INDEX idx_vendor_configs_tenant ON vendor_configs(tenant_id);
CREATE INDEX idx_vendor_configs_vendor ON vendor_configs(vendor_name);
CREATE INDEX idx_vendor_configs_active ON vendor_configs(is_active);
```

---

## 15.4. Configuration Hierarchy

### Default → Tenant Override

```
System Default Config
        ↓
   (inherited)
        ↓
Tenant-Specific Override
        ↓
   (final config used)
```

**Example:**

**System Default (tenant_id = NULL):**
```json
{
  "vendor_name": "boxnox",
  "column_mapping": {
    "product_ean": "Product EAN",
    "quantity": "Sold Qty"
  }
}
```

**Tenant Override (tenant_id = "customer1"):**
```json
{
  "vendor_name": "boxnox",
  "column_mapping": {
    "product_ean": "Product Code",  // Different column name
    "quantity": "Qty Sold"          // Different column name
  }
}
```

**Final Config (merged):**
```json
{
  "vendor_name": "boxnox",
  "column_mapping": {
    "product_ean": "Product Code",  // From tenant override
    "quantity": "Qty Sold"          // From tenant override
  },
  // All other fields inherited from default
}
```

---

## 15.5. Configuration Loading

### Loading Logic

```python
def load_vendor_config(tenant_id: str, vendor_name: str) -> VendorConfig:
    """
    Load vendor configuration with inheritance

    Priority:
    1. Tenant-specific active config
    2. System default config
    3. Fallback to hardcoded defaults
    """

    # Try tenant-specific config
    tenant_config = db.query(
        "SELECT config_data FROM vendor_configs "
        "WHERE tenant_id = %s AND vendor_name = %s AND is_active = TRUE",
        (tenant_id, vendor_name)
    ).first()

    if tenant_config:
        return VendorConfig(**tenant_config.config_data)

    # Fallback to system default
    default_config = db.query(
        "SELECT config_data FROM vendor_configs "
        "WHERE tenant_id IS NULL AND vendor_name = %s AND is_default = TRUE",
        (vendor_name,)
    ).first()

    if default_config:
        return VendorConfig(**default_config.config_data)

    # Fallback to hardcoded defaults
    return get_hardcoded_default_config(vendor_name)
```

---

## 15.6. Configuration API

### Endpoints

**List Vendor Configurations:**
```http
GET /api/vendors/configs
Authorization: Bearer {tenant_jwt}

Response:
[
  {
    "config_id": "abc-123",
    "vendor_name": "boxnox",
    "is_active": true,
    "is_custom": false,  // Using default
    "config_data": {...}
  },
  {
    "config_id": "def-456",
    "vendor_name": "galilu",
    "is_active": true,
    "is_custom": true,   // Tenant override
    "config_data": {...}
  }
]
```

**Get Specific Configuration:**
```http
GET /api/vendors/configs/boxnox
Authorization: Bearer {tenant_jwt}

Response:
{
  "config_id": "abc-123",
  "vendor_name": "boxnox",
  "config_data": {...},
  "is_custom": false,
  "source": "system_default"
}
```

**Create/Update Tenant Configuration:**
```http
PUT /api/vendors/configs/boxnox
Authorization: Bearer {tenant_jwt}
Content-Type: application/json

{
  "column_mapping": {
    "product_ean": "Product Code",  // Override
    "quantity": "Qty Sold"          // Override
  },
  "validation_rules": {
    "ean_length": 12  // Override (different from default 13)
  }
}

Response:
{
  "config_id": "new-config-id",
  "vendor_name": "boxnox",
  "is_active": true,
  "message": "Vendor configuration updated successfully"
}
```

**Reset to Default:**
```http
DELETE /api/vendors/configs/boxnox
Authorization: Bearer {tenant_jwt}

Response:
{
  "message": "Vendor configuration reset to system default",
  "vendor_name": "boxnox"
}
```

---

## 15.7. Configuration Use Cases

### Use Case 1: Different Column Names

**Customer A (Boxnox files):**
- Column: "Product EAN" → Map to `product_ean`

**Customer B (Boxnox files):**
- Column: "Product Code" → Map to `product_ean` (different column name)

**Solution:**
```json
// Customer B override
{
  "vendor_name": "boxnox",
  "column_mapping": {
    "product_ean": "Product Code"  // Different source column
  }
}
```

### Use Case 2: Different Currency

**Customer A (Boxnox - EUR):**
```json
{
  "currency": "EUR",
  "exchange_rate": 1.0
}
```

**Customer B (Boxnox - GBP):**
```json
{
  "currency": "GBP",
  "exchange_rate": 1.17  // GBP to EUR
}
```

### Use Case 3: Custom Validation

**Customer A (Standard 13-digit EAN):**
```json
{
  "validation_rules": {
    "ean_length": 13
  }
}
```

**Customer B (12-digit UPC):**
```json
{
  "validation_rules": {
    "ean_length": 12  // Override
  }
}
```

### Use Case 4: Additional Fields

**Customer A (Standard fields):**
```json
{
  "column_mapping": {
    "product_ean": "Product EAN",
    "quantity": "Sold Qty"
  }
}
```

**Customer B (Extra tracking field):**
```json
{
  "column_mapping": {
    "product_ean": "Product EAN",
    "quantity": "Sold Qty",
    "region": "Sales Region",      // Additional field
    "sales_rep": "Sales Rep Name"  // Additional field
  }
}
```

---

## 15.8. Configuration UI (Future)

### Configuration Management Interface

```
┌─────────────────────────────────────────────┐
│  Vendor Configurations                      │
├─────────────────────────────────────────────┤
│                                             │
│  📄 Boxnox                    [Using Default]│
│  📄 Galilu                    [Customized]  │
│  📄 Skins SA                  [Using Default]│
│                                             │
│  [+ Add Custom Vendor]                      │
└─────────────────────────────────────────────┘

Click "Galilu" →

┌─────────────────────────────────────────────┐
│  Galilu Configuration              [Edit]   │
├─────────────────────────────────────────────┤
│  Column Mapping:                            │
│  • Product EAN    → "EAN Code"             │
│  • Quantity       → "Qty"                  │
│  • Sales Amount   → "Revenue PLN"          │
│                                             │
│  Validation Rules:                          │
│  • EAN Length: 13 digits                    │
│  • Month Range: 1-12                        │
│                                             │
│  Currency: PLN → EUR (Rate: 0.23)          │
│                                             │
│  [Save Changes]  [Reset to Default]        │
└─────────────────────────────────────────────┘
```

---

## 15.9. Default Configurations

### System-Provided Defaults

**Boxnox (Europe - EUR):**
```sql
INSERT INTO vendor_configs (vendor_name, config_data, is_default) VALUES
('boxnox', '{
  "currency": "EUR",
  "file_format": {"type": "excel", "sheet_name": "Sell Out by EAN"},
  "column_mapping": {
    "product_ean": "Product EAN",
    "functional_name": "Functional Name",
    "quantity": "Sold Qty",
    "sales_eur": "Sales Amount (EUR)"
  },
  "validation_rules": {
    "ean_length": 13,
    "required_fields": ["product_ean", "quantity", "month", "year"]
  }
}'::jsonb, true);
```

**Galilu (Poland - PLN):**
```sql
INSERT INTO vendor_configs (vendor_name, config_data, is_default) VALUES
('galilu', '{
  "currency": "PLN",
  "exchange_rate": 0.23,
  "file_format": {"type": "excel", "pivot_format": true},
  "column_mapping": {
    "product_ean": "EAN",
    "product_name": "Product",
    "month": "Month",
    "year": "Year"
  },
  "transformation_rules": {
    "currency_conversion": "PLN_to_EUR"
  }
}'::jsonb, true);
```

**Continue for all 9 vendors...**

---

## 15.10. Configuration Validation

### Schema Validation

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class FileFormat(BaseModel):
    type: str = Field(..., pattern="^(excel|csv)$")
    sheet_name: Optional[str] = None
    header_row: int = 0
    pivot_format: bool = False

class VendorConfig(BaseModel):
    vendor_name: str
    tenant_id: Optional[str] = None
    currency: str = "EUR"
    exchange_rate: float = 1.0
    file_format: FileFormat
    column_mapping: Dict[str, str]
    transformation_rules: Dict[str, any] = {}
    validation_rules: Dict[str, any] = {}
    detection_rules: Dict[str, any] = {}

    @validator('column_mapping')
    def validate_required_mappings(cls, v):
        required = ['product_ean', 'quantity', 'month', 'year']
        missing = [f for f in required if f not in v]
        if missing:
            raise ValueError(f"Missing required mappings: {missing}")
        return v
```

---

## 15.11. Migration Strategy

### Phase 1: Hardcoded (Current)
```python
# BoxnoxProcessor.py - Hardcoded logic
class BoxnoxProcessor:
    COLUMN_MAPPING = {
        "Product EAN": "product_ean",
        ...
    }
```

### Phase 2: Extract to Database
```sql
-- Move hardcoded configs to database
INSERT INTO vendor_configs ...
```

### Phase 3: Generic Processor
```python
# Single processor using config
class ConfigurableProcessor:
    def process(self, file, config):
        # Use config instead of hardcoded
        ...
```

### Phase 4: Tenant Overrides
```python
# Load tenant-specific config
config = load_vendor_config(tenant_id, vendor_name)
processor.process(file, config)
```

---

## 15.12. Best Practices

### ✅ DO

- Store all vendor configs in database, not code
- Use inheritance (default → tenant override)
- Validate configurations before saving
- Version configurations for rollback
- Log all configuration changes
- Test configurations before activation
- Provide sensible defaults
- Document all configuration fields

### ❌ DON'T

- Hardcode vendor logic in processor classes
- Allow tenants to break validation rules
- Store sensitive data in configs (use separate encrypted storage)
- Deploy code for simple config changes
- Mix configuration and business logic
- Allow circular dependencies in configs

---

## 15.13. Summary

TaskifAI's configuration system provides:

✅ **Flexibility**: Tenant-specific vendor processing without code changes
✅ **Scalability**: Add new vendors via configuration, not code
✅ **Maintainability**: Centralized configuration management
✅ **Safety**: Validation and inheritance prevent breaking changes
✅ **Speed**: Deploy config changes instantly, no deployment needed

The configuration-driven approach transforms vendor management from a development bottleneck into a customer self-service feature!
