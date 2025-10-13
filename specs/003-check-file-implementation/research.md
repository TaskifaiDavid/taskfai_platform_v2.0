# Research: Dynamic Dashboard Configuration System

**Feature**: `003-check-file-implementation`
**Date**: 2025-10-12
**Phase**: 0 - Technology Research and Decision Making

## Research Objectives

This document captures technical decisions made for implementing a database-driven dashboard configuration system with dynamic widget rendering. All decisions prioritize flexibility, type safety, and multi-tenant security compliance.

---

## 1. Widget Configuration Storage Strategy

### Decision: **JSONB in PostgreSQL**

**Rationale**:
- Allows adding new widget types without database schema migrations
- Native JSONB indexing and querying support in PostgreSQL 17
- Type validation handled at application layer (Pydantic + TypeScript)
- Supabase provides excellent JSONB querying support
- Eliminates need for complex EAV (Entity-Attribute-Value) patterns

**Alternatives Considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **JSONB (chosen)** | Schema-less flexibility, fast queries, native PG support | Requires application-level validation | ✅ Selected |
| Separate widget tables | Strong typing at DB level, foreign keys | Requires migrations for new widgets, schema bloat | ❌ Rejected |
| Serialized JSON text | Simple to implement | No indexing, slow queries, no native validation | ❌ Rejected |
| EAV pattern | Extreme flexibility | Complex queries, poor performance, maintenance nightmare | ❌ Rejected |

**Implementation Notes**:
- Use Pydantic models to validate JSONB structure before database write
- Create GIN index on layout column for widget type queries: `CREATE INDEX idx_layout_widget_types ON dynamic_dashboard_configs USING GIN (layout);`
- TypeScript interfaces mirror Pydantic models for end-to-end type safety

---

## 2. RLS Policy Design for Multi-Level Defaults

### Decision: **Partial Unique Indexes + OR Conditions in RLS**

**Rationale**:
- Need to support both tenant-wide defaults (user_id IS NULL) and user-specific defaults
- Only one default dashboard per user OR one default per tenant (not both active simultaneously)
- RLS policies must enforce: users see their own configs + tenant defaults
- Partial unique index prevents multiple defaults at same scope level

**RLS Policy Strategy**:
```sql
-- Read policy: Users can view their own configs + tenant defaults
CREATE POLICY select_dashboard_configs ON dynamic_dashboard_configs
    FOR SELECT
    USING (
        user_id = auth.uid()  -- User's own configs
        OR
        (user_id IS NULL AND auth.uid() IS NOT NULL)  -- Tenant defaults for authenticated users
    );

-- Write policies: Users can only modify their own configs
CREATE POLICY insert_dashboard_configs ON dynamic_dashboard_configs
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY update_dashboard_configs ON dynamic_dashboard_configs
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY delete_dashboard_configs ON dynamic_dashboard_configs
    FOR DELETE
    USING (user_id = auth.uid());
```

**Unique Constraint**:
```sql
-- Ensure only one default per user
CREATE UNIQUE INDEX idx_dynamic_dashboard_configs_unique_default
    ON dynamic_dashboard_configs (user_id)
    WHERE is_default = true AND user_id IS NOT NULL;

-- Ensure only one tenant-wide default (user_id IS NULL)
CREATE UNIQUE INDEX idx_dynamic_dashboard_configs_unique_tenant_default
    ON dynamic_dashboard_configs ((user_id IS NULL))
    WHERE is_default = true AND user_id IS NULL;
```

**Alternatives Considered**:
- **Application-level enforcement**: Rejected - requires transaction locks, race conditions
- **Trigger-based validation**: Rejected - adds complexity, harder to debug
- **Single default per tenant in config table**: Rejected - doesn't support user customization

---

## 3. React Query Cache Strategy

### Decision: **5-minute staleTime + refetchOnWindowFocus**

