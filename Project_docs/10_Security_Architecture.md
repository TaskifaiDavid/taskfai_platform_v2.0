# 10. Security Architecture

This document outlines the security patterns, authentication mechanisms, and data protection strategies employed throughout the TaskifAI multi-tenant SaaS platform.

## 10.1. Security Principles

### Core Security Goals

1. **Multi-Tenant Isolation:** Complete physical data separation between customers (database-per-tenant)
2. **Authentication:** Verify user identity before granting access
3. **Authorization:** Ensure users can only access their own data within their tenant
4. **Data Isolation:** Prevent cross-tenant and cross-user data leakage
5. **Input Validation:** Protect against injection attacks
6. **Secure Communication:** Encrypt data in transit and at rest
7. **Audit Logging:** Track security-relevant events per tenant
8. **Tenant Context Security:** Ensure subdomain→tenant_id mapping is secure and tamper-proof

### Defense in Depth

The system employs multiple layers of security:

```
Layer 0: Tenant Isolation (Physical database separation)
    ↓
Layer 1: Network Security (HTTPS, TLS, Subdomain validation)
    ↓
Layer 2: Tenant Context (Subdomain→TenantID mapping)
    ↓
Layer 3: Authentication (JWT tokens with tenant_id claim)
    ↓
Layer 4: Authorization (Tenant-specific database routing)
    ↓
Layer 5: Input Validation (SQL injection prevention)
    ↓
Layer 6: Data Encryption (At rest and in transit)
    ↓
Layer 7: Audit Logging (Per-tenant security event tracking)
```

---

## 10.2. Multi-Tenant Security Model

### Database-per-Tenant Isolation

TaskifAI implements the highest level of data isolation: **physical database separation**.

**Architecture:**
```
Tenant 1 → Supabase Project A → Database A (completely isolated)
Tenant 2 → Supabase Project B → Database B (completely isolated)
Demo    → Supabase Project Demo → Database Demo (testing)
```

**Security Benefits:**
- ✅ **Impossible Cross-Tenant Queries:** Even with SQL injection, cannot access other tenant data
- ✅ **Independent Security:** Each database has own credentials, RLS policies, encryption keys
- ✅ **Compliance:** Meets strictest data residency and isolation requirements
- ✅ **Schema Flexibility:** Tenants can have custom table structures without affecting others
- ✅ **Audit Trail:** Separate logs per tenant for compliance

### Tenant Context Security

**Subdomain to Tenant ID Mapping:**

```python
# Secure tenant resolution flow
1. Extract subdomain from request: customer1.taskifai.com → "customer1"
2. Lookup tenant_id from master tenant registry (cached, encrypted)
3. Validate tenant is active and not suspended
4. Load tenant-specific database credentials (encrypted at rest)
5. Create database connection with tenant credentials
6. Inject tenant_id into JWT token claims
7. All operations execute against tenant's database
```

**Security Measures:**
- Tenant registry stored in secure master database
- Database credentials encrypted at rest (AES-256)
- Subdomain validation (prevent subdomain spoofing)
- Tenant suspension flag for immediate access revocation
- Connection pool isolation per tenant

### Tenant Provisioning Security

**New Tenant Creation:**
```
1. Admin creates tenant via secure API endpoint (admin-only)
2. Generate unique tenant_id (UUID)
3. Create new Supabase database project
4. Generate unique database credentials (stored encrypted)
5. Run schema migration on new database
6. Seed default configurations (vendor configs, RLS policies)
7. Configure subdomain DNS mapping
8. Add tenant to registry with is_active=true
9. Audit log all provisioning steps
```

**Security Controls:**
- Only platform admins can create tenants
- Provisioning requires multi-factor authentication
- Database credentials never exposed to tenant users
- Automatic security baseline (RLS, encryption) applied
- Provisioning failures rollback completely

---

## 10.3. Authentication System

### JWT-Based Authentication

