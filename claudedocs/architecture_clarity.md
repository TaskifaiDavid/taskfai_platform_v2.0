# TaskifAI Multi-Tenant Processor Architecture

**Last Updated**: 2025-10-25
**Status**: Active Development - BIBBI Focus

---

## Executive Summary

TaskifAI is designed as a **multi-tenant SaaS platform** for sales analytics, though currently **only BIBBI tenant is implemented**. The codebase maintains dual processor directories to support future tenant isolation while sharing common infrastructure.

### Current State

- **Active Tenant**: BIBBI (fashion/beauty brand with reseller analytics)
- **Paused Tenant**: Demo (reference implementation, paused database)
- **Future Tenants**: Architecture supports additional tenants

### Key Architectural Decision

**KEEP both processor directories:**
- `/services/vendors/` → For demo tenant and future general-purpose processors
- `/services/bibbi/processors/` → For BIBBI-specific business logic and customizations

This is **intentional design**, not code duplication to be removed.

---

## Directory Structure

```
backend/app/
├── services/
│   ├── vendors/                    # General vendor processors (demo + future)
│   │   ├── base.py                # ✅ NEW: Shared base class
│   │   ├── boxnox_processor.py    # Demo tenant processor
│   │   ├── cdlc_processor.py      # Demo tenant processor
│   │   ├── galilu_processor.py    # Demo tenant processor
│   │   ├── continuity_processor.py
│   │   ├── demo_processor.py
│   │   ├── online_processor.py
│   │   ├── ukraine_processor.py
│   │   ├── selfridges_processor.py
│   │   ├── skins_nl_processor.py
│   │   ├── skins_sa_processor.py
│   │   ├── liberty_processor.py   # Legacy - BIBBI uses its own
│   │   ├── config_loader.py
│   │   └── detector.py
│   │
│   └── bibbi/
│       └── processors/             # BIBBI-specific processors
│           ├── base.py            # ✅ ENHANCED: BIBBI base with tenant logic
│           ├── aromateque_processor.py
│           ├── boxnox_processor.py
│           ├── cdlc_processor.py
│           ├── galilu_processor.py
│           ├── liberty_processor.py  # 🔥 ACTIVE DEVELOPMENT
│           ├── selfridges_processor.py
│           ├── skins_nl_processor.py
│           └── skins_sa_processor.py
│
└── utils/                          # ✅ NEW: Shared utilities (DRY)
    ├── validation.py              # Common validation logic
    └── excel.py                   # Excel parsing utilities
```

---

## Architecture Principles

### 1. Tenant Isolation

**Each tenant gets:**
- Dedicated subdomain (e.g., `bibbi.taskifai.com`, `demo.taskifai.com`)
- Isolated Supabase database instance
- Tenant-specific configuration in centralized registry
- Optional processor customizations

### 2. Shared Infrastructure

**Common across all tenants:**
- FastAPI backend application
- Celery background workers
- Redis cache/queue
- Authentication system (JWT with tenant claims)
- AI Chat engine (LangChain + OpenAI)

### 3. Processor Architecture

**Two-Layer Design:**

```
VendorProcessor (base.py)           # Shared utilities
    ↓
BibbiBseProcessor (bibbi/base.py)  # BIBBI-specific logic
    ↓
LibertyProcessor                    # Vendor-specific implementation
```

**Why Two Base Classes?**

- `VendorProcessor` (utils/vendors/base.py): Pure utility methods, no business logic
- `BibbiBseProcessor` (bibbi/processors/base.py): BIBBI tenant requirements:
  - 3-stage processing pipeline (staging → validation → approval)
  - Multi-store detection and extraction
  - Reseller sales_channel integration
  - Tenant ID injection

### 4. Code Reuse Strategy (DRY)

**Shared Utilities** (`app/utils/`):
- ✅ `validation.py`: EAN validation, type conversions, date/time validation
- ✅ `excel.py`: Workbook loading, sheet parsing, row extraction

**Base Processors** (`base.py` files):
- Excel file operations
- Common transformation patterns
- Error handling frameworks
- Currency conversion

**Vendor Processors** (individual files):
- Vendor-specific column mappings only
- Custom business rules per vendor
- Data format quirks and edge cases

---

## Multi-Tenant Routing

### Subdomain-Based Tenant Detection

```python
# Request to: https://bibbi.taskifai.com/api/uploads
# → Extracted tenant_id: "bibbi"
# → Routes to BIBBI processors

# Request to: https://demo.taskifai.com/api/uploads
# → Extracted tenant_id: "demo"
# → Routes to vendors/ processors
```

### DigitalOcean Deployment Override

For non-subdomain deployments (e.g., `*.ondigitalocean.app`):

```bash
# Environment variable overrides automatic detection
TENANT_ID_OVERRIDE=bibbi
```

This forces the backend to use BIBBI tenant regardless of URL.

---

## Processor Selection Flow

### For BIBBI Uploads

