"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";
import type { FinancialStatement, FSType } from "@/lib/types";

const FS_TABS: { type: FSType; label: string }[] = [
  { type: "balance_sheet", label: "งบแสดงฐานะการเงิน" },
  { type: "profit_loss", label: "งบกำไรขาดทุน" },
  { type: "cash_flow", label: "งบกระแสเงินสด" },
  { type: "equity_changes", label: "งบแสดงการเปลี่ยนแปลงส่วนทุน" },
];

function formatNumber(n: number | undefined | null): string {
  if (n === undefined || n === null) return "-";
  return new Intl.NumberFormat("th-TH", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
}

function renderSection(title: string, items: Record<string, number> | undefined) {
  if (!items) return null;
  return (
    <div className="mb-6">
      <h3 className="font-semibold text-gray-700 mb-2 border-b pb-1">{title}</h3>
      <div className="space-y-1">
        {Object.entries(items).map(([key, val]) => (
          <div key={key} className="flex justify-between text-sm">
            <span className="text-gray-600 capitalize">{key.replace(/_/g, " ")}</span>
            <span className="font-mono text-gray-900">{formatNumber(val)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function EditorPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { user } = useApp();
  const [activeTab, setActiveTab] = useState<FSType>("balance_sheet");
  const [statements, setStatements] = useState<Partial<Record<FSType, FinancialStatement>>>({});
  const [loading, setLoading] = useState(true);
  const [drafting, setDrafting] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  const loadStatements = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    const results: Partial<Record<FSType, FinancialStatement>> = {};
    await Promise.all(
      FS_TABS.map(async (tab) => {
        try {
          // Backend: GET /projects/{id}/fs/{fs_type}
          const data = await api.get(`/projects/${projectId}/fs/${tab.type}`, authHeader(user.token));
          results[tab.type] = data;
        } catch {
          // not generated yet — skip
        }
      })
    );
    setStatements(results);
    setLoading(false);
  }, [user, projectId]);

  useEffect(() => { loadStatements(); }, [loadStatements]);

  async function runDraft() {
    if (!user) return;
    setDrafting(true);
    try {
      // Backend: POST /projects/{id}/draft
      await api.post(`/projects/${projectId}/draft`, {}, authHeader(user.token));
      toast.success("Draft งบการเงินสำเร็จ");
      await loadStatements();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Draft ไม่สำเร็จ");
    } finally {
      setDrafting(false);
    }
  }

  async function finalize() {
    if (!user) return;
    setFinalizing(true);
    try {
      // Backend: POST /projects/{id}/fs/{fs_type}/finalize (finalize all via balance_sheet)
      await api.post(`/projects/${projectId}/fs/balance_sheet/finalize`, {}, authHeader(user.token));
      toast.success("Finalize งบการเงินสำเร็จ");
      await loadStatements();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Finalize ไม่สำเร็จ");
    } finally {
      setFinalizing(false);
    }
  }

  const current = statements[activeTab];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = current?.data as any;
  const hasAny = Object.keys(statements).length > 0;

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">งบการเงิน</h1>
            {current && (
              <p className="text-sm text-gray-500 mt-1">
                Version {current.version} • {current.is_final ? "Finalized" : "Draft"}
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={runDraft} disabled={drafting}
              className="border border-blue-600 text-blue-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-50 disabled:opacity-50 transition">
              {drafting ? "กำลัง draft..." : hasAny ? "Re-Draft" : "Draft งบการเงิน"}
            </button>
            {hasAny && (
              <button type="button" onClick={finalize} disabled={finalizing}
                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition">
                {finalizing ? "กำลัง finalize..." : "Finalize งบ"}
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b mb-6 gap-1">
          {FS_TABS.map((tab) => (
            <button key={tab.type} type="button" onClick={() => setActiveTab(tab.type)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                activeTab === tab.type ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400">กำลังโหลด...</div>
        ) : !current ? (
          <div className="text-center py-16 border-2 border-dashed rounded-xl">
            <p className="text-gray-400 mb-4">ยังไม่มีข้อมูลงบนี้ — กด Draft งบการเงินก่อน</p>
          </div>
        ) : (
          <div className="bg-white border rounded-xl p-6">
            {current.is_final && (
              <div className="mb-4 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-4 py-2">
                งบนี้ถูก Finalize แล้ว — เป็นเวอร์ชันสุดท้าย
              </div>
            )}

            {activeTab === "balance_sheet" && data && (
              <>
                {renderSection("สินทรัพย์หมุนเวียน", data.current_assets)}
                {renderSection("สินทรัพย์ไม่หมุนเวียน", data.non_current_assets)}
                <div className="flex justify-between font-bold text-sm border-t pt-2 mb-6">
                  <span>รวมสินทรัพย์</span>
                  <span className="font-mono">{formatNumber(data.total_assets)}</span>
                </div>
                {renderSection("หนี้สินหมุนเวียน", data.current_liabilities)}
                {renderSection("หนี้สินไม่หมุนเวียน", data.non_current_liabilities)}
                {renderSection("ส่วนของผู้ถือหุ้น", data.equity)}
                <div className="flex justify-between font-bold text-sm border-t pt-2">
                  <span>รวมหนี้สินและส่วนของผู้ถือหุ้น</span>
                  <span className="font-mono">{formatNumber(data.total_liabilities_and_equity)}</span>
                </div>
              </>
            )}

            {activeTab === "profit_loss" && data && (
              <>
                {renderSection("รายได้", data.revenue)}
                {renderSection("ต้นทุน", data.cost_of_sales)}
                <div className="flex justify-between font-semibold text-sm border-t pt-2 mb-6">
                  <span>กำไรขั้นต้น</span>
                  <span className="font-mono">{formatNumber(data.gross_profit)}</span>
                </div>
                {renderSection("ค่าใช้จ่ายขาย", data.selling_expenses)}
                {renderSection("ค่าใช้จ่ายบริหาร", data.admin_expenses)}
                {renderSection("รายได้อื่น", data.other_income)}
                {renderSection("ค่าใช้จ่ายอื่น", data.other_expenses)}
                <div className="flex justify-between font-bold text-sm border-t pt-2">
                  <span>กำไร (ขาดทุน) สุทธิ</span>
                  <span className={`font-mono ${(data.net_profit || 0) >= 0 ? "text-green-700" : "text-red-600"}`}>
                    {formatNumber(data.net_profit)}
                  </span>
                </div>
              </>
            )}

            {(activeTab === "cash_flow" || activeTab === "equity_changes") && data && (
              <pre className="text-xs text-gray-600 bg-gray-50 p-4 rounded-lg overflow-auto">
                {JSON.stringify(data, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