**Token Structure (Tenant-Aware):**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "user_123",
    "tenant_id": "customer1",
    "email": "user@example.com",
    "role": "analyst",
    "subdomain": "customer1",
    "exp": 1678901234
  },
  "signature": "..."
}
```

**Tenant-Specific Claims:**
- `tenant_id`: Unique identifier for the customer/tenant
- `subdomain`: Validates request origin matches token
- Both used for database routing and access control

**Authentication Flow:**

```
1. User Login Request
   POST /api/login
   Body: { "email": "user@example.com", "password": "****" }
   ↓
2. Server Validates Credentials
   - Hash password with bcrypt
   - Compare against stored hash
   - Verify account is active
   ↓
3. Generate JWT Token
   - Include user_id, email, role
   - Set expiration (e.g., 24 hours)
   - Sign with secret key
   ↓
4. Return Token to Client
   Response: { "access_token": "eyJhbGc...", "token_type": "Bearer" }
   ↓
5. Client Stores Token
   - Store in memory or secure storage
   - Include in Authorization header for requests
   ↓
6. Subsequent Requests
   Authorization: Bearer eyJhbGc...
   ↓
7. Server Validates Token
   - Verify signature
   - Check expiration
   - Extract user_id for data filtering
```

### Password Security

**Storage:**
- Passwords NEVER stored in plain text
- Hashed using bcrypt with salt rounds ≥ 12
- Hash includes random salt to prevent rainbow table attacks

**Requirements:**
- Minimum 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, special characters
- No common passwords (check against breach databases)

**Password Reset Flow:**
```
1. User requests password reset
2. System generates secure reset token
3. Token sent via email (expires in 1 hour)
4. User clicks link with token
5. User sets new password
6. Token invalidated after use
```

### Session Management

**Token Expiration:**
- Access tokens: 24 hours
- Refresh tokens: 7 days (optional)
- Reset tokens: 1 hour

**Logout:**
- Client discards token
- Optional: Token blacklist for immediate revocation
- Session invalidation on server side

**Security Headers:**
```
Authorization: Bearer <token>
X-Request-ID: <unique_id>
```

---

## 10.3. Authorization & Access Control

### Role-Based Access Control (RBAC)

**Roles:**

| Role | Permissions |
|------|-------------|
| **Analyst** | View own data, upload files, use chat, view dashboards |
| **Admin** | All analyst permissions + user management, system configuration |

**Permission Matrix:**

| Action | Analyst | Admin |
|--------|---------|-------|
| Upload files | ✅ | ✅ |
| View own sales data | ✅ | ✅ |
| View other users' data | ❌ | ❌ |
| Use AI chat | ✅ | ✅ |
| Manage dashboards | ✅ | ✅ |
| Create users | ❌ | ✅ |
| Delete users | ❌ | ✅ |
| View system logs | ❌ | ✅ |

### User Data Isolation (Within Tenant)

**Per-Tenant Database + Row Level Security:**

Each tenant has their own database with RLS policies for user-level isolation:

```sql
-- Enable RLS on table
ALTER TABLE sellout_entries2 ENABLE ROW LEVEL SECURITY;

-- Create policy for user isolation (SELECT)
CREATE POLICY "users_can_read_own_data"
ON sellout_entries2
FOR SELECT
TO authenticated
USING (user_id = auth.uid());

-- Create policy for user isolation (INSERT)
CREATE POLICY "users_can_insert_own_data"
ON sellout_entries2
FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid());

-- CORRECT: RLS automatically filters queries
SELECT * FROM sellout_entries2
WHERE month = 5 AND year = 2024;
-- Returns only rows where user_id = authenticated user's ID

-- INCORRECT: Without RLS enabled (security vulnerability)
-- All users would see all data
```

**Two-Layer Isolation:**

1. **Tenant-Level (Physical):** Each customer has separate database
   - Tenant A users → Database A
   - Tenant B users → Database B
   - **Impossible to query across tenants** even with SQL injection

2. **User-Level (RLS):** Within tenant database, users isolated by RLS
   - User 1 → Sees only their data
   - User 2 → Sees only their data
   - Automatic filtering via `auth.uid()`

**Automatic Filtering with Supabase:**

Supabase RLS automatically enforces user isolation:

```python
from supabase import create_client, Client

# Initialize Supabase client with user's auth token
supabase: Client = create_client(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=user_jwt_token  # User's authenticated token
)

