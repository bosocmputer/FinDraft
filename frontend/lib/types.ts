// ==============================
// Auth & Organization
// ==============================
export type Role = "admin" | "auditor" | "viewer";

export interface Organization {
  id: string;
  name: string;
  created_at: string;
}

export interface UserOrganization {
  user_id: string;
  org_id: string;
  role: Role;
  joined_at: string;
}

// ==============================
// Projects
// ==============================
export type ProjectStatus = "uploading" | "mapping" | "reviewing" | "drafting" | "finalized";

export interface Project {
  id: string;
  org_id: string;
  company_name: string;
  fiscal_year: number;
  comparative_year?: number;
  currency: string;
  status: ProjectStatus;
  template_id?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// ==============================
// TB Rows
// ==============================
export interface TBRow {
  id: string;
  project_id: string;
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  net: number;
  row_order: number;
}

// ==============================
// Account Mappings
// ==============================
export type Category =
  | "current_asset" | "non_current_asset"
  | "current_liability" | "non_current_liability"
  | "equity" | "revenue" | "cost_of_sales"
  | "selling_expense" | "admin_expense"
  | "other_income" | "other_expense"
  | "operating_activity" | "investing_activity" | "financing_activity";

export interface AccountMapping {
  id: string;
  project_id: string;
  org_id: string;
  account_code: string;
  account_name?: string;
  category: Category;
  fs_line_item?: string;
  confidence: number;
  is_confirmed: boolean;
  confirmed_by?: string;
  confirmed_at?: string;
}

// ==============================
// Financial Statements
// ==============================
export type FSType = "balance_sheet" | "profit_loss" | "cash_flow" | "equity_changes" | "audit_report";

export interface FinancialStatement {
  id: string;
  project_id: string;
  fs_type: FSType;
  data: Record<string, unknown>;
  version: number;
  is_final: boolean;
  created_at: string;
  updated_at: string;
}

// ==============================
// Jobs
// ==============================
export type JobType = "mapping" | "draft" | "export";
export type JobStatus = "pending" | "running" | "done" | "failed";

export interface Job {
  id: string;
  project_id: string;
  job_type: JobType;
  status: JobStatus;
  progress: number;
  total_rows?: number;
  done_rows?: number;
  error_msg?: string;
  started_at?: string;
  finished_at?: string;
  created_at: string;
}

// ==============================
// Export
// ==============================
export interface ExportHistory {
  id: string;
  project_id: string;
  export_type: "excel" | "pdf";
  file_path: string;
  is_draft: boolean;
  created_by?: string;
  created_at: string;
  expires_at?: string;
}
