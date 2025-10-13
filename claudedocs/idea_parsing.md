# Dynamic Vendor Processing Architecture

## Current Pain Points
- Manual code changes in `tasks.py` for each new vendor (if/elif chain)
- Manual registration in `detector.py` VENDOR_PATTERNS dict
- Duplicate code across processors
- No template/generator for new customers
- 30+ minutes per customer onboarding

## Proposed Solution: Plugin-Based Architecture

### 1. Base Processor Class
**File**: `backend/app/services/vendors/base_processor.py`

Abstract base class with standard interface:
- Common utility methods (Excel reading, validation, error handling)
- Force implementation of: `process()`, `_transform_row()`, `detect()`
- Benefits: Consistency, reduced duplication, clear contract

### 2. Dynamic Vendor Registry
**File**: `backend/app/services/vendors/registry.py`

Auto-discover all processors in `vendors/` directory:
- No manual if/elif chains - dynamic import based on vendor name
- Single source of truth for vendor → processor mapping
- Benefits: Add new vendor = drop in file, no code changes elsewhere

### 3. Refactor Detector to Use Registry
**Update**: `backend/app/services/vendors/detector.py`

- Load patterns from processors themselves (not hardcoded dict)
- Each processor defines its own detection patterns
- Benefits: Vendor logic stays encapsulated in one file

### 4. Simplify Worker Task
**Update**: `backend/app/workers/tasks.py`

Replace:
```python
if detected_vendor == "demo":
    processor = DemoProcessor()
elif detected_vendor == "boxnox":
    processor = BoxnoxProcessor()
# ... etc
```

With:
```python
processor = vendor_registry.get_processor(detected_vendor)
```

### 5. Customer Onboarding Template
**New**: `backend/app/services/vendors/_TEMPLATE_processor.py`

Copy-paste template with TODO comments showing exactly what to configure.

### 6. CLI Tool for Customer Generation
**New**: `backend/scripts/generate_vendor.py`

```bash
python generate_vendor.py --name acme --table ecommerce_orders
```

Auto-generates processor from template with detection patterns.

## New Customer Workflow

### Option A: Manual (10 minutes)
1. Copy `_TEMPLATE_processor.py` → `acme_processor.py`
2. Fill in TODOs (detection patterns, column mapping, validation)
3. Test with sample file
4. Deploy (auto-discovered by registry)

### Option B: CLI (2 minutes)
1. Run: `python generate_vendor.py --name acme --table ecommerce_orders`
2. Customize transformations in generated file
3. Test with sample file
4. Deploy

## Benefits

✅ **Zero Worker Changes**: Never touch tasks.py again
✅ **Zero Detector Changes**: Patterns live with processors
✅ **Drop-in Vendors**: Just add file to vendors/ directory
✅ **Type Safety**: Base class enforces contract
✅ **Testability**: Each processor independently testable
✅ **Documentation**: Template shows exactly what to implement
✅ **Speed**: 2-10 minutes per new customer vs 30+ minutes today

## Implementation Steps

### Commit 1: Base Processor Class
- Create abstract base class with common utilities
- Extract shared logic from demo_processor
- Define required interface methods

### Commit 2: Dynamic Registry
- Create vendor registry with auto-discovery
- Test with existing demo/boxnox processors
- Verify dynamic loading works

### Commit 3: Refactor Detector
- Move patterns into processors
- Update detector to use registry
- Keep backward compatibility

### Commit 4: Simplify Worker
- Replace if/elif with registry lookup
- Test with all existing vendors
- Verify no regressions

### Commit 5: Templates & Tools
- Create _TEMPLATE_processor.py
- Create generate_vendor.py CLI tool
- Add documentation for onboarding

## Trade-offs

⚠️ **Initial Refactor**: ~4-6 hours upfront work
⚠️ **Testing**: Need to verify all existing vendors still work
⚠️ **Learning**: Team needs to understand new pattern (but simpler!)

## Status
- **Created**: 2025-10-12
- **Status**: Proposed, not implemented
- **Estimated ROI**: Pays off after customer #3
