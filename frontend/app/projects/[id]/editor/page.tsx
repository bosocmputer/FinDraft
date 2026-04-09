"use client";

export default function EditorPage({ params }: { params: { id: string } }) {
  // TODO: FSEditor (4 tab: BS, P&L, CF, SCE) + ValidationBanner + UnmappedWarning + Finalize
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">แก้ไขงบการเงิน</h1>
      <p className="text-gray-500">TODO: Financial Statement Editor</p>
    </div>
  );
}
