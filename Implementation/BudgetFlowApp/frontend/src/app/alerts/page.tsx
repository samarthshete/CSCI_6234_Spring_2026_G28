"use client";
import { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Select from "@/components/ui/Select";
import Alert from "@/components/ui/Alert";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import PageHeader from "@/components/ui/PageHeader";
import { apiFetch, ApiError } from "@/lib/api";

interface BudgetAlert {
  id: string;
  user_id: string;
  budget_id: string | null;
  category_id: string | null;
  threshold_percent: number;
  spent_amount: number;
  limit_amount: number;
  period_start: string;
  period_end: string;
  is_read: boolean;
  created_at: string;
}

const filterOpts = [
  { value: "false", label: "Unread" },
  { value: "true", label: "Read" },
  { value: "", label: "All" },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("false");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = filter !== "" ? `?is_read=${filter}` : "";
      const data = await apiFetch<BudgetAlert[]>(`/api/v1/alerts${params}`);
      setAlerts(data);
    } catch (e) {
      setError((e as ApiError).detail);
    }
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  async function markRead(id: string) {
    try {
      await apiFetch(`/api/v1/alerts/${id}/read`, { method: "PATCH" });
      load();
    } catch (e) {
      setError((e as ApiError).detail);
    }
  }

  function pctLabel(val: number): string {
    return `${(Number(val) * 100).toFixed(0)}%`;
  }

  function severityColor(pct: number): "red" | "yellow" | "green" {
    const n = Number(pct);
    if (n >= 1.0) return "red";
    if (n >= 0.9) return "yellow";
    return "green";
  }

  return (
    <AppShell>
      <PageHeader title="Budget Alerts" />
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      <Card className="mb-6">
        <div className="flex items-end gap-3">
          <Select label="Filter" options={filterOpts} value={filter} onChange={e => setFilter(e.target.value)} />
          <Button variant="secondary" onClick={load}>Refresh</Button>
        </div>
      </Card>

      {loading ? <Spinner /> : alerts.length === 0 ? (
        <EmptyState message="No alerts to show" />
      ) : (
        <div className="space-y-3">
          {alerts.map(a => (
            <Card key={a.id}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge color={severityColor(a.threshold_percent)}>
                      {pctLabel(a.threshold_percent)} threshold
                    </Badge>
                    {a.is_read && <Badge color="gray">Read</Badge>}
                  </div>
                  <p className="text-sm text-neutral-700">
                    Spent <span className="font-medium tabular-nums">${Number(a.spent_amount).toFixed(2)}</span>
                    {" "}of <span className="font-medium tabular-nums">${Number(a.limit_amount).toFixed(2)}</span> limit
                  </p>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Period: {a.period_start} to {a.period_end} &middot; {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
                {!a.is_read && (
                  <Button variant="secondary" onClick={() => markRead(a.id)} className="text-xs">
                    Mark read
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
