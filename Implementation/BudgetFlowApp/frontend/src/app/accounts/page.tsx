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

interface Account {
  id: string; name: string; type: string; currency: string; balance: number;
  is_active: boolean; institution_id?: string;
  bank_account_number_last4?: string; credit_card_last4?: string; credit_limit?: number; broker_name?: string;
}
interface Institution { id: string; name: string }

const typeOpts = [
  { value: "bank", label: "Bank" },
  { value: "credit", label: "Credit Card" },
  { value: "investment", label: "Investment" },
];

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [showInstForm, setShowInstForm] = useState(false);
  const [instName, setInstName] = useState("");

  const [form, setForm] = useState({ name: "", type: "bank", currency: "USD", balance: "0", institution_id: "", is_active: true, bank_account_number_last4: "", credit_card_last4: "", credit_limit: "", broker_name: "" });
  const [formError, setFormError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, i] = await Promise.all([
        apiFetch<Account[]>("/api/v1/accounts"),
        apiFetch<Institution[]>("/api/v1/institutions"),
      ]);
      setAccounts(a); setInstitutions(i);
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() {
    setForm({ name: "", type: "bank", currency: "USD", balance: "0", institution_id: "", is_active: true, bank_account_number_last4: "", credit_card_last4: "", credit_limit: "", broker_name: "" });
    setEditId(null); setFormError(""); setShowForm(false);
  }

  function openEdit(a: Account) {
    setForm({
      name: a.name, type: a.type, currency: a.currency, balance: String(a.balance),
      institution_id: a.institution_id || "", is_active: a.is_active,
      bank_account_number_last4: a.bank_account_number_last4 || "",
      credit_card_last4: a.credit_card_last4 || "", credit_limit: a.credit_limit ? String(a.credit_limit) : "",
      broker_name: a.broker_name || "",
    });
    setEditId(a.id); setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setFormError("");
    const body: Record<string, unknown> = { name: form.name, type: form.type, currency: form.currency, balance: parseFloat(form.balance) || 0, is_active: form.is_active };
    if (form.institution_id) body.institution_id = form.institution_id;
    if (form.type === "bank" && form.bank_account_number_last4) body.bank_account_number_last4 = form.bank_account_number_last4;
    if (form.type === "credit") { if (form.credit_card_last4) body.credit_card_last4 = form.credit_card_last4; if (form.credit_limit) body.credit_limit = parseFloat(form.credit_limit); }
    if (form.type === "investment" && form.broker_name) body.broker_name = form.broker_name;
    try {
      if (editId) { await apiFetch(`/api/v1/accounts/${editId}`, { method: "PATCH", body }); }
      else { await apiFetch("/api/v1/accounts", { method: "POST", body }); }
      resetForm(); load();
    } catch (e) { setFormError((e as ApiError).detail); }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this account?")) return;
    try { await apiFetch(`/api/v1/accounts/${id}`, { method: "DELETE" }); load(); } catch (e) { setError((e as ApiError).detail); }
  }

  async function createInst(e: React.FormEvent) {
    e.preventDefault();
    try { await apiFetch("/api/v1/institutions", { method: "POST", body: { name: instName } }); setInstName(""); setShowInstForm(false); load(); } catch (e) { setFormError((e as ApiError).detail); }
  }

  const instOpts = [{ value: "", label: "None" }, ...institutions.map(i => ({ value: i.id, label: i.name }))];

  return (
    <AppShell>
      <PageHeader title="Accounts">
        <Button onClick={() => { resetForm(); setShowForm(true); }}>New Account</Button>
      </PageHeader>
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}
      {loading ? <Spinner /> : accounts.length === 0 ? <EmptyState message="No accounts yet" /> : (
        <div className="space-y-3">
          {accounts.map(a => (
            <Card key={a.id} className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <p className="font-medium text-neutral-900">{a.name}</p>
                  <p className="text-xs text-neutral-500">{a.type} · {a.currency}</p>
                </div>
                <Badge color={a.is_active ? "green" : "gray"}>{a.is_active ? "Active" : "Inactive"}</Badge>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">${Number(a.balance).toFixed(2)}</span>
                <Button variant="ghost" onClick={() => openEdit(a)}>Edit</Button>
                <Button variant="danger" onClick={() => handleDelete(a.id)}>Delete</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showForm} onClose={resetForm} title={editId ? "Edit Account" : "New Account"}>
        {formError && <div className="mb-3"><Alert>{formError}</Alert></div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <Input label="Name" value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} required />
          {!editId && <Select label="Type" options={typeOpts} value={form.type} onChange={e => setForm(p => ({...p, type: e.target.value}))} />}
          <Input label="Currency" value={form.currency} onChange={e => setForm(p => ({...p, currency: e.target.value}))} maxLength={3} />
          <Input label="Balance" type="number" step="0.01" value={form.balance} onChange={e => setForm(p => ({...p, balance: e.target.value}))} />
          <div className="flex items-end gap-2">
            <div className="flex-1"><Select label="Institution" options={instOpts} value={form.institution_id} onChange={e => setForm(p => ({...p, institution_id: e.target.value}))} /></div>
            <Button type="button" variant="secondary" onClick={() => setShowInstForm(true)}>+</Button>
          </div>
          {form.type === "bank" && <Input label="Last 4 digits" value={form.bank_account_number_last4} onChange={e => setForm(p => ({...p, bank_account_number_last4: e.target.value}))} maxLength={4} />}
          {form.type === "credit" && <>
            <Input label="Card last 4" value={form.credit_card_last4} onChange={e => setForm(p => ({...p, credit_card_last4: e.target.value}))} maxLength={4} />
            <Input label="Credit limit" type="number" value={form.credit_limit} onChange={e => setForm(p => ({...p, credit_limit: e.target.value}))} />
          </>}
          {form.type === "investment" && <Input label="Broker name" value={form.broker_name} onChange={e => setForm(p => ({...p, broker_name: e.target.value}))} />}
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({...p, is_active: e.target.checked}))} /> Active
          </label>
          <Button type="submit" className="w-full">{editId ? "Update" : "Create"}</Button>
        </form>
      </Modal>

      <Modal open={showInstForm} onClose={() => setShowInstForm(false)} title="New Institution">
        <form onSubmit={createInst} className="space-y-3">
          <Input label="Institution Name" value={instName} onChange={e => setInstName(e.target.value)} required />
          <Button type="submit" className="w-full">Create</Button>
        </form>
      </Modal>
    </AppShell>
  );
}