# Query - RLS automatically applies user_id filter
response = supabase.table("sellout_entries2")\
    .select("*")\
    .eq("month", 5)\
    .execute()

# Only returns data where user_id = auth.uid()
# No manual WHERE user_id clause needed!
```

**Flow:**
```
API Request: GET /api/uploads
↓
Authentication Middleware extracts JWT token
↓
Supabase client initialized with user token
↓
RLS policies automatically filter by auth.uid()
↓
Only returns uploads belonging to authenticated user
```

**Multi-Tenant Data Model:**

```
users table
├── user_id (Primary Key)
└── email

sellout_entries2 table
├── id (Primary Key)
├── user_id (Foreign Key to users) ← ISOLATION KEY
├── product_ean
├── sales_eur
└── ...

ecommerce_orders table
├── order_id (Primary Key)
├── user_id (Foreign Key to users) ← ISOLATION KEY
├── product_name
└── ...

conversation_history table
├── conversation_id (Primary Key)
├── user_id (Foreign Key to users) ← ISOLATION KEY
└── ...
```

Every table with user data includes `user_id` for isolation.

---

## 10.4. AI Chat Security

### SQL Injection Prevention

**Threat:** Malicious user attempts to inject SQL via chat queries

**Example Attack:**
```
User: "Show sales'; DROP TABLE sellout_entries2; --"
```

**Protection Mechanisms:**

1. **Query Validation:**
```python
BLOCKED_PATTERNS = [
    r'DROP\s+TABLE',
    r'DELETE\s+FROM',
    r'UPDATE\s+.*SET',
    r'INSERT\s+INTO',
    r'ALTER\s+TABLE',
    r'CREATE\s+TABLE',
    r';',           # Statement separator
    r'--',          # SQL comment
    r'/\*',         # Multi-line comment start
    r'\*/',         # Multi-line comment end
    r'UNION',       # UNION attacks
    r'INTO\s+OUTFILE',  # File operations
]

def validate_query(sql_query):
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_query, re.IGNORECASE):
            raise SecurityError("Query contains prohibited SQL operations")
```

2. **Read-Only Access:**
```sql
-- Database user for AI chat has SELECT-only permissions
GRANT SELECT ON sellout_entries2 TO chat_user;
GRANT SELECT ON ecommerce_orders TO chat_user;
-- NO INSERT, UPDATE, DELETE, or DDL permissions
```

3. **Parameterized Queries:**
```python
# CORRECT: Using parameterized queries
query = "SELECT * FROM sellout_entries2 WHERE user_id = %s AND month = %s"
results = db.execute(query, (user_id, month))

# INCORRECT: String concatenation (vulnerable)
query = f"SELECT * FROM sellout_entries2 WHERE user_id = {user_id}"
```

4. **User Data Filtering:**
```python
# ALWAYS inject user_id filter into AI-generated queries
original_query = "SELECT * FROM sellout_entries2 WHERE month = 5"
secured_query = f"""
SELECT * FROM sellout_entries2
WHERE user_id = {user_id}  -- ADDED AUTOMATICALLY
AND month = 5
"""
```

### Conversation Memory Security

**Privacy:**
- Conversations stored per user
- No cross-user conversation access
- Session isolation via `session_id`

**Data Retention:**
- Conversations stored indefinitely unless user clears
- Users can clear their own history
- Admins cannot view user conversations (privacy protection)

**Sensitive Data Handling:**
- No passwords or tokens stored in conversation history
- Financial data summarized, not stored verbatim
- PII (if present) not persisted beyond session

---

## 10.5. Dashboard Security

### Iframe Sandboxing

**Sandbox Attributes:**
```html
<iframe
  src="https://external-dashboard.com/embed"
  sandbox="allow-scripts allow-same-origin allow-forms"
  title="Sales Dashboard"
/>
```

**Allowed Capabilities:**
- `allow-scripts`: JavaScript for dashboard interactivity
- `allow-same-origin`: Access to same-origin resources
- `allow-forms`: Form submission within dashboard

**Blocked Capabilities:**
- `allow-top-navigation`: Prevents hijacking parent window
- `allow-popups`: Blocks unwanted popup windows
- `allow-pointer-lock`: Prevents mouse capture
- `allow-modals`: Blocks modal dialogs

### URL Validation

**Whitelist Approach:**
```python
ALLOWED_DOMAINS = [
    'lookerstudio.google.com',
    'public.tableau.com',
    'app.powerbi.com',
    'metabase.company.com',
]

