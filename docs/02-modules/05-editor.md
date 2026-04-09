# Module 5 — Financial Statement Editor

_Blueprint v3.2 | [← Index](../README.md)_

---

## Component Structure (React)

```
FSEditor/
├── FSToolbar.tsx               # Save, Finalize (admin only), Version history
├── FSTabBar.tsx                # BS | P&L | CF | SCE | Audit Report
├── BalanceSheetTab.tsx
│   ├── FSSection.tsx
│   ├── FSRow.tsx               # แก้ไขได้ inline
│   └── FSTotal.tsx             # คำนวณ auto
├── ProfitLossTab.tsx
├── CashFlowTab.tsx             # เพิ่มใน MVP
├── EquityChangesTab.tsx        # เพิ่มใน MVP (Statement of Changes in Equity)
├── AuditReportTab.tsx
├── ValidationBanner.tsx        # แสดง warning ถ้างบไม่สมดุล (5 เงื่อนไข)
├── UnmappedWarning.tsx         # แสดงจำนวน rows ที่ยัง unmapped + link ไปแก้
└── OnlineAvatars.tsx           # แสดง user ที่ online (Supabase Realtime)
```

## Finalize Flow

```
Editor → กด "Finalize" (admin only)
       → ระบบ validate อีกรอบ (server-side, 5 เงื่อนไข)
       → ถ้าผ่าน: project.status = 'finalized'
                  financial_statements.is_final = true
                  lock การแก้ไขทุก field
       → Export ที่ finalized → ไม่มี DRAFT watermark
       → Export ที่ status = drafting → มี DRAFT watermark ทุกหน้า
```

## Claude Code Prompt

```
สร้าง Financial Statement Editor ใน React + TypeScript ที่:
1. แสดงงบการเงินแบบ tree structure 4 tab: Balance Sheet, P&L, Cash Flow, SCE (Statement of Changes in Equity)
2. คลิก cell ตัวเลขเพื่อแก้ inline (disabled ถ้า is_final = true)
3. เมื่อแก้ตัวเลข ยอดรวม section และ grand total update อัตโนมัติ
4. ValidationBanner แสดง error list จาก validate 5 เงื่อนไข (พร้อมระบุ account code ที่ทำให้ diff)
5. UnmappedWarning แสดง count + link ไปหน้า /mapping/unmapped
6. ปุ่ม Finalize (admin only) → เรียก POST /projects/{id}/fs/{type}/finalize
7. บันทึก version ทุกครั้งที่ save
8. OnlineAvatars แสดง user ที่ online (Supabase Realtime)
```
