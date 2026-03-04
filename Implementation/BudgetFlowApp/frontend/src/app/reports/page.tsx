"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Alert from "@/components/ui/Alert";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import PageHeader from "@/components/ui/PageHeader";
import { apiFetch, ApiError } from "@/lib/api";

interface Report {
  id: string;
  type: string;
  format: string;
  from_date: string;
  to_date: string;
  status: string;
  error: string | null;
  download_url: string | null;
  job_id: string | null;
  job_status: string | null;
  created_at: string;
  completed_at: string | null;
}

const typeOpts = [
  { value: "monthly_summary", label: "Monthly Summary" },
  { value: "category_breakdown", label: "Category Breakdown" },
  { value: "budget_vs_actual", label: "Budget vs Actual" },
  { value: "transactions", label: "Transactions" },
];

const formatOpts = [
  { value: "csv", label: "CSV" },
  { value: "pdf", label: "PDF" },
];

const statusColors: Record<string, "green" | "red" | "yellow" | "gray"> = {
  succeeded: "green",
  failed: "red",
  running: "yellow",
  pending: "yellow",
  queued: "gray",
};

export default function ReportsPage() {
  const now = new Date();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const [reportType, setReportType] = useState("monthly_summary");
  const [format, setFormat] = useState("csv");
  const [fromDate, setFromDate] = useState(new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10));
  const [toDate, setToDate] = useState(now.toISOString().slice(0, 10));
  const pollIntervalsRef = useRef<ReturnType<typeof setInterval>[]>([]);

  useEffect(() => {
    return () => { pollIntervalsRef.current.forEach(clearInterval); };
  }, []);

  const loadReports = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Report[]>("/api/v1/reports");
      setReports(data);
    } catch (e) {
      setError((e as ApiError).detail);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadReports(); }, [loadReports]);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    setError("");
    try {
      const report = await apiFetch<Report>("/api/v1/reports", {
        method: "POST",
        body: {
          type: reportType,
          format,
          from_date: fromDate,
          to_date: toDate,
        },
      });
      setReports(prev => [report, ...prev]);
      pollReportUntilDone(report.id);
    } catch (e) {
      setError((e as ApiError).detail);
    }
    setGenerating(false);
  }

  function pollReportUntilDone(reportId: string) {
    const interval = setInterval(async () => {
      try {
        const report = await apiFetch<Report>(`/api/v1/reports/${reportId}`);
        setReports(prev => prev.map(r => r.id === reportId ? report : r));
        if (report.status === "succeeded" || report.status === "failed") {
          clearInterval(interval);
          pollIntervalsRef.current = pollIntervalsRef.current.filter(i => i !== interval);
        }
      } catch {
        clearInterval(interval);
        pollIntervalsRef.current = pollIntervalsRef.current.filter(i => i !== interval);
      }
    }, 1500);
    pollIntervalsRef.current.push(interval);
  }

  function formatLabel(type: string): string {
    return type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }

  return (
    <AppShell>
      <PageHeader title="Reports" />
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      <Card className="mb-6">
        <h3 className="mb-3 text-sm font-medium text-neutral-700">Generate Report</h3>
        <form onSubmit={handleGenerate} className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Select label="Report Type" options={typeOpts} value={reportType} onChange={e => setReportType(e.target.value)} />
            <Select label="Format" options={formatOpts} value={format} onChange={e => setFormat(e.target.value)} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="From" type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} required />
            <Input label="To" type="date" value={toDate} onChange={e => setToDate(e.target.value)} required />
          </div>
          <Button type="submit" loading={generating}>Generate</Button>
        </form>
      </Card>

      <h2 className="mb-3 text-lg font-medium text-neutral-700">Generated Reports</h2>
      {loading ? <Spinner /> : reports.length === 0 ? (
        <EmptyState message="No reports generated yet" />
      ) : (
        <div className="space-y-3">
          {reports.map(r => {
            const isPending = r.status === "queued" && (r.job_status === "pending" || r.job_status === "running");
            return (
              <Card key={r.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium text-neutral-900">{formatLabel(r.type)}</p>
                      <Badge color={statusColors[r.status] || statusColors[r.job_status || ""] || "gray"}>
                        {r.job_status || r.status}
                      </Badge>
                      <Badge color="blue">{r.format.toUpperCase()}</Badge>
                      {isPending && <Spinner />}
                    </div>
                    <p className="text-xs text-neutral-500">
                      {r.from_date} to {r.to_date} &middot; {new Date(r.created_at).toLocaleString()}
                    </p>
                    {r.error && <p className="mt-1 text-xs text-red-600">{r.error}</p>}
                  </div>
                  {r.download_url && r.status === "succeeded" && (
                    <a
                      href={r.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-50"
                    >
                      Download
                    </a>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
