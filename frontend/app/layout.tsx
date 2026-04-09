import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinDraft AI — ระบบ Draft งบการเงินอัตโนมัติ",
  description: "AI-powered financial statement drafting for Auditors",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
