-- ==========================================
-- Row Level Security (RLS) Policies
-- Blueprint v3.2
-- ==========================================

-- Organizations
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_organizations" ON organizations
  USING (id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

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

-- FS Comments
ALTER TABLE fs_comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_fs_comments" ON fs_comments
  USING (fs_id IN (
    SELECT f.id FROM financial_statements f
    JOIN projects p ON p.id = f.project_id
    JOIN user_organizations uo ON uo.org_id = p.org_id
    WHERE uo.user_id = auth.uid()
  ));

-- Templates
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_templates" ON templates
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- Export History
ALTER TABLE export_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_exports" ON export_history
  USING (project_id IN (
    SELECT p.id FROM projects p
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

-- Invitations
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_invitations" ON invitations
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));

-- Org AI Configs (เฉพาะ admin ของ org)
ALTER TABLE org_ai_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation_ai_configs" ON org_ai_configs
  USING (org_id IN (
    SELECT org_id FROM user_organizations WHERE user_id = auth.uid()
  ));
