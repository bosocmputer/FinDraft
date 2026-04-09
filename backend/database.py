import os
from supabase import create_client, Client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Service role client — bypass RLS (ใช้ใน backend เท่านั้น)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
