"use client";
import { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Select from "@/components/ui/Select";
import Input from "@/components/ui/Input";
import Badge from "@/components/ui/Badge";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import PageHeader from "@/components/ui/PageHeader";
import { apiFetch, ApiError } from "@/lib/api";

interface Tx {
  id: string; posted_date: string; description: string; amount: number;
  currency: string; category_id: string | null; merchant_id: string | null;
  needs_manual: boolean; categorization_source: string | null;
  category_confidence: number | null; account_id: string;
}
interface Category { id: string; name: string; user_id: string | null }
interface Account { id: string; name: string }

export default function TransactionsPage() {
  const [txs, setTxs] = useState<Tx[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterAcct, setFilterAcct] = useState("");
  const [filterCat, setFilterCat] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterAcct) params.set("account_id", filterAcct);
      if (filterCat) params.set("category_id", filterCat);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const qs = params.toString() ? `?${params}` : "";
      const [t, c, a] = await Promise.all([
        apiFetch<Tx[]>(`/api/v1/transactions${qs}`),
        apiFetch<Category[]>("/api/v1/categories"),
        apiFetch<Account[]>("/api/v1/accounts"),
      ]);
      setTxs(t); setCategories(c); setAccounts(a);
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, [filterAcct, filterCat, dateFrom, dateTo]);

  useEffect(() => { load(); }, [load]);

  const catMap = Object.fromEntries(categories.map(c => [c.id, c.name]));
  const acctOpts = [{ value: "", label: "All accounts" }, ...accounts.map(a => ({ value: a.id, label: a.name }))];
  const catOpts = [{ value: "", label: "All categories" }, ...categories.map(c => ({ value: c.id, label: c.name }))];

  async function categorize(txId: string, catId?: string) {
    try {
      const body = catId ? { category_id: catId } : undefined;
      await apiFetch(`/api/v1/transactions/${txId}/categorize`, { method: "POST", body });
      load();
    } catch (e) { setError((e as ApiError).detail); }
  }

  return (
    <AppShell>
      <PageHeader title="Transactions" />
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      <Card className="mb-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Select label="Account" options={acctOpts} value={filterAcct} onChange={e => setFilterAcct(e.target.value)} />
          <Select label="Category" options={catOpts} value={filterCat} onChange={e => setFilterCat(e.target.value)} />
          <Input label="From" type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <Input label="To" type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
        </div>
      </Card>

      {loading ? <Spinner /> : txs.length === 0 ? <EmptyState message="No transactions found" /> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-medium text-neutral-500">
                <th className="pb-2 pr-4">Date</th>
                <th className="pb-2 pr-4">Description</th>
                <th className="pb-2 pr-4">Amount</th>
                <th className="pb-2 pr-4">Category</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {txs.map(tx => (
                <tr key={tx.id} className="border-b border-neutral-100">
                  <td className="py-3 pr-4 text-neutral-600">{tx.posted_date}</td>
                  <td className="py-3 pr-4 font-medium">{tx.description}</td>
                  <td className="py-3 pr-4 tabular-nums">{tx.currency} {Number(tx.amount).toFixed(2)}</td>
                  <td className="py-3 pr-4">{tx.category_id ? catMap[tx.category_id] || "—" : "—"}</td>
                  <td className="py-3 pr-4">
                    {tx.needs_manual && <Badge color="yellow">Needs manual</Badge>}
                    {tx.categorization_source === "rule" && <Badge color="blue">Rule</Badge>}
                    {tx.categorization_source === "manual" && <Badge color="purple">Manual</Badge>}
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      {(tx.needs_manual || !tx.category_id) && (
                        <select
                          className="rounded border px-2 py-1 text-xs"
                          defaultValue=""
                          onChange={e => { if (e.target.value) categorize(tx.id, e.target.value); }}
                        >
                          <option value="">Assign...</option>
                          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                      )}
                      <Button variant="ghost" onClick={() => categorize(tx.id)} className="text-xs">Run rules</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
