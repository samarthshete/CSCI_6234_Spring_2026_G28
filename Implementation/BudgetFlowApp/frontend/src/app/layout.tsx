import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BudgetFlow",
  description: "Intelligent Personal Finance Management",
  icons: { icon: "/icon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
