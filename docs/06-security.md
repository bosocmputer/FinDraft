# Security

_Blueprint v3.2 | [← Index](README.md)_

---

## File Upload

- ตรวจ magic bytes (python-magic) ไม่ใช่แค่ extension
- จำกัด 20MB per file
- Reject ทันทีถ้า content ไม่ตรง extension

## AI Response Sanitizer

- `sanitize_and_parse_json()` ทุกครั้งก่อนใช้ output จาก AI provider (รองรับทุก provider)
- Validate category enum (whitelist)
- Clamp confidence 0.0–1.0
- Strip special chars จาก text fields (ป้องกัน injection)
- Reject ถ้า response ไม่ใช่ JSON array

## Supabase Storage

- bucket `tb-files` และ `exports` เป็น **private** เสมอ
- Download ผ่าน signed URL เท่านั้น (expire 1 ชั่วโมง)
- ไม่มี public URL ถาวรสำหรับไฟล์ใดๆ

## Row Level Security (RLS)

```sql
-- Projects
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_projects" ON projects
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- TB Rows
ALTER TABLE tb_rows ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_tb_rows" ON tb_rows
  USING (project_id IN (
    SELECT p.id FROM projects p
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));

-- Account Mappings
ALTER TABLE account_mappings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_mappings" ON account_mappings
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- Financial Statements
ALTER TABLE financial_statements ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_fs" ON financial_statements
  USING (project_id IN (
    SELECT p.id FROM projects p
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));

-- Export History
ALTER TABLE export_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_exports" ON export_history
  USING (project_id IN (
    SELECT p.id FROM projects p
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));

-- Organizations (เห็นเฉพาะ org ที่ตัวเองอยู่)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_organizations" ON organizations
  USING (id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- Templates
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_templates" ON templates
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- FS Comments
ALTER TABLE fs_comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_fs_comments" ON fs_comments
  USING (fs_id IN (
    SELECT f.id FROM financial_statements f
    JOIN projects p ON p.id = f.project_id
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));

-- Audit Logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_audit_logs" ON audit_logs
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- Jobs
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_jobs" ON jobs
  USING (project_id IN (
    SELECT p.id FROM projects p
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));
```

## Rate Limiting

> **ปรับปรุงจาก v3.1:** limit ต่อ **org_id + user_id** ไม่ใช่แค่ IP address
> เพราะ 10 คนใน org เดียวกันจะรวมกัน shared IP limit ทำให้ user อื่นถูกบล็อกโดยไม่ผิด

```python
from slowapi import Limiter
from fastapi import Request

def get_org_user_key(request: Request) -> str:
    """Rate limit key = org_id:user_id — แยกต่อ org และ user"""
    user = request.state.user          # set โดย auth middleware
    org_id = request.path_params.get("org_id") or getattr(user, "current_org_id", "unknown")
    return f"{org_id}:{user.id}"

limiter = Limiter(key_func=get_org_user_key)

# AI Mapping — limit ต่อ user 10 ครั้ง/นาที
@app.post("/projects/{id}/mapping/run")
@limiter.limit("10/minute")
async def run_mapping(...): ...

# Draft — limit ต่อ user 5 ครั้ง/นาที
@app.post("/projects/{id}/draft")
@limiter.limit("5/minute")
async def run_draft(...): ...

# Export PDF — limit ต่อ user 20 ครั้ง/นาที
@app.post("/projects/{id}/export/pdf")
@limiter.limit("20/minute")
async def export_pdf(...): ...

# AI Provider test — limit ต่อ user 5 ครั้ง/นาที (ป้องกัน key brute-force)
@app.get("/organizations/{org_id}/ai-provider/test")
@limiter.limit("5/minute")
async def test_ai_provider(...): ...
```

## CORS (Production)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://findraft.app",
        "https://www.findraft.app",
        # ลบ localhost ออกก่อน go live
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
