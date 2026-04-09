# API Routes

_Blueprint v3.2 | [← Index](README.md)_

---

## Auth & Organization

```
POST   /auth/register
POST   /auth/login

GET    /organizations                                    # list orgs ที่ user อยู่
POST   /organizations                                    # สร้าง org ใหม่
GET    /organizations/{org_id}/members
PUT    /organizations/{org_id}/members/{user_id}         # เปลี่ยน role
DELETE /organizations/{org_id}/members/{user_id}

# Invite flow (token-based)
POST   /organizations/{org_id}/invitations               # สร้าง invite link (admin only)
GET    /organizations/{org_id}/invitations               # list pending invitations
DELETE /organizations/{org_id}/invitations/{id}          # ยกเลิก invite
POST   /invitations/accept                               # รับ invite (ส่ง token มา, public)
```

## Projects

```
GET    /projects                                         # list (filtered by org, ไม่รวม deleted)
POST   /projects
GET    /projects/{id}
PUT    /projects/{id}
DELETE /projects/{id}                                    # soft delete (set deleted_at)
POST   /projects/{id}/restore                            # กู้คืน soft-deleted project
```

## Upload & TB

```
POST /projects/{id}/upload
GET  /projects/{id}/tb-rows
```

## Mapping

```
GET  /projects/{id}/mapping
POST /projects/{id}/mapping/run                  # trigger AI mapper → return { job_id } (async)
PUT  /projects/{id}/mapping/{account_code}       # แก้ manual
POST /projects/{id}/mapping/confirm              # confirm ทั้ง batch
GET  /projects/{id}/mapping/unmapped             # rows ที่ confidence < 0.8
```

## Draft & Financial Statements

```
POST /projects/{id}/draft
GET  /projects/{id}/fs/{type}                    # balance_sheet | profit_loss | cash_flow | equity_changes | audit_report
PUT  /projects/{id}/fs/{type}
POST /projects/{id}/fs/{type}/finalize           # finalize (admin only)
GET  /projects/{id}/fs/{type}/versions           # version history
```

## Export

```
POST /projects/{id}/export/excel
POST /projects/{id}/export/pdf
GET  /projects/{id}/export/history
GET  /projects/{id}/export/{export_id}/download  # signed URL (expire 1h)
```

## Jobs (Background Task Progress)

```
GET  /projects/{id}/jobs                         # list jobs สำหรับ project
GET  /projects/{id}/jobs/{job_id}                # status + progress (%)
GET  /projects/{id}/jobs/{job_id}/stream         # SSE stream สำหรับ real-time progress
```

## Audit Log

```
GET  /projects/{id}/audit-log                    # activity trail ของ project (admin only)
```

## Templates

```
GET    /templates
POST   /templates
GET    /templates/{id}
PUT    /templates/{id}
DELETE /templates/{id}
POST   /templates/{id}/clone
```

## AI Provider Config (admin only)

```
GET    /organizations/{org_id}/ai-provider               # ดู provider ปัจจุบันของ org (ไม่ return api_key)
PUT    /organizations/{org_id}/ai-provider               # ตั้งค่า provider + model + api_key
DELETE /organizations/{org_id}/ai-provider               # ลบ config → fallback เป็น system default
GET    /organizations/{org_id}/ai-provider/test          # ทดสอบ provider ว่า key ใช้ได้ไหม
```
