"use client";

export default function UnmappedPage({ params }: { params: { id: string } }) {
  // TODO: แสดง rows ที่ confidence < 0.8 ให้ user แก้ manual
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">รายการที่ยังไม่ได้ Mapping</h1>
      <p className="text-gray-500">TODO: Unmapped rows list</p>
    </div>
  );
}
