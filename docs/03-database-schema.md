# Database Schema

_Blueprint v3.2 | [← Index](README.md)_

---

```sql
-- ==========================================
-- Organizations
-- ==========================================
CREATE TABLE organizations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- Users (ไม่มี org_id/role โดยตรง — ย้ายไป junction table)
-- ==========================================
CREATE TABLE users (
  id         UUID PRIMARY KEY,  -- ตรงกับ Supabase Auth uid
  email      TEXT UNIQUE NOT NULL,
  name       TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- User ↔ Organization (Multi-org support)
-- 1 user อยู่ได้หลาย org, แต่ละ org มี role ต่างกัน
-- ==========================================
CREATE TABLE user_organizations (
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  org_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role       TEXT NOT NULL CHECK (role IN ('admin', 'auditor', 'viewer')),
  invited_by UUID REFERENCES users(id),
  joined_at  TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, org_id)
);

CREATE INDEX idx_user_organizations_org  ON user_organizations(org_id);
CREATE INDEX idx_user_organizations_user ON user_organizations(user_id);

-- ==========================================
-- Projects
-- ==========================================
CREATE TABLE projects (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id           UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  company_name     TEXT NOT NULL,
  fiscal_year      INT  NOT NULL,
  comparative_year INT,                          -- ปีเปรียบเทียบ (แสดง 2 คอลัมน์ในงบ)
  currency         TEXT NOT NULL DEFAULT 'THB',  -- ISO 4217 เช่น THB, USD, SGD
  status           TEXT NOT NULL DEFAULT 'uploading'
                   CHECK (status IN ('uploading','mapping','reviewing','drafting','finalized')),
  template_id      UUID REFERENCES templates(id),
  created_by       UUID REFERENCES users(id),
  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now(),
  deleted_at       TIMESTAMPTZ DEFAULT NULL      -- soft delete: NULL = active
);

CREATE INDEX idx_projects_org ON projects(org_id);

-- ==========================================
-- TB Rows
-- ==========================================
CREATE TABLE tb_rows (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  account_code TEXT NOT NULL,
  account_name TEXT NOT NULL,
  debit        NUMERIC(18,2) DEFAULT 0,
  credit       NUMERIC(18,2) DEFAULT 0,
  net          NUMERIC(18,2) GENERATED ALWAYS AS (debit - credit) STORED,
  row_order    INT  -- เก็บลำดับจาก file ต้นฉบับ
);

CREATE INDEX idx_tb_rows_project ON tb_rows(project_id);

-- ==========================================
-- Account Mappings
-- scoped ต่อ org_id สำหรับ cache ระดับ org
-- ==========================================
CREATE TABLE account_mappings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id    UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  account_code  TEXT NOT NULL,
  account_name  TEXT,
  category      TEXT NOT NULL,
  fs_line_item  TEXT,
  confidence    NUMERIC(5,4),  -- 0.0000–1.0000
  is_confirmed  BOOLEAN NOT NULL DEFAULT false,
  confirmed_by  UUID REFERENCES users(id),
  confirmed_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT now()
);

-- Index สำหรับ cache lookup (query บ่อยที่สุด)
CREATE UNIQUE INDEX idx_account_mappings_org_code
  ON account_mappings(org_id, account_code)
  WHERE is_confirmed = true;

CREATE INDEX idx_account_mappings_project ON account_mappings(project_id);

-- ==========================================
-- Financial Statements
-- ==========================================
CREATE TABLE financial_statements (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  fs_type    TEXT NOT NULL
             CHECK (fs_type IN ('balance_sheet','profit_loss','cash_flow','equity_changes','audit_report')),
  data       JSONB NOT NULL,
  version    INT  NOT NULL DEFAULT 1,
  is_final   BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_fs_project_type ON financial_statements(project_id, fs_type);

-- ==========================================
-- Templates
-- ==========================================
CREATE TABLE templates (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id                 UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name                   TEXT NOT NULL,
  description            TEXT,
  fs_structure           JSONB,
  cf_structure           JSONB,
  sce_structure          JSONB,      -- Statement of Changes in Equity template
  mapping_rules          JSONB,
  audit_report_template  TEXT,
  created_at             TIMESTAMPTZ DEFAULT now(),
  updated_at             TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- FS Comments
-- ==========================================
CREATE TABLE fs_comments (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fs_id      UUID NOT NULL REFERENCES financial_statements(id) ON DELETE CASCADE,
  cell_ref   TEXT,
  content    TEXT NOT NULL,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  resolved   BOOLEAN DEFAULT false
);

CREATE INDEX idx_fs_comments_fs ON fs_comments(fs_id);

-- ==========================================
-- Export History
-- ==========================================
CREATE TABLE export_history (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  export_type  TEXT NOT NULL CHECK (export_type IN ('excel', 'pdf')),
  file_path    TEXT NOT NULL,
  is_draft     BOOLEAN NOT NULL DEFAULT true,
  created_by   UUID REFERENCES users(id),
  created_at   TIMESTAMPTZ DEFAULT now(),
  expires_at   TIMESTAMPTZ
);

CREATE INDEX idx_export_history_project ON export_history(project_id);

-- ==========================================
-- Triggers: auto-update updated_at
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_fs_updated_at
  BEFORE UPDATE ON financial_statements
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ==========================================
-- Audit Logs (Activity Trail)
-- ==========================================
CREATE TABLE audit_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  project_id  UUID REFERENCES projects(id) ON DELETE SET NULL,
  user_id     UUID REFERENCES users(id),
  action      TEXT NOT NULL,   -- 'mapping.confirm' | 'fs.edit' | 'fs.finalize' | 'export'
  target_type TEXT,            -- 'account_mapping' | 'financial_statement' | 'project'
  target_id   UUID,
  metadata    JSONB,           -- before/after values หรือ context เพิ่มเติม
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_audit_logs_project ON audit_logs(project_id);
CREATE INDEX idx_audit_logs_org     ON audit_logs(org_id);
CREATE INDEX idx_audit_logs_user    ON audit_logs(user_id);

-- ==========================================
-- Jobs (Background Task Tracking)
-- ==========================================
CREATE TABLE jobs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  job_type    TEXT NOT NULL CHECK (job_type IN ('mapping', 'draft', 'export')),
  status      TEXT NOT NULL DEFAULT 'pending'
              CHECK (status IN ('pending', 'running', 'done', 'failed')),
  progress    INT  DEFAULT 0,  -- 0–100 (%)
  total_rows  INT,
  done_rows   INT  DEFAULT 0,
  error_msg   TEXT,
  started_at  TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_jobs_project ON jobs(project_id);

-- ==========================================
-- Invitations (Token-based invite link)
-- ==========================================
CREATE TABLE invitations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('admin', 'auditor', 'viewer')),
  token       TEXT NOT NULL UNIQUE,              -- random token สำหรับ invite link
  invited_by  UUID REFERENCES users(id),
  status      TEXT NOT NULL DEFAULT 'pending'
              CHECK (status IN ('pending', 'accepted', 'expired')),
  expires_at  TIMESTAMPTZ NOT NULL,              -- invite หมดอายุ 7 วัน
  accepted_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_invitations_org   ON invitations(org_id);
CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);

-- ==========================================
-- Org AI Provider Configs
-- เก็บ API key ของ org (encrypted) + provider ที่เลือก
-- ==========================================
CREATE TABLE org_ai_configs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id            UUID NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
  provider          TEXT NOT NULL DEFAULT 'anthropic'
                    CHECK (provider IN ('anthropic', 'openai', 'gemini', 'openrouter')),
  model             TEXT NOT NULL,               -- เช่น 'claude-sonnet-4-6', 'gpt-4o'
  api_key_encrypted TEXT NOT NULL,               -- AES-256-GCM encrypted
  updated_by        UUID REFERENCES users(id),
  updated_at        TIMESTAMPTZ DEFAULT now(),
  created_at        TIMESTAMPTZ DEFAULT now()
);

-- RLS: เฉพาะ admin ของ org เท่านั้นที่จัดการได้ (enforce ที่ application layer)
ALTER TABLE org_ai_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_ai_configs" ON org_ai_configs
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));
```
