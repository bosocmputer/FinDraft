# Roadmap & Claude Code Commands

_Blueprint v3.2 | [← Index](README.md)_

---

## Phase 1 — MVP (4–6 สัปดาห์)

> เป้าหมาย: งบครบชุด 4 งบตาม TFRS/NPAE — Auditor นำไปใช้จริงได้เลย

- [ ] Auth + Organization setup (multi-org, user_organizations junction table)
- [ ] Token-based invite flow (invitations table, expire 7 วัน)
- [ ] Upload Excel/CSV + Parser (magic bytes validation, Decimal schema)
- [ ] AI Provider Abstraction Layer (base_provider + factory + AES-256-GCM key encryption)
- [ ] AI Account Mapper — provider-agnostic (batch + retry + org-scoped cache)
  - Default: Anthropic claude-sonnet-4-6
- [ ] Manual review UI (mapping table + unmapped queue)
- [ ] Draft Balance Sheet + P&L + **Cash Flow (indirect method)** + **SCE** (ครบชุด 4 งบ)
  - CF Editor มี section "Adjust Items" ให้กรอก non-cash items (ค่าเสื่อม ฯลฯ) manual
- [ ] Comparative period support (ตัวเลขปีก่อน — 2 คอลัมน์ในทุกงบ)
- [ ] Validation Engine (5 เงื่อนไข, Decimal tolerance 0.01, error บอก account code)
- [ ] Editor (4 tab: BS, P&L, CF, SCE + ValidationBanner 5 เงื่อนไข + UnmappedWarning)
- [ ] Background job queue (Celery + Redis) — mapping + export เป็น async
- [ ] Job progress SSE stream
- [ ] Audit log (mapping confirm, fs edit, finalize, export, ai-provider change)
- [ ] Finalize flow (admin only, lock การแก้ไข)
- [ ] Export PDF + Excel (DRAFT watermark, async Celery job)
- [ ] Signed URL download (expire 1h)
- [ ] Export history
- [ ] Deploy: Vercel + Railway + Supabase

## Phase 2 — Core Features (4 สัปดาห์)

- [ ] AI Provider Settings UI (admin — เลือก provider/model/key ต่อ org)
- [ ] ทดสอบ provider connection จาก UI (GET /ai-provider/test)
- [ ] PDF Upload + OCR (ภาษาไทย)
- [ ] Audit Report page + AI draft (Prompt 2 — provider-agnostic)
- [ ] Export ชุดงบทั้งหมดใน 1 คลิก
- [ ] Version history (ดู diff ระหว่าง version)
- [ ] Comment system (fs_comments)

## Phase 3 — Team Features (3 สัปดาห์)

- [ ] Multi-user realtime (Supabase Realtime — OnlineAvatars)
- [ ] Approve workflow
- [ ] Template manager (save + clone + pre-fill mapping scoped ต่อ org)
- [ ] Email notification (invite accepted, finalize, export ready)

## Phase 4 — Polish (2 สัปดาห์)

- [ ] Dashboard analytics (projects per month, avg mapping accuracy, AI cost per org)
- [ ] Project archive / restore (soft delete ด้วย deleted_at)
- [ ] Cache mapping rules UI (ดู/แก้ไข org-level cache)
- [ ] Sentry + monitoring dashboard
- [ ] Performance: lazy load large TB tables (virtual scroll)
- [ ] Currency display (แสดงสกุลเงินตาม projects.currency)

---

## เริ่มต้นด้วย Claude Code

