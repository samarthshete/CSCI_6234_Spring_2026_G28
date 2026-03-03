"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
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
import Modal from "@/components/ui/Modal";
import { apiFetch, ApiError } from "@/lib/api";

interface BudgetItem { id?: string; category_id: string; limit_amount: number }
interface Budget { id: string; name: string; period_start: string; period_end: string; period_type: string; thresholds: number[]; items: BudgetItem[] }
interface Category { id: string; name: string; user_id: string | null }

const periodOpts = [
  { value: "monthly", label: "Monthly" },
  { value: "weekly", label: "Weekly" },
  { value: "custom", label: "Custom" },
];

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", period_start: "", period_end: "", period_type: "monthly", thresholds: "0.8,0.9,1.0" });
  const [items, setItems] = useState<{ category_id: string; limit_amount: string }[]>([]);
  const [formError, setFormError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, c] = await Promise.all([
        apiFetch<Budget[]>("/api/v1/budgets"),
        apiFetch<Category[]>("/api/v1/categories"),
      ]);
      setBudgets(b); setCategories(c);
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() {
    setForm({ name: "", period_start: "", period_end: "", period_type: "monthly", thresholds: "0.8,0.9,1.0" });
    setItems([]); setFormError(""); setShowForm(false);
  }

  function addItem() { setItems(i => [...i, { category_id: categories[0]?.id || "", limit_amount: "" }]); }
  function removeItem(i: number) { setItems(arr => arr.filter((_, idx) => idx !== i)); }

  const catOpts = categories.map(c => ({ value: c.id, label: c.name }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setFormError("");
    const thresholds = form.thresholds.split(",").map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
    const catIds = items.map(i => i.category_id);
    if (new Set(catIds).size !== catIds.length) { setFormError("Duplicate categories in items"); return; }
    for (const it of items) {
      if (!it.limit_amount || parseFloat(it.limit_amount) <= 0) { setFormError("All limit amounts must be > 0"); return; }
    }
    const body = {
      name: form.name,
      period_start: form.period_start,
      period_end: form.period_end,
      period_type: form.period_type,
      thresholds,
      items: items.map(i => ({ category_id: i.category_id, limit_amount: parseFloat(i.limit_amount) })),
    };
    try {
      await apiFetch("/api/v1/budgets", { method: "POST", body });
      resetForm(); load();
    } catch (e) { setFormError((e as ApiError).detail); }
  }

  const catMap = Object.fromEntries(categories.map(c => [c.id, c.name]));

  return (
    <AppShell>
      <PageHeader title="Budgets">
        <Button onClick={() => { resetForm(); setShowForm(true); }}>New Budget</Button>
      </PageHeader>
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {loading ? <Spinner /> : budgets.length === 0 ? <EmptyState message="No budgets yet" /> : (
        <div className="grid gap-4 sm:grid-cols-2">
          {budgets.map(b => (
            <Link key={b.id} href={`/budgets/${b.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-neutral-900">{b.name}</p>
                  <Badge color="blue">{b.period_type}</Badge>
                </div>
                <p className="text-xs text-neutral-500">{b.period_start} — {b.period_end}</p>
                <p className="mt-1 text-xs text-neutral-400">{b.items.length} item(s)</p>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Modal open={showForm} onClose={resetForm} title="New Budget">
        {formError && <div className="mb-3"><Alert>{formError}</Alert></div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input label="Name" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Start" type="date" value={form.period_start} onChange={e => setForm(f => ({...f, period_start: e.target.value}))} required />
            <Input label="End" type="date" value={form.period_end} onChange={e => setForm(f => ({...f, period_end: e.target.value}))} required />
          </div>
          <Select label="Period Type" options={periodOpts} value={form.period_type} onChange={e => setForm(f => ({...f, period_type: e.target.value}))} />
          <Input label="Thresholds (comma-separated)" value={form.thresholds} onChange={e => setForm(f => ({...f, thresholds: e.target.value}))} placeholder="0.8,0.9,1.0" />
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-neutral-700">Budget Items</label>
              <Button type="button" variant="secondary" onClick={addItem} className="text-xs">Add Item</Button>
            </div>
            {items.map((it, i) => (
              <div key={i} className="mb-2 flex items-end gap-2">
                <div className="flex-1"><Select label={i === 0 ? "Category" : undefined} options={catOpts} value={it.category_id} onChange={e => setItems(arr => arr.map((x, idx) => idx === i ? {...x, category_id: e.target.value} : x))} /></div>
                <div className="w-32"><Input type="number" step="0.01" placeholder="Limit" value={it.limit_amount} onChange={e => setItems(arr => arr.map((x, idx) => idx === i ? {...x, limit_amount: e.target.value} : x))} /></div>
                <Button type="button" variant="danger" onClick={() => removeItem(i)} className="text-xs">×</Button>
              </div>
            ))}
          </div>
          <Button type="submit" className="w-full">Create Budget</Button>
        </form>
      </Modal>
    </AppShell>
  );
}
