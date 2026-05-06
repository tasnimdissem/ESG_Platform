# 🔒 SECURITY GUIDE - Production Deployment

## Critical Security Fixes Applied

This document outlines security improvements made to the ESG Platform to ensure production-ready deployment.

---

## 1. Secrets Management

### ✅ Fixed: Hardcoded Default Secrets

**Before:**
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
POSTGRES_PASSWORD: password  # in docker-compose.yml
```

**After:**
```python
# Backend now validates that secrets are set in production
if IS_PRODUCTION and not SECRET_KEY:
    raise ValueError("CRITICAL: SECRET_KEY must be set in production")
```

### 📋 Required Environment Variables (Production)

Set these in your `.env` file BEFORE deploying to production:

```bash
# Core secrets - REQUIRED in production
FLASK_ENV=production
SECRET_KEY=<generate-with-: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database
DATABASE_URL=postgresql://user:strong_password@db-host:5432/esg_db
POSTGRES_PASSWORD=<strong-random-password>

# JWT Configuration
JWT_SECRET_KEY=$SECRET_KEY  # Reuses SECRET_KEY

# Email/SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-app-email@gmail.com
SMTP_PASSWORD=<gmail-app-specific-password>
SMTP_USE_TLS=true

# Optional: Model storage (S3/GCS)
MODEL_S3_BUCKET=your-esg-models-bucket
MODEL_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
```

### 🛡️ Never commit `.env` to Git

```bash
# .env is already in .gitignore
```

---

## 2. Authentication: HttpOnly Cookies Instead of localStorage

### ✅ Fixed: XSS Vulnerability

**Before:**
```typescript
// INSECURE: localStorage is vulnerable to XSS attacks
localStorage.setItem('esg_token', access_token);
```

**After:**
```typescript
// SECURE: Cookies with HttpOnly flag prevent JavaScript access
response.set_cookie(
    'access_token_cookie',
    value=access_token,
    httponly=True,        # ✓ Cannot be accessed by JavaScript
    secure=True,          # ✓ HTTPS only (production)
    samesite='Strict',    # ✓ CSRF protection
    max_age=86400         # ✓ 24-hour expiration
)
```

**Frontend Changes:**
- All API calls now automatically include cookies via `credentials: 'include'`
- No manual token storage needed
- XSS attacks cannot steal the token

---

## 3. Rate Limiting Protection

### ✅ Fixed: Brute-Force & Resource Abuse

Endpoints are now protected with rate limits:

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `/api/auth/login` | 5/hour per IP | Prevent brute-force attacks |
| `/api/auth/register` | 5/hour per IP | Prevent account spam |
| `/api/auth/forgot-password` | 3/hour per IP | Prevent email spam |
| `/api/predict` | 30/hour per IP | Prevent ML model resource abuse |

**Exceeding limits returns:**
```json
{
  "error": "429 Too Many Requests",
  "message": "5 per 1 hour"
}
```

---

## 4. Input Validation with Pydantic

### ✅ Fixed: Backend Accepts Invalid Data

**Before:**
```python
# No validation - backend trusts frontend
board_diversity_pct = data.get('board_diversity_pct')  # Could be 9999!
```

**After:**
```python
# Strict validation with bounds
class PredictRequest(BaseModel):
    board_diversity_pct: float = Field(ge=0, le=100)  # 0-100% only
    carbon_emissions: float = Field(ge=0, le=1000000)  # Reasonable bounds
```

**Invalid requests are rejected with details:**
```json
{
  "error": "Invalid input data",
  "details": [
    {
      "field": "board_diversity_pct",
      "message": "ensure this value is less than or equal to 100"
    }
  ]
}
```

---

## 5. Password Reset Tokens - Dev vs Production

### ✅ Fixed: Reset Tokens Exposed in Responses

**In Development** (`FLASK_ENV=development`):
```json
{
  "message": "Reset token generated for development use.",
  "reset_token": "abc123xyz...",  // ✓ Safe for local testing
  "email_sent": false
}
```

**In Production** (`FLASK_ENV=production`):
```json
{
  "message": "Password reset email sent.",
  "reset_token": null,  // ✗ Never returned in production
  "email_sent": true
}
```

**Configuration:**
```python
RETURN_RESET_TOKEN_IN_RESPONSE = not IS_PRODUCTION  # Dev only
```

---

## 6. ML Models - Git LFS or External Storage

### ✅ Fixed: 40MB Binary Files in Repository

**Current Status:**
- Model files (`*.cbm`, `*.pkl`) are now in `.gitignore`
- No binary files committed to Git

**For Production:**

#### Option A: Git LFS (Simple)
```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "backend/model/*.cbm"
git lfs track "backend/model/*.pkl"
```

#### Option B: S3/GCS (Recommended for CI/CD)
```bash
# Models are downloaded at startup
python backend/scripts/download_models.py

# Set environment variables:
MODEL_S3_BUCKET=your-esg-models-bucket
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***
```

---

## 7. Deployment Checklist

Before deploying to production, verify:

- [ ] `FLASK_ENV=production` is set
- [ ] `SECRET_KEY` is a strong, random value (32+ characters)
- [ ] Database credentials are strong and unique
- [ ] SMTP/Email credentials are set up
- [ ] HTTPS/TLS is enabled on the domain
- [ ] `.env` file is NOT committed to Git
- [ ] Models are downloaded from external storage (not in repo)
- [ ] Rate limiting is working (test with multiple requests)
- [ ] JWT cookies are `Secure` and `HttpOnly`
- [ ] CORS is configured to allow only trusted domains
- [ ] Error messages don't expose sensitive information
- [ ] Logs are sent to a secure logging service

---

## 8. Environment Variables Reference

### Core (.env file)
```bash
FLASK_ENV=production|development
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
```

### Email
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=<app-password>
SMTP_USE_TLS=true
EMAIL_FROM=noreply@esg-platform.com
EMAIL_FROM_NAME=ESG Platform
```

### RAG (Optional)
```bash
RAG_API_BASE_URL=http://localhost:8000
RAG_ALLOW_LOCAL_FALLBACK=true
```

### Model Storage (Optional)
```bash
MODEL_S3_BUCKET=your-bucket
AWS_ACCESS_KEY_ID=***
AWS_SECRET_ACCESS_KEY=***
```

---

## 9. Monitoring & Logging

In production, monitor:

1. **Failed login attempts** - Check for brute-force patterns
2. **Rate limit hits** - Check for resource abuse
3. **Validation errors** - Check for malicious payloads
4. **JWT exceptions** - Check for tampering attempts

---

## Questions?

For security issues, please report responsibly via email instead of public issues.

