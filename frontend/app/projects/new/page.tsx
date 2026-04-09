"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";

export default function NewProjectPage() {
  const router = useRouter();
  const { user, org } = useApp();
  const [form, setForm] = useState({
    company_name: "",
    fiscal_year: new Date().getFullYear(),
    comparative_year: "",
    currency: "THB",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!org && user) {
      // wait for org to load
    }
  }, [org, user]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!user || !org) { toast.error("กรุณาเลือกองค์กรก่อน"); return; }
    setLoading(true);
    try {
      const body = {
        org_id: org.org_id,
        company_name: form.company_name,
        fiscal_year: Number(form.fiscal_year),
        comparative_year: form.comparative_year ? Number(form.comparative_year) : null,
        currency: form.currency,
      };
      const project = await api.post("/projects", body, authHeader(user.token));
      toast.success("สร้างโปรเจกต์สำเร็จ");
      router.push(`/projects/${project.id}/upload`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "สร้างโปรเจกต์ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">สร้างโปรเจกต์ใหม่</h1>
        <form onSubmit={handleSubmit} className="space-y-5 bg-white border rounded-xl p-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ชื่อบริษัท / ลูกค้า</label>
            <input
              type="text"
              required
              value={form.company_name}
              onChange={(e) => setForm({ ...form, company_name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="เช่น บริษัท XYZ จำกัด"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ปีงบการเงิน</label>
              <input
                type="number"
                required
                value={form.fiscal_year}
                onChange={(e) => setForm({ ...form, fiscal_year: Number(e.target.value) })}
                title="ปีงบการเงิน"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ปีเปรียบเทียบ (ถ้ามี)</label>
              <input
                type="number"
                value={form.comparative_year}
                onChange={(e) => setForm({ ...form, comparative_year: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="เช่น 2567"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">สกุลเงิน</label>
            <select
              value={form.currency}
              onChange={(e) => setForm({ ...form, currency: e.target.value })}
              aria-label="สกุลเงิน"
              title="สกุลเงิน"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="THB">THB — บาท</option>
              <option value="USD">USD — ดอลลาร์สหรัฐ</option>
              <option value="EUR">EUR — ยูโร</option>
            </select>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => router.back()}
              className="flex-1 border rounded-lg py-2 text-sm hover:bg-gray-50 transition"
            >
              ยกเลิก
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loading ? "กำลังสร้าง..." : "สร้างโปรเจกต์"}
            </button>
          </div>
        </form>
      </div>
    </AuthGuard>
  );
}
