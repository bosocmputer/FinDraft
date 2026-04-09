# Deploy Plan

_Blueprint v3.2 | Updated 2026-04-09 | [← Index](README.md)_

---

## 🟢 สถานะ Deploy ปัจจุบัน (2026-04-09)

| Service | URL | Status |
|---------|-----|--------|
| Backend (Railway) | https://bountiful-freedom-production.up.railway.app | ✅ Live |
| Frontend (Vercel) | https://fin-draft-rho.vercel.app | ✅ Live |
| Database (Supabase) | ztzytgieqmuswrpneliz.supabase.co | ✅ Live |
| Redis (Railway) | redis.railway.internal:6379 | ✅ Live |

### ✅ ทำเสร็จแล้ว
- Backend deploy บน Railway (buildpack Python 3.11)
- Frontend deploy บน Vercel (Next.js 16)
- Database migrations รันครบ (13 tables)
- RLS disabled (backend handle access control แทน)
- Unique constraint บน account_mappings(project_id, account_code)
- Redis service deploy บน Railway
- CORS allow *.vercel.app ทุก subdomain
- Login / Register / Dashboard ทำงานได้
- Upload TB (Excel) ทำงานได้
- AI Mapping ทำงานได้ (OpenRouter + llama-3.3-70b)

### ⚠️ Known Issues / ยังต้องแก้
- Mapping page: ยังมี bug บางจุดที่ยังทดสอบไม่ครบ
- Editor page: draft/finalize ยังไม่ได้ทดสอบ end-to-end
- Export page: Excel/PDF export ยังไม่ได้ทดสอบ
- Register flow: user ที่สมัครก่อน fix ต้อง insert user_organizations ด้วย SQL manual
- CORS: ตอนนี้ใช้ allow_origins=["*"] ชั่วคราว — ต้องแก้ให้ specific ก่อน go live
- Supabase email confirmation ถูกปิดไว้ (ควรเปิดใน production)
- Celery worker ยังไม่ได้ deploy (mapping/draft ทำงาน sync แทน)
- PDF export ต้องการ weasyprint ซึ่งต้องใช้ Dockerfile (ยังไม่ได้เปิด)

### 🔑 Environment Variables (Railway Backend)
```env
SUPABASE_URL=https://ztzytgieqmuswrpneliz.supabase.co
SUPABASE_SERVICE_KEY=eyJ...service_role...
DATABASE_URL=postgresql://postgres:%40findraft2026@db.ztzytgieqmuswrpneliz.supabase.co:5432/postgres
AI_PROVIDER=openrouter
AI_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_API_KEY=sk-or-v1-...
AI_KEY_ENCRYPTION_SECRET=hVAqbhiGpR2iF5VrUck3pJpXrht8afpnDavv1yoU4Ss=
FRONTEND_URL=https://fin-draft-rho.vercel.app
SECRET_KEY=findraft-prod-secret-2026
REDIS_URL=redis://default:aqVchHKIE...@redis.railway.internal:6379/0
```

### 🔑 Environment Variables (Vercel Frontend)
```env
NEXT_PUBLIC_API_URL=https://bountiful-freedom-production.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://ztzytgieqmuswrpneliz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...anon...
```

---

## Architecture Overview

```
GitHub (bosocmputer/FinDraft)
  ├── push frontend/ ──→ Vercel       (auto deploy)
  └── push backend/  ──→ Railway      (auto deploy)

Users
  └── fin-draft-rho.vercel.app (Vercel)
        └── API calls ──→ bountiful-freedom-production.up.railway.app (Railway)
                              ├── PostgreSQL   (Supabase — RLS disabled, backend handles auth)
                              ├── File Storage (Supabase — tb-files, exports buckets)
                              ├── Redis        (Railway — Celery broker)
                              └── OpenRouter   (AI — llama-3.3-70b default)
```

## Services และค่าใช้จ่าย

| Service   | ใช้ทำอะไร                   | Free Tier    | Production      |
| --------- | --------------------------- | ------------ | --------------- |
| Vercel    | Host Next.js frontend       | ✅ ใช้งานได้ | $20/เดือน (Pro) |
| Railway   | Host FastAPI backend        | ✅ $5 credit | ~$10–20/เดือน   |
| Supabase  | PostgreSQL + Auth + Storage | ✅ 500MB     | $25/เดือน (Pro) |
| Anthropic | Claude API (sonnet-4-6)     | ❌           | Pay per token   |
| Redis     | Celery broker/backend       | ✅ Railway    | ~$5/เดือน       |

> ช่วง dev/test ใช้ free tier ได้หมด ค่าจริงเริ่มเมื่อ launch

## Frontend — Vercel

```bash
# 1. push code ขึ้น GitHub
git push origin main

# 2. ไป vercel.com → Import Git Repository
# 3. Root Directory: frontend/
# 4. ตั้ง Environment Variables
# 5. Add Custom Domain: findraft.app
```

**Environment Variables บน Vercel:**

```env
NEXT_PUBLIC_API_URL=https://api.findraft.app
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

**`frontend/vercel.json`:**

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.findraft.app/:path*"
    }
  ]
}
```

## Backend — Railway

**`backend/Dockerfile`:**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-tha \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    fonts-thai-tlwg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`backend/requirements.txt`:**

