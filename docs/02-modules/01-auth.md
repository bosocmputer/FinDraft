# Module 1 — Auth & Multi-user

_Blueprint v3.2 | [← Index](../README.md)_

---

## ฟีเจอร์

- Login / Register
- สร้าง Organization (สำนักงาน)
- เชิญ member เข้า team
- Role: `admin` | `auditor` | `viewer`
- **1 user สามารถอยู่ได้หลาย org** (ผ่าน junction table `user_organizations`)

## Permission Matrix

| Action          | admin | auditor | viewer |
| --------------- | ----- | ------- | ------ |
| อัปโหลด TB      | ✅    | ✅      | ❌     |
| แก้ไข mapping   | ✅    | ✅      | ❌     |
| Draft งบ        | ✅    | ✅      | ❌     |
| แก้ไขงบ         | ✅    | ✅      | ❌     |
| Finalize งบ     | ✅    | ❌      | ❌     |
| Export          | ✅    | ✅      | ✅     |
| จัดการ template | ✅    | ❌      | ❌     |
| จัดการ member   | ✅    | ❌      | ❌     |

## Claude Code Prompt

```
สร้าง auth system สำหรับ FastAPI + Next.js ที่มี:
- JWT token-based auth ผ่าน Supabase Auth
- Organization concept (1 org มีหลาย user, 1 user อยู่ได้หลาย org)
- Role ถูกเก็บใน user_organizations junction table (ไม่ใช่ใน users)
- Middleware ตรวจ role ก่อนเข้า route
- Finalize action สำหรับ admin เท่านั้น
```
