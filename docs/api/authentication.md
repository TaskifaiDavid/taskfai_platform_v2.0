# Authentication API

## Overview

The TaskifAI authentication system provides secure user registration, login, and optional two-factor authentication (TOTP-based MFA) using JWT tokens.

**Base Path**: `/api/auth`

## Authentication Flow

### Standard Login (No MFA)

```
User → POST /auth/login → JWT Token → Authenticated Requests
```

### MFA-Protected Login

```
User → POST /auth/login → Temp Token (requires_mfa: true)
     → POST /auth/login/mfa-verify (with TOTP code) → Full JWT Token → Authenticated Requests
```

## Endpoints

### Register New User

Create a new user account and receive an authentication token.

**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "analyst"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Valid email address (unique) |
| password | string | Yes | Minimum 8 characters |
| full_name | string | Yes | User's full name |
| role | string | No | Either `analyst` or `admin` (default: `analyst`) |

**Success Response** (201 Created):
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "analyst",
    "created_at": "2024-10-18T14:30:00.000Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:

`400 Bad Request` - Email already registered:
```json
{
  "detail": "Email already registered"
}
```

`422 Unprocessable Entity` - Validation error:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@company.com",
    "password": "SecurePass123!",
    "full_name": "Jane Analyst",
    "role": "analyst"
  }'
```

---

### Login

Authenticate with email and password to receive a JWT token.

**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response** (200 OK) - Standard Login:
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "analyst",
    "created_at": "2024-10-18T14:30:00.000Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK) - MFA Required:
```json
{
  "requires_mfa": true,
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Please enter your 6-digit authentication code"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Incorrect email or password"
}
```

**JWT Token Claims**:
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "analyst",
  "tenant_id": "demo",
  "subdomain": "demo",
  "exp": 1729349400,
  "iat": 1729263000
}
```

**Token Expiration**: 24 hours (1440 minutes)

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@company.com",
    "password": "SecurePass123!"
  }'
```

---

### Logout

Logout user (client should discard token).

**Endpoint**: `POST /auth/logout`

**Authentication**: Required (Bearer token)

**Success Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

**Note**: Logout is client-side. The server does not invalidate tokens. Ensure the client removes the token from storage.

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Multi-Factor Authentication (MFA)

### Enroll in MFA

Enable TOTP-based two-factor authentication for the account.

**Endpoint**: `POST /auth/mfa/enroll`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "password": "SecurePassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "secret": "JBSWY3DPEHPK3PXP",
  "backup_codes": [
    "12345678",
    "87654321",
    "11223344",
    "44332211",
    "55667788",
    "88776655",
    "99887766",
    "66778899",
    "22334455",
    "55443322"
  ]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| qr_code | string | Base64-encoded QR code image for authenticator apps |
| secret | string | TOTP secret (for manual entry) |
| backup_codes | array | 10 one-time recovery codes (store securely!) |

**Error Responses**:

`401 Unauthorized` - Invalid password:
```json
{
  "detail": "Invalid password"
}
```

`400 Bad Request` - MFA already enabled:
```json
{
  "detail": "MFA already enabled for this account"
}
```

**Supported Authenticator Apps**:
- Google Authenticator
- Authy
- Microsoft Authenticator
- 1Password
- LastPass Authenticator

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/mfa/enroll \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "SecurePass123!"}'
```

---

### Verify MFA Enrollment

Complete MFA setup by verifying a TOTP code from your authenticator app.

**Endpoint**: `POST /auth/mfa/verify-enrollment`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "code": "123456"
}
```

**Success Response** (200 OK):
```json
{
  "message": "MFA enabled successfully. Your account is now protected with two-factor authentication."
}
```

**Error Responses**:

`401 Unauthorized` - Invalid code:
```json
{
  "detail": "Invalid verification code. Please try again."
}
```

`400 Bad Request` - MFA already enabled:
```json
{
  "detail": "MFA already enabled"
}
```

`400 Bad Request` - Enrollment not started:
```json
{
  "detail": "MFA enrollment not started. Call /mfa/enroll first."
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/mfa/verify-enrollment \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

---

### Disable MFA

Disable two-factor authentication (requires password and current TOTP code).

**Endpoint**: `POST /auth/mfa/disable`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "password": "SecurePassword123!",
  "code": "123456"
}
```

**Success Response** (200 OK):
```json
{
  "message": "MFA disabled successfully"
}
```

**Error Responses**:

`401 Unauthorized` - Invalid password or code:
```json
{
  "detail": "Invalid password"
}
```
or
```json
{
  "detail": "Invalid verification code"
}
```

`400 Bad Request` - MFA not enabled:
```json
{
  "detail": "MFA is not enabled on this account"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/mfa/disable \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "SecurePass123!",
    "code": "123456"
  }'