def validate_dashboard_url(url):
    parsed = urlparse(url)

    # Must be HTTPS
    if parsed.scheme != 'https':
        raise ValidationError("Dashboard URL must use HTTPS")

    # Check against whitelist (optional, based on security policy)
    if ALLOWED_DOMAINS and parsed.netloc not in ALLOWED_DOMAINS:
        raise ValidationError(f"Domain {parsed.netloc} not allowed")

    # Block localhost in production
    if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
        raise ValidationError("Localhost URLs not allowed")
```

### Authentication Token Storage

**Encrypted Storage:**
```python
from cryptography.fernet import Fernet

# Generate encryption key (stored securely)
ENCRYPTION_KEY = os.environ['DASHBOARD_ENCRYPTION_KEY']
cipher = Fernet(ENCRYPTION_KEY)

# Encrypt sensitive tokens before storing
def store_dashboard_config(config):
    if config.authentication_config:
        encrypted = cipher.encrypt(
            json.dumps(config.authentication_config).encode()
        )
        config.authentication_config_encrypted = encrypted

# Decrypt when needed
def get_dashboard_token(config):
    decrypted = cipher.decrypt(config.authentication_config_encrypted)
    return json.loads(decrypted)
```

**Token Types:**
- Bearer tokens: Encrypted before database storage
- API keys: Encrypted before database storage
- OAuth tokens: Encrypted with refresh token rotation

---

## 10.6. File Upload Security

### File Validation

**Allowed File Types:**
```python
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_upload(file):
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type {ext} not allowed")

    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValidationError(f"File size {size} exceeds {MAX_FILE_SIZE}")

    # Check for password protection
    if is_password_protected(file):
        raise ValidationError("Password-protected files not allowed")
```

### Malware Prevention

**Virus Scanning:**
```python
# Optional: Integrate with antivirus service
import clamd

def scan_file_for_malware(file_path):
    cd = clamd.ClamdUnixSocket()
    result = cd.scan(file_path)

    if result[file_path][0] == 'FOUND':
        virus_name = result[file_path][1]
        raise SecurityError(f"Malware detected: {virus_name}")
```

**File Content Validation:**
```python
# Verify file is actually Excel/CSV
import magic

def validate_file_content(file_path):
    file_type = magic.from_file(file_path, mime=True)

    ALLOWED_MIME_TYPES = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',
    }

    if file_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Invalid file content type: {file_type}")
```

### Temporary File Handling

**Secure Storage:**
```python
import tempfile
import os

# Create secure temporary file
with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
    tmp.write(uploaded_file.read())
    temp_path = tmp.name

try:
    # Process file
    process_upload(temp_path)
finally:
    # Always clean up, even if processing fails
    if os.path.exists(temp_path):
        os.remove(temp_path)
```

**Path Traversal Prevention:**
```python
import os

def safe_join(base_dir, filename):
    # Sanitize filename
    filename = os.path.basename(filename)  # Remove path components

    # Join safely
    full_path = os.path.join(base_dir, filename)

    # Verify result is within base directory
    if not full_path.startswith(os.path.abspath(base_dir)):
        raise SecurityError("Path traversal attempt detected")

    return full_path
```

---

## 10.7. Email Security

### Email Address Validation

```python
import re

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validate_email(email):
    if not re.match(EMAIL_REGEX, email):
        raise ValidationError("Invalid email address")

    # Check against disposable email domains (optional)
    if is_disposable_email(email):
        raise ValidationError("Disposable email addresses not allowed")
```

### Email Content Security

**HTML Sanitization:**
```python
import bleach

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {'a': ['href']}

