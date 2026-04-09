import os
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Service role client — ควร bypass RLS โดยอัตโนมัติ
# ถ้ายังไม่ bypass ต้องส่ง header เพิ่ม
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Force bypass RLS ด้วย service role header
supabase.postgrest.auth(SUPABASE_SERVICE_KEY)
