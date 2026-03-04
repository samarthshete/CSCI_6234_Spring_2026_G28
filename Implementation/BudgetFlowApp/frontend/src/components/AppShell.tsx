"use client";
import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearTokens } from "@/lib/auth";
import RequireAuth from "./RequireAuth";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: "▦" },
  { href: "/accounts", label: "Accounts", icon: "◈" },
  { href: "/import", label: "Import", icon: "↑" },
  { href: "/transactions", label: "Transactions", icon: "≡" },
  { href: "/categories", label: "Categories", icon: "⊞" },
  { href: "/budgets", label: "Budgets", icon: "◎" },
  { href: "/analytics", label: "Analytics", icon: "◔" },
  { href: "/alerts", label: "Alerts", icon: "◇" },
  { href: "/reports", label: "Reports", icon: "⊜" },
  { href: "/jobs", label: "Jobs", icon: "⚙" },
  { href: "/advisor", label: "Advisor", icon: "◈" },
  { href: "/recommendations", label: "Invest", icon: "▲" },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearTokens();
    router.replace("/login");
  }

  return (
    <RequireAuth>
      <div className="flex min-h-screen">
        <aside className="flex w-56 flex-col border-r border-neutral-200 bg-white">
          <div className="px-5 py-6">
            <Link href="/dashboard" className="text-lg font-bold text-neutral-900">BudgetFlow</Link>
          </div>
          <nav className="flex-1 space-y-0.5 px-3">
            {nav.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  pathname.startsWith(n.href)
                    ? "bg-neutral-100 text-neutral-900"
                    : "text-neutral-500 hover:bg-neutral-50 hover:text-neutral-800"
                }`}
              >
                <span className="text-base">{n.icon}</span>
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="border-t border-neutral-200 p-3">
            <button
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-neutral-500 hover:bg-neutral-50 hover:text-neutral-800"
            >
              <span className="text-base">⎋</span>
              Logout
            </button>
          </div>
        </aside>
        <main className="flex-1 overflow-auto p-8">{children}</main>
      </div>
    </RequireAuth>
  );
}