```
1. File uploaded to /api/bibbi/uploads
2. Vendor detection (detector.py)
3. Route to /services/bibbi/processors/{vendor}_processor.py
4. Uses BibbiBseProcessor base class
5. 3-stage processing pipeline
6. Inserts to BIBBI database
```

### For Demo/Future Tenants

```
1. File uploaded to /api/uploads
2. Vendor detection (detector.py)
3. Route to /services/vendors/{vendor}_processor.py
4. Uses VendorProcessor base class
5. Standard processing pipeline
6. Inserts to tenant-specific database
```

---

## When to Use Which Directory

### Use `/services/bibbi/processors/` when:

- ✅ Implementing BIBBI-specific vendor processor
- ✅ Need multi-store detection logic
- ✅ Require 3-stage validation pipeline
- ✅ Integration with BIBBI resellers table
- ✅ BIBBI tenant-specific business rules

### Use `/services/vendors/` when:

- ✅ Implementing demo tenant processor
- ✅ Creating general-purpose vendor processor
- ✅ Future tenant requirements unknown
- ✅ Standard 2-stage processing sufficient
- ✅ No tenant-specific business logic needed

---

## Current Development Status

### ✅ Completed

- Core platform infrastructure (FastAPI, Celery, Supabase)
- Multi-tenant authentication and routing
- BIBBI tenant database and configuration
- Shared utility modules (`app/utils/validation.py`, `app/utils/excel.py`)
- Enhanced base processor classes

### 🔥 Active Development

- **Liberty Processor**: BIBBI's primary vendor (ongoing work, not finished)
  - Multi-store detection implementation
  - EAN validation improvements
  - Sales insertion refinements

### ⏸️ Paused

- **Demo Tenant**: Database paused, processors remain for future use
- **Other BIBBI Vendors**: Processors exist but need rewriting when vendor data formats change

### 📋 Planned

- Additional BIBBI vendor processors (when new data formats received)
- Future tenant implementations (architecture ready)
- Processor template and generator tools

---

## Benefits of Current Architecture

### Flexibility

- Easy to add new tenants without touching existing code
- Tenant-specific customizations isolated from shared logic
- Clear separation between business logic and utilities

### Maintainability

- Single source of truth for validation logic (`app/utils/`)
- Base classes eliminate 500-800 LOC of duplication
- Clear patterns for adding new processors

### Scalability

- Each tenant gets isolated database (Supabase)
- Horizontal scaling via Celery workers
- Independent tenant deployments possible

### Development Speed

- Shared utilities accelerate processor development
- New vendor processor: ~30-50 LOC vs ~200 LOC
- Clear templates and patterns to follow

---

## Migration Path (Future)

If/when demo tenant is fully deprecated:

1. Archive `/services/vendors/` processors to `legacy/`
2. Keep `VendorProcessor` base class (still useful for future tenants)
3. Keep shared utilities (`app/utils/`) permanently
4. Document migration in this file

**Do NOT delete vendors/ directory without explicit decision that:**
- Demo tenant permanently shut down
- No future tenants planned
- All code moved to BIBBI-specific location

---

## Common Pitfalls to Avoid

### ❌ Don't:

- Delete `/services/vendors/` assuming it's "legacy" or "duplicate"
- Copy-paste code from BIBBI processors to vendors/ without using shared utilities
- Mix BIBBI-specific logic into `VendorProcessor` base class
- Create new vendor processors without inheriting from base classes

### ✅ Do:

- Use shared utilities from `app/utils/` for all common operations
- Inherit from appropriate base class (`VendorProcessor` or `BibbiBseProcessor`)
- Keep vendor-specific logic isolated to individual processor files
- Document tenant-specific requirements clearly
- Add new shared utilities when patterns emerge across multiple processors

---

## Key Contacts & Resources

- **BIBBI Tenant Details**: `/docs/deployment/02_Customer_Onboarding_BIBBI_Example.md`
- **System Architecture**: `/docs/architecture/SYSTEM_OVERVIEW.md`
- **Processor Development**: `/claudedocs/adding_vendor_processors.md` (see next doc)
- **Refactoring History**: `/docs/architecture/REFACTORING_IMPROVEMENTS.md`

---

## Questions?

**Q: Why keep both processor directories if only BIBBI is active?**
A: Platform is designed for multi-tenancy. Demo may restart, future tenants will come. Keeping vendors/ maintains architectural flexibility.

**Q: Should I use vendors/ processors as templates for BIBBI?**
A: No. Use `/services/bibbi/processors/base.py` and existing BIBBI processors as templates. Vendors/ processors may have different requirements.

**Q: When adding a new BIBBI vendor, where do I put the processor?**
A: Always in `/services/bibbi/processors/`. Never in `/services/vendors/`.

**Q: Can I move shared code from processors to utils/?**
A: Yes! That's encouraged. If you see repeated patterns across 3+ processors, extract to `app/utils/`.

---

**Last Review**: 2025-10-25 (Initial refactoring phase)
**Next Review**: After Liberty processor completion or when adding new vendor
