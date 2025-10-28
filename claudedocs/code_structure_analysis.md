# Code Structure Analysis

## Vendor Processors Analysis

**Total Processors Found**: 11

| File | Lines | Code Lines | Classes | Patterns |
|------|-------|------------|---------|----------|
| liberty_processor.py | 295 | 202 | LibertyProcessor | process_method, openpyxl, error_handling |
| online_processor.py | 262 | 199 | OnlineProcessor | process_method, openpyxl, validation, error_handling |
| continuity_processor.py | 225 | 176 | ContinuityProcessor | process_method, openpyxl, validation, error_handling |
| galilu_processor.py | 207 | 169 | GaliluProcessor | process_method, openpyxl, validation, error_handling |
| boxnox_processor.py | 221 | 161 | BoxnoxProcessor | process_method, openpyxl, validation, error_handling |
| cdlc_processor.py | 201 | 157 | CDLCProcessor | process_method, openpyxl, validation, error_handling |
| skins_sa_processor.py | 197 | 157 | SkinsSAProcessor | process_method, openpyxl, validation, error_handling |
| selfridges_processor.py | 193 | 156 | SelfridgesProcessor | process_method, openpyxl, validation, error_handling |
| ukraine_processor.py | 193 | 156 | UkraineProcessor | process_method, openpyxl, validation, error_handling |
| skins_nl_processor.py | 187 | 151 | SkinsNLProcessor | process_method, openpyxl, validation, error_handling |
| demo_processor.py | 184 | 137 | DemoProcessor | process_method, openpyxl, validation, error_handling |

### Common Patterns Across Processors

- **has_process_method**: 11/11 (100%)
- **uses_openpyxl**: 11/11 (100%)
- **has_error_handling**: 11/11 (100%)
- **has_validation**: 10/11 (91%)

## API Routes Analysis

**Total Route Files**: 8

| File | Lines | Endpoints | Dependencies |
|------|-------|-----------|--------------|
| auth.py | 333 | 8 | 0 |
| dashboards.py | 248 | 7 | 14 |
| bibbi_product_mappings.py | 337 | 7 | 21 |
| uploads.py | 294 | 6 | 12 |
| dashboard_config.py | 362 | 6 | 12 |
| bibbi_uploads.py | 443 | 5 | 15 |
| analytics.py | 282 | 5 | 10 |
| chat.py | 127 | 4 | 4 |

## Potential Code Duplication

**Functions with same signature in multiple files**: 51

### `__init__(2 args)`
Found in 24 files:
- app/services/tenant_registry.py
- app/services/data_inserter.py
- app/services/file_storage.py
- app/workers/report_generator.py
- app/middleware/tenant_context.py
- app/core/bibbi.py
- app/core/bibbi.py
- app/core/db_manager.py
- app/services/analytics/sales.py
- app/services/analytics/kpis.py
- app/services/bibbi/product_service.py
- app/services/bibbi/product_mapping_service.py
- app/services/bibbi/store_service.py
- app/services/bibbi/sales_insertion_service.py
- app/services/bibbi/validation_service.py
- app/services/bibbi/staging_service.py
- app/services/ai_chat/memory.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/config_loader.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/bibbi/processors/base.py
- app/services/bibbi/processors/liberty_processor.py

### `__init__(1 args)`
Found in 12 files:
- app/workers/upload_pipeline.py
- app/core/tenant.py
- app/core/tenant_db_manager.py
- app/core/rate_limiter.py
- app/core/token_blacklist.py
- app/services/bibbi/vendor_router.py
- app/services/email/notifier.py
- app/services/email/sendgrid_client.py
- app/services/tenant/manager.py
- app/services/tenant/registry.py
- app/services/tenant/provisioner.py
- app/services/vendors/liberty_processor.py

### `_validate_ean(2 args)`
Found in 11 files:
- app/services/bibbi/product_mapping_service.py
- app/services/vendors/online_processor.py
- app/services/vendors/cdlc_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py
- app/services/bibbi/processors/base.py

### `process(4 args)`
Found in 11 files:
- app/services/vendors/online_processor.py
- app/services/vendors/cdlc_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/demo_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py
- app/services/vendors/liberty_processor.py

### `_extract_rows(2 args)`
Found in 10 files:
- app/services/vendors/online_processor.py
- app/services/vendors/cdlc_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/demo_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py

### `_transform_row(4 args)`
Found in 10 files:
- app/services/vendors/online_processor.py
- app/services/vendors/cdlc_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/demo_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py

### `_to_float(3 args)`
Found in 10 files:
- app/services/vendors/online_processor.py
- app/services/vendors/cdlc_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py
- app/services/bibbi/processors/base.py

### `_to_int(3 args)`
Found in 9 files:
- app/services/vendors/online_processor.py
- app/services/vendors/selfridges_processor.py
- app/services/vendors/skins_nl_processor.py
- app/services/vendors/boxnox_processor.py
- app/services/vendors/galilu_processor.py
- app/services/vendors/ukraine_processor.py
- app/services/vendors/skins_sa_processor.py
- app/services/vendors/continuity_processor.py
- app/services/bibbi/processors/base.py

### `get_vendor_name(1 args)`
Found in 9 files:
- app/services/bibbi/processors/cdlc_processor.py
- app/services/bibbi/processors/selfridges_processor.py
- app/services/bibbi/processors/skins_nl_processor.py
- app/services/bibbi/processors/boxnox_processor.py
- app/services/bibbi/processors/galilu_processor.py
- app/services/bibbi/processors/base.py
- app/services/bibbi/processors/skins_sa_processor.py
- app/services/bibbi/processors/liberty_processor.py
- app/services/bibbi/processors/aromateque_processor.py

### `get_currency(1 args)`
Found in 9 files:
- app/services/bibbi/processors/cdlc_processor.py
- app/services/bibbi/processors/selfridges_processor.py
- app/services/bibbi/processors/skins_nl_processor.py
- app/services/bibbi/processors/boxnox_processor.py
- app/services/bibbi/processors/galilu_processor.py
- app/services/bibbi/processors/base.py
- app/services/bibbi/processors/skins_sa_processor.py
- app/services/bibbi/processors/liberty_processor.py
- app/services/bibbi/processors/aromateque_processor.py

## DRY/YAGNI Refactoring Opportunities

### High Priority (DRY Violations)

2. **Consolidate Duplicated Functions**: 51 function signatures appear in multiple files