```
fastapi==0.111.0
uvicorn==0.30.0
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
pydantic==2.7.0
python-multipart==0.0.9
openpyxl==3.1.2
pandas==2.2.2
pdfplumber==0.11.0
pytesseract==0.3.10
xlsxwriter==3.2.0
weasyprint==62.1
# AI Providers
anthropic>=0.49.0
openai>=1.30.0
google-generativeai>=0.7.0
# Encryption (API key storage)
cryptography>=42.0.0
# Auth & Security
supabase==2.4.6
python-jose==3.3.0
slowapi==0.1.9
python-magic==0.4.27
# Background jobs
celery==5.4.0
redis==5.0.4
```

**Environment Variables บน Railway:**

```env
DATABASE_URL=postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres

# AI System Default (fallback ถ้า org ไม่ได้ตั้งค่าเอง)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

# Encryption key สำหรับ org API keys (base64-encoded 32 bytes)
# สร้างด้วย: python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
AI_KEY_ENCRYPTION_SECRET=base64_encoded_32_bytes_here

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...
FRONTEND_URL=https://findraft.app
SECRET_KEY=your-jwt-secret-key
REDIS_URL=redis://your-redis.railway.internal:6379/0
```

## Database — Supabase

```bash
# 1. supabase.com → New Project → Region: Southeast Asia (Singapore)
# 2. Copy connection string → DATABASE_URL บน Railway

npm install -g supabase
supabase login
supabase link --project-ref xxxx
supabase db push   # push migrations ทั้งหมด
```

**Storage Buckets (private ทั้งหมด):**

```
tb-files/    → ไฟล์ TB ที่อัปโหลด    (private)
exports/     → Excel/PDF ที่ export   (private, signed URL 1h)
```

## CI/CD Pipeline

**`.github/workflows/deploy.yml`:**

```yaml
name: Test & Deploy

on:
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build

# Vercel และ Railway deploy อัตโนมัติเมื่อ push ถึง main
```

## Environment Strategy

| Environment | Frontend URL                | Backend URL             | Database                    |
| ----------- | --------------------------- | ----------------------- | --------------------------- |
| Local       | localhost:3000              | localhost:8000          | Supabase dev project        |
| Staging     | findraft-staging.vercel.app | Railway staging service | Supabase staging project    |
| Production  | findraft.app                | api.findraft.app        | Supabase production project |

**`frontend/.env.local`** (ไม่ commit):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

**`backend/.env`** (ไม่ commit):

```env
DATABASE_URL=postgresql://...
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...
FRONTEND_URL=http://localhost:3000
SECRET_KEY=dev-secret-key
REDIS_URL=redis://localhost:6379/0
```

**`.gitignore` (root):**

```
frontend/.env.local
frontend/.env*.local
backend/.env
backend/.env.*
__pycache__/
.pytest_cache/
node_modules/
.next/
```

## Checklist ก่อน Go Live

```
Infrastructure
  ☐ Custom domain ตั้งค่าแล้ว (Vercel + Railway)
  ☐ SSL certificate ใช้งานได้ (auto)
  ☐ CORS เปิดเฉพาะ domain จริง (ลบ localhost ออก)
  ☐ Environment variables ครบทุกตัว (รวม ANTHROPIC_MODEL, REDIS_URL, AI_KEY_ENCRYPTION_SECRET)
  ☐ Redis service deploy แล้วบน Railway
  ☐ Celery worker deploy แล้ว (แยก service จาก FastAPI)

Database
  ☐ Migrations รันครบ (รวม user_organizations, export_history, audit_logs, jobs,
       invitations, org_ai_configs, triggers, RLS policies)
  ☐ Backup อัตโนมัติเปิดอยู่ (Supabase Pro)
  ☐ RLS เปิดทุก table (organizations, users, projects, tb_rows,
       account_mappings, financial_statements, templates, fs_comments,
       export_history, audit_logs, jobs, invitations, org_ai_configs)
  ☐ Index ครบ (idx_account_mappings_org_code, idx_projects_org, idx_audit_logs_project,
       idx_invitations_token, etc.)
  ☐ comparative_year และ currency ใน projects table
  ☐ deleted_at ใน projects table (soft delete)

Security
  ☐ API keys ไม่ถูก commit ลง Git
  ☐ Rate limiting เปิดต่อ org+user (mapping 10/min, draft 5/min, export 20/min, ai-test 5/min)
  ☐ File upload จำกัดขนาด max 20MB
  ☐ Magic bytes validation เปิด (python-magic + libmagic1 ใน Dockerfile)
  ☐ AI response sanitizer ใช้งานอยู่ทุก endpoint (รองรับทุก provider)
  ☐ Supabase Storage เป็น private (ไม่มี public URL)
  ☐ Export ใช้ signed URL (expire 1h)
  ☐ Redis URL ไม่ถูก expose (ใช้ environment variable)
  ☐ Audit log บันทึกทุก action สำคัญ (confirm mapping, edit fs, finalize, export)
  ☐ AI_KEY_ENCRYPTION_SECRET ตั้งค่าแล้ว (AES-256-GCM สำหรับ org API keys)
  ☐ org API key endpoint ไม่ return plaintext key กลับมาเด็ดขาด

Monitoring
  ☐ Vercel Analytics เปิด
  ☐ Railway Metrics ดูได้
  ☐ Sentry error tracking ติดตั้งแล้ว
```
