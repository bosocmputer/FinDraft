"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";
import type { Organization, Project } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  uploading: "อัปโหลด TB",
  mapping: "Mapping บัญชี",
  reviewing: "รอยืนยัน",
  drafting: "Draft งบ",
  finalized: "เสร็จสมบูรณ์",
};

const STATUS_COLOR: Record<string, string> = {
  uploading: "bg-yellow-100 text-yellow-700",
  mapping: "bg-blue-100 text-blue-700",
  reviewing: "bg-orange-100 text-orange-700",
  drafting: "bg-purple-100 text-purple-700",
  finalized: "bg-green-100 text-green-700",
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, org, setOrg } = useApp();
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const loadOrgs = useCallback(async () => {
    if (!user) return;
    try {
      const data = await api.get("/organizations", authHeader(user.token));
      setOrgs(data);
      // Auto-select first org if none selected
      if (!org && data.length > 0) {
        setOrg({ org_id: data[0].id, org_name: data[0].name, role: "admin" });
      }
    } catch {
      toast.error("โหลดข้อมูลองค์กรไม่สำเร็จ");
    }
  }, [user, org, setOrg]);

  const loadProjects = useCallback(async () => {
    if (!user || !org) return;
    setLoading(true);
    try {
      const data = await api.get(`/projects?org_id=${org.org_id}`, authHeader(user.token));
      setProjects(data);
    } catch {
      toast.error("โหลดโปรเจกต์ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }, [user, org]);

  useEffect(() => { loadOrgs(); }, [loadOrgs]);
  useEffect(() => { loadProjects(); }, [loadProjects]);

  function handleOrgChange(orgId: string) {
    const selected = orgs.find((o) => o.id === orgId);
    if (selected) setOrg({ org_id: selected.id, org_name: selected.name, role: "admin" });
  }

  function getNextStep(project: Project) {
    switch (project.status) {
      case "uploading": return `/projects/${project.id}/upload`;
      case "mapping": return `/projects/${project.id}/mapping`;
      case "reviewing": return `/projects/${project.id}/mapping`;
      case "drafting": return `/projects/${project.id}/editor`;
      case "finalized": return `/projects/${project.id}/editor`;
      default: return `/projects/${project.id}/upload`;
    }
  }

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Org Switcher */}
        {orgs.length > 0 && (
          <div className="mb-6 flex items-center gap-3">
            <label className="text-sm text-gray-500">องค์กร:</label>
            <select
              value={org?.org_id || ""}
              onChange={(e) => handleOrgChange(e.target.value)}
              aria-label="เลือกองค์กร"
              title="เลือกองค์กร"
              className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">โปรเจกต์ทั้งหมด</h1>
          <Link
            href="/projects/new"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            + สร้างโปรเจกต์ใหม่
          </Link>
        </div>

        {/* Project List */}
        {loading ? (
          <div className="text-center py-16 text-gray-400">กำลังโหลด...</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 border-2 border-dashed rounded-xl">
            <p className="text-gray-400 mb-4">ยังไม่มีโปรเจกต์</p>
            <Link
              href="/projects/new"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            >
              สร้างโปรเจกต์แรก
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.map((project) => (
              <div
                key={project.id}
                className="border rounded-xl p-5 bg-white hover:shadow-sm transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900">{project.company_name}</h2>
                    <p className="text-sm text-gray-500 mt-0.5">
                      ปีงบ {project.fiscal_year} • {project.currency}
                      {project.comparative_year && ` • เปรียบเทียบ ${project.comparative_year}`}
                    </p>
                  </div>
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full ${STATUS_COLOR[project.status] || "bg-gray-100 text-gray-600"}`}
                  >
                    {STATUS_LABEL[project.status] || project.status}
                  </span>
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    type="button"
                    onClick={() => router.push(getNextStep(project))}
                    className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 transition"
                  >
                    ดำเนินการต่อ
                  </button>
                  <button
                    type="button"
                    onClick={() => router.push(`/projects/${project.id}/editor`)}
                    className="text-sm border px-3 py-1.5 rounded-lg hover:bg-gray-50 transition"
                  >
                    ดูงบการเงิน
                  </button>
                  <button
                    type="button"
                    onClick={() => router.push(`/projects/${project.id}/export`)}
                    className="text-sm border px-3 py-1.5 rounded-lg hover:bg-gray-50 transition"
                  >
                    Export
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
