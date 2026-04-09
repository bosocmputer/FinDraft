# FinDraft AI — โครงสร้างโปรเจกต์

_Blueprint v3.2 | [← Index](README.md)_

---

## 3. โครงสร้างโปรเจกต์

```
findraft-ai/
├── frontend/                    # Next.js 14
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   │   ├── [id]/
│   │   │   │   ├── upload/
│   │   │   │   ├── mapping/
│   │   │   │   │   └── unmapped/    # ดู rows ที่ยัง confidence < 0.8
│   │   │   │   ├── editor/
│   │   │   │   └── export/
│   │   │   └── new/
│   │   ├── templates/
│   │   └── settings/
│   │       └── ai-provider/         # หน้าตั้งค่า AI Provider ต่อ org
│   ├── components/
│   │   ├── upload/
│   │   ├── mapping-table/
│   │   │   ├── MappingTable.tsx
│   │   │   ├── UnmappedAlert.tsx    # แสดง warning rows ที่ยัง unconfirmed
│   │   │   └── ConfidenceBadge.tsx
│   │   ├── fs-editor/
│   │   │   ├── FSEditor.tsx
│   │   │   ├── FSToolbar.tsx
│   │   │   ├── FSTabBar.tsx
│   │   │   ├── BalanceSheet.tsx
│   │   │   ├── ProfitLoss.tsx
│   │   │   ├── CashFlow.tsx         # เพิ่มใน MVP
│   │   │   ├── AuditReport.tsx
│   │   │   ├── ValidationBanner.tsx # แสดง warning ถ้างบไม่สมดุล
│   │   │   ├── UnmappedWarning.tsx  # แสดงจำนวน rows ที่ยัง unmapped
│   │   │   └── OnlineAvatars.tsx    # Supabase Realtime
│   │   ├── export/
│   │   └── ai-provider/
│   │       └── ProviderSelector.tsx # dropdown เลือก provider + model
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── .env.local
│   └── package.json
│
├── backend/                     # FastAPI
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── organizations.py         # จัดการ org, member, invite
│   │   ├── projects.py
│   │   ├── upload.py
│   │   ├── mapping.py
│   │   ├── draft.py
│   │   ├── export.py
│   │   ├── ai_providers.py          # CRUD provider config ต่อ org
│   │   └── jobs.py                  # job status + progress tracking
│   ├── workers/
│   │   ├── celery_app.py            # Celery app instance + Redis broker
│   │   ├── mapping_worker.py        # async AI mapping task
│   │   └── export_worker.py         # async PDF/Excel export task
│   ├── services/
│   │   ├── parser/
│   │   │   ├── file_validator.py    # magic bytes + MIME check
│   │   │   ├── excel_parser.py
│   │   │   ├── csv_parser.py
│   │   │   └── pdf_parser.py
│   │   ├── ai/
│   │   │   ├── provider_factory.py  # factory: return provider by org config
│   │   │   ├── base_provider.py     # abstract base class (interface)
│   │   │   ├── anthropic_provider.py
│   │   │   ├── openai_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── openrouter_provider.py
│   │   │   ├── account_mapper.py    # ใช้ provider_factory — ไม่ผูกกับ Claude
│   │   │   ├── draft_engine.py      # BS + P&L + CF + SCE + validation
│   │   │   └── response_sanitizer.py
│   │   └── export/
│   │       ├── excel_export.py
│   │       └── pdf_export.py        # รองรับ DRAFT watermark
│   ├── models/
│   ├── schemas/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
│
└── database/
    └── migrations/
```
