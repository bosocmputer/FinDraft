"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";
import type { AccountMapping, Category } from "@/lib/types";

const CATEGORIES: { value: Category; label: string }[] = [
  { value: "current_asset", label: "สินทรัพย์หมุนเวียน" },
  { value: "non_current_asset", label: "สินทรัพย์ไม่หมุนเวียน" },
  { value: "current_liability", label: "หนี้สินหมุนเวียน" },
  { value: "non_current_liability", label: "หนี้สินไม่หมุนเวียน" },
  { value: "equity", label: "ส่วนของผู้ถือหุ้น" },
  { value: "revenue", label: "รายได้" },
  { value: "cost_of_sales", label: "ต้นทุนขาย" },
  { value: "selling_expense", label: "ค่าใช้จ่ายขาย" },
  { value: "admin_expense", label: "ค่าใช้จ่ายบริหาร" },
  { value: "other_income", label: "รายได้อื่น" },
  { value: "other_expense", label: "ค่าใช้จ่ายอื่น" },
  { value: "operating_activity", label: "กิจกรรมดำเนินงาน" },
  { value: "investing_activity", label: "กิจกรรมลงทุน" },
  { value: "financing_activity", label: "กิจกรรมจัดหาเงิน" },
];

export default function MappingPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const { user } = useApp();
  const [mappings, setMappings] = useState<AccountMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningAI, setRunningAI] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const loadMappings = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.get(`/projects/${projectId}/mapping`, authHeader(user.token));
      setMappings(data);
    } catch {
      toast.error("โหลด mapping ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }, [user, projectId]);

  useEffect(() => { loadMappings(); }, [loadMappings]);

  async function runAIMapping() {
    if (!user) return;
    setRunningAI(true);
    try {
      await api.post(`/projects/${projectId}/mapping/run`, {}, authHeader(user.token));
      toast.success("AI Mapping สำเร็จ");
      await loadMappings();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "AI Mapping ไม่สำเร็จ");
    } finally {
      setRunningAI(false);
    }
  }

  async function updateCategory(accountCode: string, category: Category) {
    if (!user) return;
    try {
      // Backend: PUT /projects/{id}/mapping/{account_code}
      await api.put(
        `/projects/${projectId}/mapping/${accountCode}`,
        { category },
        authHeader(user.token)
      );
      setMappings((prev) => prev.map((m) => (m.account_code === accountCode ? { ...m, category } : m)));
    } catch {
      toast.error("อัปเดต category ไม่สำเร็จ");
    }
  }

  async function confirmAll() {
    if (!user) return;
    setConfirming(true);
    try {
      await api.post(`/projects/${projectId}/mapping/confirm`, {}, authHeader(user.token));
      toast.success("ยืนยัน mapping ทั้งหมดสำเร็จ");
      router.push(`/projects/${projectId}/editor`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "ยืนยันไม่สำเร็จ");
    } finally {
      setConfirming(false);
    }
  }

  const unconfirmed = mappings.filter((m) => !m.is_confirmed);
  const lowConfidence = mappings.filter((m) => m.confidence < 0.8 && !m.is_confirmed);

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ตรวจสอบการ Mapping บัญชี</h1>
            <p className="text-gray-500 text-sm mt-1">
              {mappings.length} บัญชี • {unconfirmed.length} รอยืนยัน
              {lowConfidence.length > 0 && (
                <span className="ml-2 text-orange-500">• {lowConfidence.length} confidence ต่ำ (&lt;80%)</span>
              )}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={runAIMapping}
              disabled={runningAI}
              className="border border-blue-600 text-blue-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-50 disabled:opacity-50 transition"
            >
              {runningAI ? "กำลัง run AI..." : "Run AI Mapping"}
            </button>
            <button
              type="button"
              onClick={confirmAll}
              disabled={confirming || mappings.length === 0}
              className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition"
            >
              {confirming ? "กำลังยืนยัน..." : "ยืนยันทั้งหมด → Draft งบ"}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400">กำลังโหลด...</div>
        ) : mappings.length === 0 ? (
          <div className="text-center py-16 border-2 border-dashed rounded-xl">
            <p className="text-gray-400 mb-4">ยังไม่มี mapping — กด Run AI Mapping เพื่อเริ่ม</p>
          </div>
        ) : (
          <div className="border rounded-xl overflow-hidden bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">รหัสบัญชี</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">ชื่อบัญชี</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Category</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Line Item</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">Confidence</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-600">สถานะ</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {mappings.map((m) => (
                  <tr key={m.id} className={m.confidence < 0.8 && !m.is_confirmed ? "bg-orange-50" : ""}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{m.account_code}</td>
                    <td className="px-4 py-3 text-gray-900">{m.account_name || "-"}</td>
                    <td className="px-4 py-3">
                      <select
                        value={m.category}
                        onChange={(e) => updateCategory(m.account_code, e.target.value as Category)}
                        aria-label={`Category สำหรับ ${m.account_code}`}
                        title={`Category สำหรับ ${m.account_code}`}
                        className="border rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {CATEGORIES.map((c) => (
                          <option key={c.value} value={c.value}>{c.label}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{m.fs_line_item || "-"}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        m.confidence >= 0.9 ? "bg-green-100 text-green-700" :
                        m.confidence >= 0.8 ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      }`}>
                        {Math.round(m.confidence * 100)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {m.is_confirmed ? (
                        <span className="text-xs text-green-600 font-medium">ยืนยันแล้ว</span>
                      ) : (
                        <span className="text-xs text-gray-400">รอยืนยัน</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
