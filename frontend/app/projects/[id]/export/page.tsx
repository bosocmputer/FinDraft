"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";
import type { ExportHistory } from "@/lib/types";

export default function ExportPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user } = useApp();
  const [history, setHistory] = useState<ExportHistory[]>([]);
  const [exporting, setExporting] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.get(`/projects/${projectId}/exports`, authHeader(user.token));
      setHistory(data);
    } catch {
      // no history yet
    }
  }, [user, projectId]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  async function handleExport(type: "excel" | "pdf", isDraft: boolean) {
    if (!user) return;
    const key = `${type}-${isDraft}`;
    setExporting(key);
    try {
      const res = await api.getRaw(
        `/projects/${projectId}/export/${type}?is_draft=${isDraft}`,
        authHeader(user.token)
      );
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `financial_statement_${isDraft ? "draft" : "final"}.${type === "excel" ? "xlsx" : "pdf"}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Export ${type.toUpperCase()} สำเร็จ`);
      await loadHistory();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Export ไม่สำเร็จ");
    } finally {
      setExporting(null);
    }
  }

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Export งบการเงิน</h1>

        {/* Export Options */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          {/* Excel */}
          <div className="border rounded-xl p-5 bg-white">
            <h2 className="font-semibold text-gray-900 mb-1">Excel (.xlsx)</h2>
            <p className="text-sm text-gray-500 mb-4">งบครบ 4 แผ่น พร้อมสูตรและ formatting</p>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => handleExport("excel", true)}
                disabled={!!exporting}
                className="border border-blue-600 text-blue-600 rounded-lg py-2 text-sm font-medium hover:bg-blue-50 disabled:opacity-50 transition"
              >
                {exporting === "excel-true" ? "กำลัง export..." : "Draft (มีลายน้ำ)"}
              </button>
              <button
                type="button"
                onClick={() => handleExport("excel", false)}
                disabled={!!exporting}
                className="bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {exporting === "excel-false" ? "กำลัง export..." : "Final (ไม่มีลายน้ำ)"}
              </button>
            </div>
          </div>

          {/* PDF */}
          <div className="border rounded-xl p-5 bg-white">
            <h2 className="font-semibold text-gray-900 mb-1">PDF</h2>
            <p className="text-sm text-gray-500 mb-4">พร้อมส่งลูกค้าหรือใช้ยื่นสรรพากร</p>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => handleExport("pdf", true)}
                disabled={!!exporting}
                className="border border-gray-600 text-gray-600 rounded-lg py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition"
              >
                {exporting === "pdf-true" ? "กำลัง export..." : "Draft PDF (มีลายน้ำ)"}
              </button>
              <button
                type="button"
                onClick={() => handleExport("pdf", false)}
                disabled={!!exporting}
                className="bg-gray-800 text-white rounded-lg py-2 text-sm font-medium hover:bg-gray-900 disabled:opacity-50 transition"
              >
                {exporting === "pdf-false" ? "กำลัง export..." : "Final PDF"}
              </button>
            </div>
          </div>
        </div>

        {/* Export History */}
        {history.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-900 mb-3">ประวัติการ Export</h2>
            <div className="border rounded-xl overflow-hidden bg-white">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">ประเภท</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">สถานะ</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600">วันที่</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {history.map((h) => (
                    <tr key={h.id}>
                      <td className="px-4 py-3 uppercase font-medium text-gray-900">{h.export_type}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${h.is_draft ? "bg-yellow-100 text-yellow-700" : "bg-green-100 text-green-700"}`}>
                          {h.is_draft ? "Draft" : "Final"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(h.created_at).toLocaleString("th-TH")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