def sanitize_email_content(html):
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
```

**Link Security:**
```python
def secure_download_link(resource_id, user_id):
    # Generate signed token
    token = jwt.encode({
        'resource_id': resource_id,
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY)

    return f"https://platform.com/download/{resource_id}?token={token}"
```

### Rate Limiting

**Email Sending Limits:**
```python
# Per user limits
MAX_EMAILS_PER_HOUR = 10
MAX_EMAILS_PER_DAY = 50

@rate_limit(max_calls=10, period=3600)  # 10 per hour
def send_email(user_id, recipient, subject, body):
    # Check daily limit
    today_count = get_email_count_today(user_id)
    if today_count >= MAX_EMAILS_PER_DAY:
        raise RateLimitError("Daily email limit exceeded")

    # Send email
    smtp.send(recipient, subject, body)
```

---

## 10.8. API Security

### Rate Limiting

**Per-Endpoint Limits:**
```python
RATE_LIMITS = {
    '/api/login': (5, 60),           # 5 attempts per minute
    '/api/upload': (10, 3600),        # 10 uploads per hour
    '/api/chat': (30, 60),            # 30 queries per minute
    '/api/dashboards/configs': (100, 3600),  # 100 requests per hour
}

@app.before_request
def check_rate_limit():
    endpoint = request.endpoint
    user_id = get_user_id_from_token()

    if endpoint in RATE_LIMITS:
        max_calls, period = RATE_LIMITS[endpoint]
        if is_rate_limited(user_id, endpoint, max_calls, period):
            return jsonify({'error': 'Rate limit exceeded'}), 429
```

### CORS Configuration

**Allowed Origins:**
```python
from flask_cors import CORS

ALLOWED_ORIGINS = [
    'https://app.example.com',
    'https://admin.example.com',
]

CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)
```

### Request Validation

**Input Sanitization (Pydantic v2):**
```python
from typing import Annotated
from pydantic import BaseModel, field_validator, Field

class UploadRequest(BaseModel):
    filename: Annotated[str, Field(min_length=1, max_length=255)]
    mode: Annotated[str, Field(pattern="^(append|replace)$")]

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        # Remove path components
        v = os.path.basename(v)

        # Check for suspicious patterns
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename")

        return v

# FastAPI usage with dependency injection
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/upload")
async def upload_file(
    request: UploadRequest,
    token: Annotated[str, Depends(security)]
):
    # FastAPI automatically validates request body
    # Pydantic v2 provides enhanced validation
    ...