```

---

### Get MFA Status

Check current MFA enrollment status for authenticated user.

**Endpoint**: `GET /auth/mfa/status`

**Authentication**: Required (Bearer token)

**Success Response** (200 OK):
```json
{
  "mfa_enabled": true,
  "enrolled_at": "2024-10-18T14:30:00.000Z",
  "backup_codes_remaining": 8
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| mfa_enabled | boolean | Whether MFA is enabled |
| enrolled_at | string | ISO 8601 timestamp of MFA enrollment (null if not enrolled) |
| backup_codes_remaining | integer | Number of unused backup codes |

**Example**:
```bash
curl -X GET http://localhost:8000/api/auth/mfa/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Complete MFA Login

Verify TOTP code to complete MFA-protected login.

**Endpoint**: `POST /auth/login/mfa-verify`

**Request Body**:
```json
{
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "mfa_code": "123456"
}
```

**Request Schema**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| temp_token | string | Yes | Temporary token from `/auth/login` response |
| mfa_code | string | Yes | 6-digit TOTP code from authenticator app |

**Success Response** (200 OK):
```json
{
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "analyst",
    "mfa_enabled": true,
    "created_at": "2024-10-18T14:30:00.000Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:

`401 Unauthorized` - Invalid or expired temp token:
```json
{
  "detail": "Invalid or expired MFA token"
}
```

`401 Unauthorized` - Invalid TOTP code:
```json
{
  "detail": "Invalid authentication code"
}
```

**Security Notes**:
- Temp token expires in 5 minutes
- Temp token is one-time use (JTI claim prevents reuse)
- Failed MFA attempts are logged to `mfa_attempts` table
- IP address and user agent are recorded for security auditing

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/login/mfa-verify \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "mfa_code": "123456"
  }'
```

---

## JWT Token Usage

### Including Token in Requests

Add the JWT token to the `Authorization` header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Structure

JWT tokens contain three parts (header.payload.signature):

**Decoded Payload Example**:
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "role": "analyst",
  "tenant_id": "demo",
  "subdomain": "demo",
  "exp": 1729349400,
  "iat": 1729263000
}
```

### Token Expiration

- **Standard Token**: 24 hours (1440 minutes)
- **MFA Temp Token**: 5 minutes

When a token expires, clients receive:
```json
{
  "detail": "Token has expired"
}
```

**Best Practice**: Refresh the token before expiration or implement automatic re-login.

---

## Multi-Tenant Context

### Tenant Detection

The authentication system automatically detects tenant context from:

1. **Subdomain** (preferred): `bibbi.taskifai.com` → `tenant_id="bibbi"`
2. **Header**: `X-Tenant-ID: demo`
3. **Environment Variable**: `TENANT_ID_OVERRIDE=bibbi` (for DigitalOcean deployments)

### Tenant Isolation

Each tenant has:
- Isolated user accounts
- Separate data storage
- Independent authentication

**Important**: Users from `demo` tenant cannot access `bibbi` tenant data and vice versa.

---

## Security Best Practices

### Password Requirements

- Minimum 8 characters
- No maximum length enforced
- Recommend: Include uppercase, lowercase, numbers, special characters

### Token Storage

**Recommended**:
- Store JWT tokens in memory (React state)
- Use `httpOnly` cookies for production (XSS protection)
- Never store tokens in localStorage (XSS vulnerable)

**Current Frontend Implementation**: localStorage (plan to migrate to httpOnly cookies)

### HTTPS Enforcement

- Production API enforces HTTPS
- HTTP requests are redirected to HTTPS
- Tokens should never be transmitted over unencrypted connections

### MFA Recommendations

- Enable MFA for admin accounts (mandatory)
- Enable MFA for analyst accounts (recommended)
- Store backup codes in password manager
- Generate new backup codes periodically

---

## Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid input or MFA already enabled/disabled |
| 401 | Unauthorized | Invalid credentials, expired token, or wrong TOTP code |
| 422 | Unprocessable Entity | Validation error (malformed email, weak password) |
| 500 | Internal Server Error | Database or server error |

---

## Code Examples

### Python

```python
import requests

# Register
response = requests.post('http://localhost:8000/api/auth/register', json={
    'email': 'newuser@example.com',
    'password': 'SecurePass123!',
    'full_name': 'New User',
    'role': 'analyst'
})
token = response.json()['access_token']

# Use token for authenticated request
headers = {'Authorization': f'Bearer {token}'}
kpis = requests.get('http://localhost:8000/api/analytics/kpis', headers=headers)
print(kpis.json())
```

### JavaScript

```javascript
// Login with MFA
async function loginWithMFA(email, password) {
  // Step 1: Initial login
  const loginRes = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  const loginData = await loginRes.json();

  // Step 2: Check if MFA required
  if (loginData.requires_mfa) {
    const mfaCode = prompt('Enter your 6-digit authentication code:');

    const mfaRes = await fetch('/api/auth/login/mfa-verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temp_token: loginData.temp_token,
        mfa_code: mfaCode
      })
    });

    return await mfaRes.json();
  }

  return loginData;
}

// Use the function
const { access_token } = await loginWithMFA('user@example.com', 'password');
localStorage.setItem('token', access_token);
```

### cURL

```bash
# Complete MFA enrollment workflow
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# Enroll in MFA
curl -X POST http://localhost:8000/api/auth/mfa/enroll \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password":"SecurePass123!"}' \
  | jq '.'

# Verify enrollment with TOTP code
curl -X POST http://localhost:8000/api/auth/mfa/verify-enrollment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"123456"}'
```

---

## Related Documentation

- [API Overview](./README.md)
- [Error Codes](./error-codes.md)
- [Multi-Tenant Architecture](../architecture/multi-tenant-overview.md)
- [Security Architecture](../architecture/security-architecture.md)