**Rationale**:
- Dashboard configurations change infrequently (mostly read operations)
- 5-minute cache reduces backend load for repeated dashboard views
- Window focus refetch ensures users see updates after config changes
- Background refetch keeps data fresh without user interaction

**React Query Configuration**:
```typescript
export const useDashboardConfig = () => {
  return useQuery({
    queryKey: ['dashboardConfig', 'default'],
    queryFn: () => dashboardConfigAPI.getDefault(),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    retry: 2,
  });
};
```

**Alternatives Considered**:
- **No caching (staleTime: 0)**: Rejected - excessive backend requests for static data
- **Infinite cache (staleTime: Infinity)**: Rejected - users won't see config updates without manual refresh
- **Polling (refetchInterval)**: Rejected - unnecessary server load for infrequently changing data

**Cache Invalidation Strategy**:
```typescript
// Invalidate on config mutations
const mutation = useMutation({
  mutationFn: dashboardConfigAPI.update,
  onSuccess: () => {
    queryClient.invalidateQueries(['dashboardConfig']);
  },
});
```

---

## 4. Dynamic Component Rendering Pattern

### Decision: **Switch-case with Component Registry**

**Rationale**:
- Type-safe component selection based on widget type string
- Easy to extend with new widget types (add case + component)
- Centralized widget registry for documentation and tooling
- Compile-time errors for missing widget implementations

**Implementation Pattern**:
```typescript
// Widget registry for type safety
export const WIDGET_COMPONENTS = {
  kpi_grid: KPIGridWidget,
  recent_uploads: RecentUploadsWidget,
  top_products: TopProductsWidget,
  // Future widgets added here
} as const;

export type WidgetType = keyof typeof WIDGET_COMPONENTS;

// Dynamic rendering
const DynamicDashboard: React.FC<Props> = ({ config }) => {
  return (
    <div className="dashboard-grid">
      {config.layout.map((widget) => {
        const WidgetComponent = WIDGET_COMPONENTS[widget.type as WidgetType];

        if (!WidgetComponent) {
          console.error(`Unknown widget type: ${widget.type}`);
          return <ErrorWidget key={widget.id} message="Widget not found" />;
        }

        return <WidgetComponent key={widget.id} config={widget} />;
      })}
    </div>
  );
};
```

**Alternatives Considered**:
- **Dynamic imports**: Rejected - adds complexity, loading states, potential FOUC
- **Component map object**: Same as registry approach, chosen for clarity
- **Factory pattern**: Rejected - over-engineered for simple component selection
- **Lazy loading**: Deferred - premature optimization, add later if bundle size becomes issue

---

## 5. FastAPI Async Patterns for Supabase

### Decision: **Async/await with Supabase Python client**

**Rationale**:
- FastAPI is async-first framework - maximize concurrency
- Supabase Python client supports async operations
- Non-blocking I/O for database queries improves throughput
- Consistent with existing backend patterns in TaskifAI

**Endpoint Pattern**:
```python
@router.get("/default", response_model=DashboardConfigResponse)
async def get_default_dashboard_config(
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    # Non-blocking database query
    response = await supabase.table("dynamic_dashboard_configs")\
        .select("*")\
        .eq("user_id", current_user.user_id)\
        .eq("is_default", True)\
        .maybe_single()\
        .execute()

    if not response.data:
        # Fall back to tenant default
        response = await supabase.table("dynamic_dashboard_configs")\
            .select("*")\
            .is_("user_id", "null")\
            .eq("is_default", True)\
            .single()\
            .execute()

    return response.data
```

**Alternatives Considered**:
- **Synchronous blocking calls**: Rejected - wastes server resources, poor scalability
- **Threading**: Rejected - FastAPI async is more efficient than thread pools
- **Celery background tasks**: Not needed - queries are fast enough for synchronous response

---

## 6. Pydantic Validation for JSONB Schemas

### Decision: **Nested Pydantic Models with strict validation**