```

---

## 10.9. Data Encryption

### Encryption at Rest

**Database Encryption:**
- Full database encryption using database-native encryption
- Transparent Data Encryption (TDE) for database files
- Encrypted backups

**Sensitive Field Encryption:**
```python
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)

    def encrypt(self, value):
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, encrypted_value):
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Encrypt dashboard authentication configs
dashboard_config.auth_token = encrypted_field.encrypt(token)
```

### Encryption in Transit

**HTTPS/TLS:**
- All API communication over HTTPS
- TLS 1.2 or higher
- Strong cipher suites only

**Certificate Management:**
```
- Use valid SSL certificates (Let's Encrypt, commercial CA)
- Automatic renewal before expiration
- HSTS header to enforce HTTPS
```

**Security Headers:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## 10.10. Audit Logging

### Security Event Logging

**Logged Events:**
```python
SECURITY_EVENTS = [
    'user_login',
    'user_logout',
    'login_failed',
    'password_reset_requested',
    'password_changed',
    'unauthorized_access_attempt',
    'data_access',
    'data_modification',
    'file_upload',
    'dashboard_created',
    'dashboard_deleted',
    'email_sent',
]

def log_security_event(event_type, user_id, details):
    security_log.write({
        'timestamp': datetime.utcnow(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'details': details,
    })
```

**Audit Log Protection:**
- Append-only (no deletion or modification)
- Encrypted storage
- Regular backups
- Retention period: 1 year minimum

### Failed Login Tracking

**Account Lockout:**
```python
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

def handle_failed_login(email):
    attempts = get_failed_attempts(email)
    attempts += 1

    if attempts >= MAX_FAILED_ATTEMPTS:
        lock_account(email, duration=LOCKOUT_DURATION)
        log_security_event('account_locked', email, {
            'reason': 'Too many failed login attempts'
        })
        raise AccountLockedError("Account temporarily locked")

    set_failed_attempts(email, attempts)
```

---

## 10.11. Vulnerability Management

### Dependency Scanning

**Regular Updates:**
```bash
# Scan for known vulnerabilities
pip-audit
npm audit

# Update dependencies with security patches
pip install --upgrade <package>
npm update
```

**Automated Scanning:**
- GitHub Dependabot alerts
- Snyk vulnerability scanning
- OWASP Dependency-Check

### Security Testing

**Penetration Testing:**
- Annual third-party security audit
- Internal security reviews quarterly
- Vulnerability disclosure program

**Common Vulnerabilities Tested:**
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Authentication bypass
- Session hijacking
- File upload vulnerabilities
- API abuse

---

## 10.12. Compliance & Data Privacy

### GDPR Compliance

**User Rights:**
- Right to access: Users can export their data
- Right to deletion: Users can request account deletion
- Right to portability: Data export in standard formats
- Right to be forgotten: Complete data removal

**Data Processing:**
```python
def export_user_data(user_id):
    return {
        'sales_data': get_all_sales(user_id),
        'uploads': get_all_uploads(user_id),
        'conversations': get_all_conversations(user_id),
        'dashboards': get_all_dashboards(user_id),
    }

def delete_user_account(user_id):
    # Delete all user data
    delete_sales_data(user_id)
    delete_uploads(user_id)
    delete_conversations(user_id)
    delete_dashboards(user_id)
    delete_user(user_id)

    log_security_event('account_deleted', user_id, {
        'deletion_timestamp': datetime.utcnow()
    })
```

### Data Retention

**Retention Policies:**
- Sales data: Retained until user requests deletion
- Upload history: 90 days
- Conversation history: Until user clears
- Email logs: 90 days
- Security logs: 1 year
- Deleted data: Permanently erased after 30-day grace period

---

## 10.13. Incident Response

### Security Incident Procedure

**Detection:**
1. Automated monitoring alerts
2. User reports
3. Security audit findings

**Response:**
1. Assess severity and impact
2. Contain the incident
3. Investigate root cause
4. Remediate vulnerability
5. Document incident
6. Notify affected users (if required)

**Notification Requirements:**
- Data breach: Notify users within 72 hours
- Service disruption: Immediate notification
- Security vulnerability: After patching

---

## 10.14. Security Best Practices Summary

### Development

- ✅ Never commit secrets to version control
- ✅ Use environment variables for configuration
- ✅ Implement input validation everywhere
- ✅ Use parameterized queries (never string concatenation)
- ✅ Apply principle of least privilege
- ✅ Keep dependencies updated

### Deployment

- ✅ Use HTTPS everywhere
- ✅ Enable database encryption
- ✅ Configure firewall rules
- ✅ Regular security updates
- ✅ Monitor security logs
- ✅ Backup data regularly

### Operations

- ✅ Regular security audits
- ✅ Penetration testing
- ✅ Vulnerability scanning
- ✅ Incident response drills
- ✅ Security training for team
- ✅ Documentation updates

---

## 10.15. Security Checklist

**Authentication:**
- [ ] JWT tokens with expiration
- [ ] Passwords hashed with bcrypt
- [ ] Secure password reset flow
- [ ] Account lockout after failed attempts

**Authorization:**
- [ ] User data isolation enforced
- [ ] Role-based access control
- [ ] Permission checks on all endpoints

**Data Protection:**
- [ ] HTTPS/TLS enforced
- [ ] Database encryption enabled
- [ ] Sensitive fields encrypted
- [ ] Secure file storage

**Input Validation:**
- [ ] SQL injection prevention
- [ ] File upload validation
- [ ] Email address validation
- [ ] URL validation for dashboards

**Monitoring:**
- [ ] Security event logging
- [ ] Failed login tracking
- [ ] Audit trail for data access
- [ ] Alert system configured

**Compliance:**
- [ ] GDPR data export capability
- [ ] User deletion workflow
- [ ] Data retention policies
- [ ] Privacy policy published

---

**Security is an ongoing process. This architecture provides the foundation, but requires continuous monitoring, testing, and updates to remain effective against evolving threats.**
