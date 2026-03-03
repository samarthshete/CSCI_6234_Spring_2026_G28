"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Alert from "@/components/ui/Alert";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import PageHeader from "@/components/ui/PageHeader";
import { apiFetch, ApiError } from "@/lib/api";

interface BudgetItem { id: string; category_id: string; limit_amount: number }
interface Budget { id: string; name: string; period_start: string; period_end: string; period_type: string; thresholds: number[]; items: BudgetItem[] }
interface Category { id: string; name: string }

const periodOpts = [
  { value: "monthly", label: "Monthly" }, { value: "weekly", label: "Weekly" }, { value: "custom", label: "Custom" },
];

export default function BudgetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [budget, setBudget] = useState<Budget | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", period_start: "", period_end: "", period_type: "monthly", thresholds: "" });
  const [items, setItems] = useState<{ category_id: string; limit_amount: string }[]>([]);
  const [formError, setFormError] = useState("");
  const itemsModified = useRef(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, c] = await Promise.all([
        apiFetch<Budget>(`/api/v1/budgets/${id}`),
        apiFetch<Category[]>("/api/v1/categories"),
      ]);
      setBudget(b); setCategories(c);
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, [id]);

  useEffect(() => { load(); }, [load]);

  function startEdit() {
    if (!budget) return;
    setForm({
      name: budget.name,
      period_start: budget.period_start,
      period_end: budget.period_end,
      period_type: budget.period_type,
      thresholds: budget.thresholds.join(","),
    });
    setItems(budget.items.map(i => ({ category_id: i.category_id, limit_amount: String(i.limit_amount) })));
    itemsModified.current = false;
    setFormError("");
    setEditing(true);
  }

  function addItem() {
    itemsModified.current = true;
    setItems(i => [...i, { category_id: categories[0]?.id || "", limit_amount: "" }]);
  }
  function removeItem(i: number) {
    itemsModified.current = true;
    setItems(arr => arr.filter((_, idx) => idx !== i));
  }
  function updateItem(i: number, field: "category_id" | "limit_amount", val: string) {
    itemsModified.current = true;
    setItems(arr => arr.map((x, idx) => idx === i ? { ...x, [field]: val } : x));
  }

  const catOpts = categories.map(c => ({ value: c.id, label: c.name }));
  const catMap = Object.fromEntries(categories.map(c => [c.id, c.name]));

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    const thresholds = form.thresholds.split(",").map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
    const body: Record<string, unknown> = {
      name: form.name,
      period_start: form.period_start,
      period_end: form.period_end,
      period_type: form.period_type,
      thresholds,
    };
    if (itemsModified.current) {
      const catIds = items.map(i => i.category_id);
      if (new Set(catIds).size !== catIds.length) { setFormError("Duplicate categories in items"); return; }
      for (const it of items) {
        if (!it.limit_amount || parseFloat(it.limit_amount) <= 0) { setFormError("All limit amounts must be > 0"); return; }
      }
      body.items = items.map(i => ({ category_id: i.category_id, limit_amount: parseFloat(i.limit_amount) }));
    }
    try {
      await apiFetch(`/api/v1/budgets/${id}`, { method: "PATCH", body });
      setEditing(false);
      load();
    } catch (e) { setFormError((e as ApiError).detail); }
  }

  async function handleDelete() {
    if (!confirm("Delete this budget?")) return;
    try {
      await apiFetch(`/api/v1/budgets/${id}`, { method: "DELETE" });
      router.push("/budgets");
    } catch (e) { setError((e as ApiError).detail); }
  }

  if (loading) return <AppShell><Spinner /></AppShell>;
  if (error) return <AppShell><Alert>{error}</Alert></AppShell>;
  if (!budget) return <AppShell><Alert>Budget not found</Alert></AppShell>;

  return (
    <AppShell>
      <PageHeader title={budget.name}>
        {!editing && <>
          <Button variant="secondary" onClick={startEdit}>Edit</Button>
          <Button variant="danger" onClick={handleDelete}>Delete</Button>
        </>}
      </PageHeader>

      {!editing ? (
        <>
          <Card className="mb-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-neutral-500">Period:</span> {budget.period_start} — {budget.period_end}</div>
              <div><span className="text-neutral-500">Type:</span> <Badge color="blue">{budget.period_type}</Badge></div>
              <div><span className="text-neutral-500">Thresholds:</span> {budget.thresholds.map(t => `${(t * 100).toFixed(0)}%`).join(", ")}</div>
            </div>
          </Card>
          <h2 className="mb-3 text-lg font-medium text-neutral-700">Items</h2>
          {budget.items.length === 0 ? <p className="text-sm text-neutral-400">No items</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b text-left text-xs font-medium text-neutral-500">
                  <th className="pb-2 pr-4">Category</th><th className="pb-2">Limit</th>
                </tr></thead>
                <tbody>{budget.items.map(i => (
                  <tr key={i.id} className="border-b border-neutral-100">
                    <td className="py-2 pr-4">{catMap[i.category_id] || i.category_id}</td>
                    <td className="py-2 tabular-nums">${Number(i.limit_amount).toFixed(2)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </>
      ) : (
        <Card>
          {formError && <div className="mb-3"><Alert>{formError}</Alert></div>}
          <form onSubmit={handleSave} className="space-y-3">
            <Input label="Name" value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))} required />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Start" type="date" value={form.period_start} onChange={e => setForm(f => ({...f, period_start: e.target.value}))} />
              <Input label="End" type="date" value={form.period_end} onChange={e => setForm(f => ({...f, period_end: e.target.value}))} />
            </div>
            <Select label="Period Type" options={periodOpts} value={form.period_type} onChange={e => setForm(f => ({...f, period_type: e.target.value}))} />
            <Input label="Thresholds" value={form.thresholds} onChange={e => setForm(f => ({...f, thresholds: e.target.value}))} />
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-neutral-700">Items {itemsModified.current ? "" : "(unchanged)"}</label>
                <Button type="button" variant="secondary" onClick={addItem} className="text-xs">Add Item</Button>
              </div>
              {items.map((it, i) => (
                <div key={i} className="mb-2 flex items-end gap-2">
                  <div className="flex-1"><Select options={catOpts} value={it.category_id} onChange={e => updateItem(i, "category_id", e.target.value)} /></div>
                  <div className="w-32"><Input type="number" step="0.01" placeholder="Limit" value={it.limit_amount} onChange={e => updateItem(i, "limit_amount", e.target.value)} /></div>
                  <Button type="button" variant="danger" onClick={() => removeItem(i)} className="text-xs">×</Button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button type="submit">Save</Button>
              <Button type="button" variant="secondary" onClick={() => setEditing(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}
    </AppShell>
  );
}