**Rationale**:
- Catch malformed configurations before database write
- Self-documenting API via OpenAPI schema generation
- Type coercion and validation out of the box
- Consistent validation between backend and database

**Model Structure**:
```python
class WidgetPosition(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    width: int = Field(ge=1, le=12)  # 12-column grid
    height: int = Field(ge=1)

class WidgetConfig(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(min_length=1)  # Widget type identifier
    position: WidgetPosition
    props: Dict[str, Any]  # Extensible widget-specific properties

class DashboardConfigCreate(BaseModel):
    dashboard_name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    layout: List[WidgetConfig] = Field(min_items=1)
    kpis: List[str] = []
    filters: Dict[str, Any] = {}
    is_default: bool = False
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)
```

**Alternatives Considered**:
- **JSON Schema validation**: Rejected - less Python-native, separate validation logic
- **Marshmallow**: Rejected - Pydantic integrates better with FastAPI
- **No validation**: Rejected - violates defense-in-depth principle

---

## 7. TypeScript Strict Mode Configuration

### Decision: **Enable strictNullChecks + noImplicitAny**

**Rationale**:
- Catch null/undefined errors at compile time
- Dashboard config may have optional fields - strict null checks prevent runtime errors
- Type safety matches backend Pydantic models
- Improves maintainability as widget types grow

**tsconfig.json**:
```json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

---

## 8. React Component Composition for Extensibility

### Decision: **Shared widget base component + composition**

**Rationale**:
- All widgets share common UI patterns (card container, header, loading states)
- Composition over inheritance for flexibility
- Reduces boilerplate in individual widget components
- Consistent styling and behavior across all widgets

**Base Widget Pattern**:
```typescript
export const WidgetCard: React.FC<WidgetCardProps> = ({
  title,
  loading,
  error,
  children,
  actions,
}) => {
  return (
    <div className="widget-card">
      <div className="widget-header">
        <h3>{title}</h3>
        {actions && <div className="widget-actions">{actions}</div>}
      </div>
      <div className="widget-body">
        {loading && <Spinner />}
        {error && <ErrorMessage message={error} />}
        {!loading && !error && children}
      </div>
    </div>
  );
};

// Usage in specific widget
export const KPIGridWidget: React.FC<WidgetProps> = ({ config }) => {
  const { data, loading, error } = useKPIData(config.props.kpis);

  return (
    <WidgetCard title={config.props.title || "KPIs"} loading={loading} error={error}>
      <div className="kpi-grid">
        {data?.map((kpi) => <KPICard key={kpi.name} {...kpi} />)}
      </div>
    </WidgetCard>
  );
};
```

---

## 9. OpenAPI Schema Generation

### Decision: **Auto-generate from Pydantic models via FastAPI**

**Rationale**:
- Single source of truth (Pydantic models)
- Always up-to-date with implementation
- Interactive API docs at `/docs` endpoint
- Contract tests can validate against generated schema

**FastAPI Configuration**:
```python
app = FastAPI(
    title="TaskifAI Dashboard Config API",
    description="Dynamic dashboard configuration management",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "dashboard-configs",
            "description": "Dashboard configuration CRUD operations",
        }
    ],
)
```

---

## Summary

All technical decisions prioritize:
1. **Flexibility**: JSONB storage allows widget types to evolve without migrations
2. **Type Safety**: Pydantic + TypeScript provide end-to-end validation
3. **Performance**: React Query caching + FastAPI async reduce backend load
4. **Security**: RLS policies + Pydantic validation enforce multi-tenant isolation
5. **Maintainability**: Component composition + registry pattern simplify extensions

These decisions align with TaskifAI's constitutional principles:
- ✅ Configuration-driven (JSONB layout)
- ✅ Defense-in-depth (RLS + validation layers)
- ✅ Technology stack compliance (FastAPI, React, Supabase)

**Next Phase**: Use these decisions to design data models and API contracts (Phase 1)