```bash
# 1. สร้าง project structure
claude "สร้าง monorepo findraft-ai แยก frontend/ และ backend/ ตาม blueprint v3.2 นี้
รวม settings/ai-provider/ ใน frontend และ routers/ai_providers.py ใน backend"

# 2. Database migrations
claude "สร้าง SQL migrations ตาม schema ใน blueprint v3.2 รวม
user_organizations, export_history, audit_logs, jobs, triggers, RLS policies,
invitations table (token-based, expires_at),
org_ai_configs table (provider, model, api_key_encrypted),
projects เพิ่ม currency และ deleted_at columns"

# 3. Backend: FastAPI + auth (multi-org + invite flow)
claude "สร้าง FastAPI app พร้อม Supabase Auth, user_organizations junction table, role middleware ตาม permission matrix
รวม invite endpoints: POST /organizations/{org_id}/invitations, POST /invitations/accept (token-based, expire 7 วัน)"

# 4. Backend: File validator + Parser (Decimal schema)
claude "สร้าง file_validator.py ตรวจ magic bytes (python-magic) และ parser Excel/CSV/PDF
ใช้ TBRow schema ที่ใช้ Decimal แทน float พร้อม ROUND_HALF_UP ตาม blueprint v3.2"

# 5. Backend: AI Provider Abstraction Layer
claude "สร้าง services/ai/ ทั้งหมดตาม blueprint v3.2:
- base_provider.py (abstract class + AIMessage + AIResponse)
- anthropic_provider.py, openai_provider.py, gemini_provider.py, openrouter_provider.py
- provider_factory.py (get_provider(org_id) + fallback system default)
- utils/encryption.py (AES-256-GCM encrypt/decrypt สำหรับ org API key)
- routers/ai_providers.py (GET/PUT/DELETE /organizations/{org_id}/ai-provider + /test endpoint)"

# 6. Backend: AI Mapper (provider-agnostic, org-scoped cache + retry + sanitizer)
claude "สร้าง account_mapper.py ที่ใช้ provider_factory.get_provider(org_id) แทนการเรียก Anthropic โดยตรง
org-scoped cache, batch 50, retry 3 ครั้ง, response_sanitizer.py รองรับทุก provider"

# 7. Backend: Draft Engine (BS + P&L + CF indirect method + SCE + 5-condition validation)
claude "สร้าง draft_engine.py สร้างงบ BS, P&L, Cash Flow (indirect method), SCE
validate 5 เงื่อนไขด้วย Decimal tolerance=0.01 ตาม blueprint v3.2
error message ระบุ account_code ที่ทำให้ diff"

# 8. Backend: Export (async Celery + DRAFT watermark + signed URL)
claude "สร้าง excel_export.py และ pdf_export.py พร้อม DRAFT watermark
ย้าย export เป็น async Celery task ใน export_worker.py พร้อม signed URL (expire 1h)"

# 9. Frontend: Next.js setup
claude "สร้าง Next.js 14 App Router พร้อม Tailwind, shadcn/ui, Supabase client"

# 10. Frontend: FS Editor (4 tab + CF Adjust Items + ValidationBanner 5 เงื่อนไข)
claude "สร้าง Financial Statement Editor 4 tab (BS, P&L, CF, SCE) พร้อม:
- inline edit, auto-recalculate totals
- CF tab มี Adjust Items section (ค่าเสื่อม, non-cash items กรอก manual)
- ValidationBanner แสดง 5 เงื่อนไข พร้อมระบุ account ที่ทำให้ diff
- UnmappedWarning + Finalize button (admin only)"

# 11. Frontend: AI Provider Settings page
claude "สร้างหน้า settings/ai-provider/ สำหรับ admin ของ org:
- ProviderSelector dropdown (Anthropic / OpenAI / Gemini / OpenRouter)
- Model input field
- API key input (masked, ไม่แสดง plaintext)
- ปุ่ม Test Connection เรียก GET /ai-provider/test
- แสดง provider ปัจจุบัน (ไม่แสดง key)"

# 12. Security: RLS + Rate limiting ต่อ org+user
claude "สร้าง RLS policies ครบทุก table (รวม invitations, org_ai_configs)
rate limiting ต่อ org+user key (ไม่ใช่ IP) ตาม blueprint v3.2"

# 13. Background jobs: Celery + Redis worker (mapping + export)
claude "สร้าง Celery app + mapping_worker.py + export_worker.py + jobs table integration
พร้อม SSE progress endpoint ตาม blueprint v3.2"

# 14. Audit log
claude "สร้าง audit_logs service บันทึก log ทุก action สำคัญ
(mapping confirm, fs edit, finalize, export, ai-provider config change)"

# 15. Deploy config
claude "สร้าง Dockerfile (รวม libmagic1), vercel.json, GitHub Actions CI/CD,
Railway Celery worker service ตาม blueprint v3.2
requirements.txt รวม anthropic, openai, google-generativeai, cryptography"
```

---

_Blueprint version 3.2 — Next.js 14 + FastAPI + Celery + Redis + Supabase + Vercel + Railway_
_AI Providers: Anthropic / OpenAI / Gemini / OpenRouter (provider-agnostic abstraction)_
_Updated: 2026-04-09_
