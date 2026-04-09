"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApp } from "@/lib/store";
import { supabase } from "@/lib/auth";
import { toast } from "sonner";

export function Navbar() {
  const router = useRouter();
  const { user, org } = useApp();

  async function handleLogout() {
    await supabase.auth.signOut();
    localStorage.removeItem("findraft_org");
    toast.success("ออกจากระบบแล้ว");
    router.push("/auth/login");
  }

  return (
    <nav className="border-b bg-white px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link href="/dashboard" className="font-bold text-blue-600 text-lg">
          FinDraft AI
        </Link>
        {org && (
          <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {org.org_name}
          </span>
        )}
      </div>
      <div className="flex items-center gap-4">
        {user && (
          <>
            <span className="text-sm text-gray-500">{user.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-red-500 hover:text-red-700 transition"
            >
              ออกจากระบบ
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
