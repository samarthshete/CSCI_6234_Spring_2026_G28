"use client";
import { useEffect, useState, useCallback, useRef } from "react";
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

interface Account { id: string; name: string; type: string }
interface Session {
  id: string; account_id: string; status: string; total_rows: number;
  imported_count: number; duplicate_count: number; failed_count: number;
  started_at: string; row_errors?: { row: number; message: string }[];
}

interface ImportQueuedResponse {
  import_session_id: string;
  job_id: string;
  status: string;
}

const POLL_INTERVAL_MS = 1500;

export default function ImportPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [detail, setDetail] = useState<Session | null>(null);
  const defaultSet = useRef(false);
  const pollIntervalsRef = useRef<ReturnType<typeof setInterval>[]>([]);

  useEffect(() => {
    return () => { pollIntervalsRef.current.forEach(clearInterval); };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([
        apiFetch<Account[]>("/api/v1/accounts"),
        apiFetch<Session[]>("/api/v1/transactions/import/sessions"),
      ]);
      setAccounts(a);
      setSessions(s);
      if (a.length && !defaultSet.current) {
        defaultSet.current = true;
        setAccountId(a[0].id);
      }
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function pollSessionUntilDone(sessionId: string) {
    const interval = setInterval(async () => {
      try {
        const s = await apiFetch<Session>(`/api/v1/transactions/import/sessions/${sessionId}`);
        setSessions((prev) => prev.map((x) => (x.id === sessionId ? s : x)));
        setResult((r) => (r?.id === sessionId ? s : r));
        if (s.status === "completed" || s.status === "failed") {
          clearInterval(interval);
          pollIntervalsRef.current = pollIntervalsRef.current.filter((i) => i !== interval);
        }
      } catch {
        clearInterval(interval);
        pollIntervalsRef.current = pollIntervalsRef.current.filter((i) => i !== interval);
      }
    }, POLL_INTERVAL_MS);
    pollIntervalsRef.current.push(interval);
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !accountId) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("account_id", accountId);
      fd.append("file", file);
      const res = await apiFetch<ImportQueuedResponse>("/api/v1/transactions/import", { method: "POST", formData: fd });
      setFile(null);
      const newSession = await apiFetch<Session>(`/api/v1/transactions/import/sessions/${res.import_session_id}`);
      setResult(newSession);
      setSessions((prev) => [newSession, ...prev]);
      pollSessionUntilDone(res.import_session_id);
    } catch (e) { setError((e as ApiError).detail); }
    setUploading(false);
  }

  async function loadDetail(id: string) {
    try {
      const s = await apiFetch<Session>(`/api/v1/transactions/import/sessions/${id}`);
      setDetail(s);
    } catch (e) { setError((e as ApiError).detail); }
  }

  const acctOpts = accounts.map(a => ({ value: a.id, label: `${a.name} (${a.type})` }));

  function SessionCard({ s }: { s: Session }) {
    const isPending = s.status === "queued" || s.status === "processing";
    return (
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => loadDetail(s.id)}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{new Date(s.started_at).toLocaleString()}</p>
            <p className="text-xs text-neutral-500">Rows: {s.total_rows} · Imported: {s.imported_count} · Duplicates: {s.duplicate_count} · Failed: {s.failed_count}</p>
          </div>
          <div className="flex items-center gap-2">
            {isPending && <Spinner />}
            <Badge color={s.status === "completed" ? "green" : s.status === "failed" ? "red" : "yellow"}>{s.status}</Badge>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <AppShell>
      <PageHeader title="Import Transactions" />
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {loading ? <Spinner /> : (
        <>
          <Card className="mb-6">
            <form onSubmit={handleUpload} className="space-y-4">
              {acctOpts.length > 0 ? (
                <Select label="Account" options={acctOpts} value={accountId} onChange={e => setAccountId(e.target.value)} />
              ) : (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
                  <p className="font-medium text-amber-800">No accounts found</p>
                  <p className="mt-1 text-amber-700">You need to create an account before importing transactions.</p>
                  <a href="/accounts" className="mt-2 inline-block text-sm font-medium text-amber-900 underline hover:no-underline">
                    Go to Accounts &rarr;
                  </a>
                </div>
              )}
              <div className="space-y-1">
                <label className="block text-sm font-medium text-neutral-700">CSV File</label>
                <input type="file" accept=".csv" onChange={e => setFile(e.target.files?.[0] || null)} className="text-sm" />
              </div>
              <Button type="submit" loading={uploading} disabled={!file || !accountId}>Upload</Button>
            </form>
          </Card>

          {result && (
            <Card className="mb-6">
              <h3 className="mb-2 font-medium text-neutral-900">Import Result</h3>
              <div className="flex items-center gap-2">
                {(result.status === "queued" || result.status === "processing") && <Spinner />}
                <p className="text-sm">Status: <Badge color={result.status === "completed" ? "green" : result.status === "failed" ? "red" : "yellow"}>{result.status}</Badge></p>
              </div>
              <p className="text-sm">Imported: {result.imported_count} · Duplicates: {result.duplicate_count} · Failed: {result.failed_count}</p>
              {result.row_errors && result.row_errors.length > 0 && (
                <div className="mt-2 max-h-40 overflow-auto rounded border p-2 text-xs">
                  {result.row_errors.slice(0, 50).map((re, i) => <p key={i}>Row {re.row}: {re.message}</p>)}
                </div>
              )}
            </Card>
          )}

          {detail && (
            <Card className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-neutral-900">Session Detail</h3>
                <button onClick={() => setDetail(null)} className="text-neutral-400 hover:text-neutral-600 text-sm">Close</button>
              </div>
              <p className="text-sm">Status: <Badge color={detail.status === "completed" ? "green" : "red"}>{detail.status}</Badge></p>
              <p className="text-sm">Total: {detail.total_rows} · Imported: {detail.imported_count} · Dup: {detail.duplicate_count} · Failed: {detail.failed_count}</p>
              {detail.row_errors && detail.row_errors.length > 0 && (
                <div className="mt-2 max-h-40 overflow-auto rounded border p-2 text-xs">
                  {detail.row_errors.slice(0, 50).map((re, i) => <p key={i}>Row {re.row}: {re.message}</p>)}
                </div>
              )}
            </Card>
          )}

          <h2 className="mb-3 text-lg font-medium text-neutral-700">Previous Sessions</h2>
          {sessions.length === 0 ? <EmptyState message="No import sessions yet" /> : (
            <div className="space-y-3">{sessions.map(s => <SessionCard key={s.id} s={s} />)}</div>
          )}
        </>
      )}
    </AppShell>
  );
}
