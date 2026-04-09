# Module 7 — Template Manager

_Blueprint v3.2 | [← Index](../README.md)_

---

## Database

```sql
templates (
  id, org_id, name, description,
  fs_structure jsonb,         -- BS + P&L structure
  cf_structure jsonb,         -- Cash Flow template
  sce_structure jsonb,        -- Statement of Changes in Equity template
  mapping_rules jsonb,        -- account_code → category mapping (scoped ต่อ org)
  audit_report_template text,
  created_at, updated_at
)
```

## Claude Code Prompt

```
สร้าง Template Manager ที่:
1. บันทึก template จากงบที่ finalized แล้ว (รวม cf_structure และ sce_structure)
2. หน้า list templates พร้อม preview
3. เลือก template เมื่อเริ่ม project ใหม่ → pre-fill mapping rules (scoped ต่อ org_id)
4. Clone template ได้ (สำหรับปีบัญชีใหม่หรือ org อื่น)
```
