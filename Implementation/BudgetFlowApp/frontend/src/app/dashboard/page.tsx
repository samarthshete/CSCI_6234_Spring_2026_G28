"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Alert from "@/components/ui/Alert";
import { apiFetch, ApiError } from "@/lib/api";

const steps = [
  { label: "Create an account", href: "/accounts", icon: "◈" },
  { label: "Import transactions", href: "/import", icon: "↑" },
  { label: "Review categorization", href: "/transactions", icon: "≡" },
  { label: "Set a budget", href: "/budgets", icon: "◎" },
  { label: "View analytics", href: "/analytics", icon: "◔" },
];

interface Summary { total_spending: number; by_category: unknown[]; by_account: unknown[] }

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const now = new Date();
    const from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
    const to = now.toISOString().slice(0, 10);
    apiFetch<Summary>(`/api/v1/analytics/summary?date_from=${from}&date_to=${to}`)
      .then(setSummary)
      .catch((e) => setError((e as ApiError).detail || "Could not load summary"));
  }, []);

  return (
    <AppShell>
      <h1 className="mb-6 text-2xl font-semibold text-neutral-900">Dashboard</h1>

      {summary && (
        <Card className="mb-6">
          <p className="text-sm text-neutral-500">Spending this month</p>
          <p className="text-3xl font-bold text-neutral-900">${Number(summary.total_spending).toFixed(2)}</p>
        </Card>
      )}
      {error && <div className="mb-6"><Alert>{error}</Alert></div>}

      <h2 className="mb-4 text-lg font-medium text-neutral-700">Getting Started</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s, i) => (
          <Link key={s.href} href={s.href}>
            <Card className="flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-100 text-lg">{s.icon}</span>
              <div>
                <p className="text-xs text-neutral-400">Step {i + 1}</p>
                <p className="text-sm font-medium text-neutral-800">{s.label}</p>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
