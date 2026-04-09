"use client";
import { useState, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { Navbar } from "@/components/navbar";
import { useApp } from "@/lib/store";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";
import { toast } from "sonner";

export default function UploadPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const { user } = useApp();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  }

  async function handleUpload() {
    if (!file || !user) return;
    if (file.size > 20 * 1024 * 1024) { toast.error("ไฟล์ใหญ่เกิน 20MB"); return; }
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.postForm(`/projects/${projectId}/upload`, form, authHeader(user.token));
      toast.success("อัปโหลดสำเร็จ");
      router.push(`/projects/${projectId}/mapping`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "อัปโหลดไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthGuard>
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">อัปโหลด Trial Balance</h1>
          <p className="text-gray-500 text-sm mt-1">รองรับไฟล์ .xlsx, .csv, .pdf — ขนาดไม่เกิน 20MB</p>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition ${
            dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
          }`}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.csv,.pdf"
            onChange={handleFileChange}
            className="hidden"
            title="เลือกไฟล์ Trial Balance"
          />
          {file ? (
            <div>
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          ) : (
            <div>
              <p className="text-gray-400 text-lg mb-2">ลากไฟล์มาวางที่นี่</p>
              <p className="text-sm text-gray-400">หรือคลิกเพื่อเลือกไฟล์ (.xlsx / .csv / .pdf)</p>
            </div>
          )}
        </div>

        {file && (
          <div className="flex gap-3 mt-6">
            <button type="button" onClick={() => setFile(null)} className="flex-1 border rounded-lg py-2 text-sm hover:bg-gray-50 transition">
              เลือกไฟล์ใหม่
            </button>
            <button
              type="button"
              onClick={handleUpload}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loading ? "กำลังอัปโหลด..." : "อัปโหลดและวิเคราะห์"}
            </button>
          </div>
        )}
      </div>
    </AuthGuard>
  );
}
