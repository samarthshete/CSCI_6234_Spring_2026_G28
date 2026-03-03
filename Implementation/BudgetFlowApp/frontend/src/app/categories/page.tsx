"use client";
import { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/AppShell";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Badge from "@/components/ui/Badge";
import Alert from "@/components/ui/Alert";
import Spinner from "@/components/ui/Spinner";
import EmptyState from "@/components/ui/EmptyState";
import PageHeader from "@/components/ui/PageHeader";
import Modal from "@/components/ui/Modal";
import { apiFetch, ApiError } from "@/lib/api";

interface Rule { pattern: string; match: string; priority: number }
interface Category { id: string; name: string; type: string; user_id: string | null; rules: Rule[] }

const typeOpts = [{ value: "expense", label: "Expense" }, { value: "income", label: "Income" }];
const matchOpts = [{ value: "contains", label: "Contains" }, { value: "regex", label: "Regex" }];

export default function CategoriesPage() {
  const [cats, setCats] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editCat, setEditCat] = useState<Category | null>(null);
  const [name, setName] = useState("");
  const [type, setType] = useState("expense");
  const [rules, setRules] = useState<Rule[]>([]);
  const [formError, setFormError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { setCats(await apiFetch<Category[]>("/api/v1/categories")); } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function openCreate() { setEditCat(null); setName(""); setType("expense"); setRules([]); setFormError(""); setShowForm(true); }
  function openEdit(c: Category) { setEditCat(c); setName(c.name); setType(c.type); setRules([...c.rules]); setFormError(""); setShowForm(true); }

  function addRule() { setRules(r => [...r, { pattern: "", match: "contains", priority: 100 }]); }
  function removeRule(i: number) { setRules(r => r.filter((_, idx) => idx !== i)); }
  function updateRule(i: number, field: keyof Rule, val: string | number) {
    setRules(r => r.map((rule, idx) => idx === i ? { ...rule, [field]: val } : rule));
  }

  function validateRegex(pattern: string): boolean {
    try { new RegExp(pattern); return true; } catch { return false; }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setFormError("");
    for (const r of rules) {
      if (r.match === "regex" && !validateRegex(r.pattern)) {
        setFormError(`Invalid regex pattern: ${r.pattern}`); return;
      }
    }
    try {
      if (editCat) {
        await apiFetch(`/api/v1/categories/${editCat.id}`, { method: "PATCH", body: { name, type, rules } });
      } else {
        await apiFetch("/api/v1/categories", { method: "POST", body: { name, type, rules } });
      }
      setShowForm(false); load();
    } catch (e) { setFormError((e as ApiError).detail); }
  }

  return (
    <AppShell>
      <PageHeader title="Categories">
        <Button onClick={openCreate}>New Category</Button>
      </PageHeader>
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {loading ? <Spinner /> : cats.length === 0 ? <EmptyState message="No categories" /> : (
        <div className="space-y-3">
          {cats.map(c => (
            <Card key={c.id} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div>
                  <p className="font-medium text-neutral-900">{c.name}</p>
                  <p className="text-xs text-neutral-500">{c.type} · {c.rules.length} rule(s)</p>
                </div>
                {!c.user_id && <Badge color="blue">System</Badge>}
              </div>
              {c.user_id && (
                <Button variant="ghost" onClick={() => openEdit(c)}>Edit</Button>
              )}
            </Card>
          ))}
        </div>
      )}

      <Modal open={showForm} onClose={() => setShowForm(false)} title={editCat ? "Edit Category" : "New Category"}>
        {formError && <div className="mb-3"><Alert>{formError}</Alert></div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Name" value={name} onChange={e => setName(e.target.value)} required />
          <Select label="Type" options={typeOpts} value={type} onChange={e => setType(e.target.value)} />
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-neutral-700">Rules</label>
              <Button type="button" variant="secondary" onClick={addRule} className="text-xs">Add Rule</Button>
            </div>
            {rules.length === 0 && <p className="text-xs text-neutral-400">No rules defined</p>}
            {rules.map((r, i) => (
              <div key={i} className="mb-2 flex items-end gap-2">
                <div className="flex-1"><Input label={i === 0 ? "Pattern" : undefined} value={r.pattern} onChange={e => updateRule(i, "pattern", e.target.value)} placeholder="Pattern" /></div>
                <div className="w-28"><Select options={matchOpts} value={r.match} onChange={e => updateRule(i, "match", e.target.value)} /></div>
                <div className="w-20"><Input type="number" value={String(r.priority)} onChange={e => updateRule(i, "priority", parseInt(e.target.value) || 100)} /></div>
                <Button type="button" variant="danger" onClick={() => removeRule(i)} className="text-xs">×</Button>
              </div>
            ))}
          </div>
          <Button type="submit" className="w-full">{editCat ? "Update" : "Create"}</Button>
        </form>
      </Modal>
    </AppShell>
  );
}
