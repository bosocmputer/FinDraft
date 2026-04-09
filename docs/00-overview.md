# FinDraft AI — Overview & Tech Stack

_Blueprint v3.2 | [← Index](README.md)_

---

## 1. Overview

### ปัญหาที่แก้

นักบัญชีและ Auditor ต้องนั่ง Map บัญชีจาก TB แล้วพิมพ์งบการเงินเองทีละรายการ ซ้ำซาก ใช้เวลานาน และ error-prone

### วิธีแก้

```
TB (Excel/CSV/PDF)
      ↓
Validate & Parse ไฟล์ (magic bytes + column detection)
      ↓
AI จัดหมวดบัญชีอัตโนมัติ (batch per org, cached by org_id)
      ↓
User ตรวจ confirm (flag rows ที่ confidence < 0.8)
      ↓
Draft Engine สร้างงบการเงินเต็มชุด (BS + P&L + CF + SCE)
      ↓
Validate ความสมดุล + ตรวจ unmapped rows
      ↓
แก้ไขบนหน้าจอ → Finalize → Export Excel / PDF (พร้อม DRAFT watermark)
```

### งบที่ระบบออกให้ (ครบชุดตาม TFRS/NPAE)

- งบแสดงฐานะการเงิน (Balance Sheet)
- งบกำไรขาดทุนเบ็ดเสร็จ (P&L)
- งบกระแสเงินสด (Cash Flow Statement) — **ต้องมีใน MVP**
- งบแสดงการเปลี่ยนแปลงส่วนของผู้ถือหุ้น (Statement of Changes in Equity) — **ต้องมีใน MVP**
- หน้ารายงานผู้สอบบัญชี (Audit Report Page)

---

## 2. Tech Stack

| Layer           | เทคโนโลยี                      | เหตุผล                                     |
| --------------- | ------------------------------ | ------------------------------------------ |
| Frontend        | Next.js 14 (App Router)        | SSR + React Server Components              |
| UI              | Tailwind CSS + shadcn/ui       | สร้างเร็ว                                  |
| Backend         | FastAPI (Python 3.11+)         | AI/data ecosystem ครบ                      |
| Database        | PostgreSQL 15                  | เก็บ mapping rules, templates, projects    |
| File Storage    | Supabase Storage               | เก็บไฟล์ TB และ output (expiry signed URL) |
| AI              | Multi-Provider (Anthropic / OpenAI / Gemini / OpenRouter) | map บัญชี + draft งบ — เลือก provider ต่อ org ได้ |
| PDF Parser      | pdfplumber + pytesseract (OCR) | อ่าน TB ที่เป็น PDF                        |
| Excel           | openpyxl + xlsxwriter          | อ่านและสร้าง Excel                         |
| Auth            | Supabase Auth                  | Multi-user, team-based                     |
| Realtime        | Supabase Realtime              | แสดงว่าใครกำลังดูอยู่ + job progress       |
| Job Queue       | Celery + Redis                 | Background AI mapping (async, retry)       |
| Frontend Deploy | Vercel                         | CI/CD อัตโนมัติจาก GitHub                  |
| Backend Deploy  | Railway                        | รัน FastAPI + Python dependencies          |
| Database Host   | Supabase                       | PostgreSQL managed + Auth + Storage รวมกัน |
