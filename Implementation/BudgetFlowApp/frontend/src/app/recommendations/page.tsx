"use client";
import { useEffect, useState, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
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

interface AllocationSlice { asset: string; ticker: string; pct: number; rationale: string }
interface ProjectionPoint { month: number; median: number; p10: number; p90: number }
interface RecItem { id: string; priority: number; type: string; title: string; details: Record<string, unknown> | null; confidence: number }
interface RunOutputs {
  needs_profile: boolean;
  risk_bucket: string | null;
  risk_score: number | null;
  monthly_spending_avg: number;
  emergency_fund_months: number;
  investable_monthly: number;
  cashflow_positive: boolean;
  safety_warnings: string[];
  allocation: AllocationSlice[];
  projection: ProjectionPoint[];
}
interface Run { id: string; status: string; outputs: RunOutputs | null; items: RecItem[]; created_at: string }
interface RunListItem { id: string; status: string; created_at: string }

const Q_LABELS: Record<string, string> = {
  market_drop_reaction: "If the market dropped 20%, I would:",
  investment_experience: "My investment experience level:",
  income_stability: "My income stability:",
  loss_tolerance_pct: "Maximum acceptable loss in a year:",
  goal_priority: "My primary goal:",
};
const Q_OPTIONS: Record<string, string[]> = {
  market_drop_reaction: ["Sell everything", "Sell some", "Hold", "Buy a little more", "Buy aggressively"],
  investment_experience: ["None", "Beginner", "Intermediate", "Advanced", "Expert"],
  income_stability: ["Very unstable", "Somewhat unstable", "Average", "Stable", "Very stable"],
  loss_tolerance_pct: ["0% loss", "Up to 5%", "Up to 10%", "Up to 20%", "30%+"],
  goal_priority: ["Preserve capital", "Income focus", "Balanced", "Growth focus", "Maximum growth"],
};

const HORIZON_OPTS = [
  { value: "12", label: "1 year" }, { value: "24", label: "2 years" },
  { value: "36", label: "3 years" }, { value: "60", label: "5 years" },
  { value: "120", label: "10 years" }, { value: "240", label: "20 years" },
];

const LIQUIDITY_OPTS = [
  { value: "low", label: "Low (rarely need cash)" },
  { value: "moderate", label: "Moderate" },
  { value: "high", label: "High (may need cash soon)" },
];

const ITEM_ICONS: Record<string, string> = {
  emergency_fund: "🛡", reduce_spending: "✂", stabilize: "⚠",
  invest: "📈", continue_saving: "💰", increase_income: "💡",
};

function fmt$(n: number) { return `$${n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`; }

export default function RecommendationsPage() {
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [answers, setAnswers] = useState<Record<string, number>>({
    market_drop_reaction: 3, investment_experience: 2,
    income_stability: 3, loss_tolerance_pct: 2, goal_priority: 3,
  });
  const [horizon, setHorizon] = useState("60");
  const [liquidity, setLiquidity] = useState("moderate");

  const loadRuns = useCallback(async () => {
    try {
      const data = await apiFetch<RunListItem[]>("/api/v1/recommendations/runs");
      setRuns(data);
    } catch (e) { setError((e as ApiError).detail); }
    setLoading(false);
  }, []);

  useEffect(() => { loadRuns(); }, [loadRuns]);

  async function loadRun(id: string) {
    try {
      const data = await apiFetch<Run>(`/api/v1/recommendations/runs/${id}`);
      setActiveRun(data);
    } catch (e) { setError((e as ApiError).detail); }
  }

  async function generate() {
    setGenerating(true);
    setError("");
    try {
      const body = showForm ? {
        risk_profile: { answers, horizon_months: parseInt(horizon), liquidity_need: liquidity },
      } : {};
      const data = await apiFetch<Run>("/api/v1/recommendations/run", { method: "POST", body });
      setActiveRun(data);
      loadRuns();
    } catch (e) { setError((e as ApiError).detail); }
    setGenerating(false);
  }

  const o = activeRun?.outputs;

  return (
    <AppShell>
      <PageHeader title="Investment Recommendations" />
      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {/* Generate section */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-neutral-700">Generate Recommendation</h3>
          <button onClick={() => setShowForm(!showForm)} className="text-xs text-blue-600 hover:underline">
            {showForm ? "Skip questionnaire" : "Fill risk profile"}
          </button>
        </div>

        {showForm && (
          <div className="mb-4 space-y-4">
            {Object.entries(Q_LABELS).map(([key, label]) => (
              <div key={key}>
                <p className="text-sm font-medium text-neutral-700 mb-1">{label}</p>
                <div className="flex gap-2 flex-wrap">
                  {Q_OPTIONS[key].map((opt, i) => (
                    <button
                      key={i}
                      onClick={() => setAnswers(a => ({ ...a, [key]: i + 1 }))}
                      className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                        answers[key] === i + 1
                          ? "border-neutral-900 bg-neutral-900 text-white"
                          : "border-neutral-300 bg-white text-neutral-600 hover:bg-neutral-50"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <div className="grid gap-3 sm:grid-cols-2">
              <Select label="Investment Horizon" options={HORIZON_OPTS} value={horizon} onChange={e => setHorizon(e.target.value)} />
              <Select label="Liquidity Need" options={LIQUIDITY_OPTS} value={liquidity} onChange={e => setLiquidity(e.target.value)} />
            </div>
          </div>
        )}

        <Button onClick={generate} loading={generating}>Generate Recommendations</Button>
      </Card>

      {/* Results */}
      {activeRun && o && (
        <div className="space-y-6">
          {/* Warnings */}
          {o.safety_warnings.length > 0 && (
            <Card className="border-amber-200 bg-amber-50">
              <h3 className="text-sm font-semibold text-amber-800 mb-2">Action Required Before Investing</h3>
              <ul className="space-y-1.5">
                {o.safety_warnings.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-700">
                    <span className="mt-0.5">⚠</span> {w}
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {o.needs_profile && (
            <Card className="border-blue-200 bg-blue-50">
              <p className="text-sm text-blue-700">
                No risk profile found. Results use default settings. Fill the questionnaire above for personalized recommendations.
              </p>
            </Card>
          )}

          {/* Summary */}
          <div className="grid gap-4 sm:grid-cols-4">
            <Card>
              <p className="text-xs text-neutral-500 mb-1">Monthly Spending</p>
              <p className="text-xl font-semibold text-neutral-900">{fmt$(o.monthly_spending_avg)}</p>
            </Card>
            <Card>
              <p className="text-xs text-neutral-500 mb-1">Emergency Fund</p>
              <p className="text-xl font-semibold text-neutral-900">{o.emergency_fund_months.toFixed(1)} mo</p>
            </Card>
            <Card>
              <p className="text-xs text-neutral-500 mb-1">Investable/mo</p>
              <p className="text-xl font-semibold text-neutral-900">{fmt$(o.investable_monthly)}</p>
            </Card>
            <Card>
              <p className="text-xs text-neutral-500 mb-1">Risk Bucket</p>
              <p className="text-xl font-semibold text-neutral-900 capitalize">
                {o.risk_bucket?.replace(/_/g, " ") || "N/A"}
              </p>
            </Card>
          </div>

          {/* Action Plan */}
          {activeRun.items.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-neutral-700 mb-3">Action Plan</h3>
              <div className="space-y-3">
                {activeRun.items.map(item => (
                  <Card key={item.id}>
                    <div className="flex items-start gap-3">
                      <span className="text-xl mt-0.5">{ITEM_ICONS[item.type] || "•"}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge color={item.type === "invest" ? "green" : item.type === "stabilize" ? "yellow" : "gray"}>
                            Priority {item.priority}
                          </Badge>
                          <Badge color="blue">{Math.round(item.confidence * 100)}% confidence</Badge>
                        </div>
                        <p className="text-sm font-medium text-neutral-900">{item.title}</p>
                        {item.details?.explanation ? (
                          <p className="text-xs text-neutral-500 mt-1">{String(item.details.explanation)}</p>
                        ) : null}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Allocation */}
          {o.allocation.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-neutral-700 mb-3">Model Portfolio Allocation</h3>
              <Card>
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-neutral-200 text-left text-xs text-neutral-500">
                        <th className="pb-2 pr-4">Asset Class</th>
                        <th className="pb-2 pr-4">Ticker</th>
                        <th className="pb-2 pr-4">Allocation</th>
                        <th className="pb-2">Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {o.allocation.map(a => (
                        <tr key={a.ticker} className="border-b border-neutral-100">
                          <td className="py-2 pr-4 font-medium text-neutral-800">{a.asset}</td>
                          <td className="py-2 pr-4"><Badge color="blue">{a.ticker}</Badge></td>
                          <td className="py-2 pr-4 tabular-nums">{a.pct}%</td>
                          <td className="py-2 text-neutral-500">{a.rationale}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Allocation bar */}
                <div className="mt-4 flex h-3 overflow-hidden rounded-full">
                  {o.allocation.map((a, i) => {
                    const colors = ["bg-blue-500", "bg-emerald-500", "bg-amber-500", "bg-purple-500", "bg-rose-500"];
                    return <div key={a.ticker} className={`${colors[i % colors.length]}`} style={{ width: `${a.pct}%` }} title={`${a.ticker} ${a.pct}%`} />;
                  })}
                </div>
              </Card>
            </div>
          )}

          {/* Projection Chart */}
          {o.projection.length > 1 && (
            <div>
              <h3 className="text-sm font-semibold text-neutral-700 mb-3">
                Growth Projection ({o.projection[o.projection.length - 1]?.month || 0} months)
              </h3>
              <Card>
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={o.projection} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} label={{ value: "Month", position: "insideBottom", offset: -2, fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(value: number | undefined) => value != null ? [`$${value.toLocaleString()}`, ""] : ["", ""]} labelFormatter={(label: unknown) => `Month ${label}`} />
                    <Legend verticalAlign="top" height={30} />
                    <Line type="monotone" dataKey="p90" name="Optimistic (90th)" stroke="#22c55e" strokeDasharray="4 2" dot={false} />
                    <Line type="monotone" dataKey="median" name="Expected (50th)" stroke="#171717" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="p10" name="Conservative (10th)" stroke="#ef4444" strokeDasharray="4 2" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
                <p className="mt-2 text-xs text-neutral-400">
                  Monte Carlo simulation with 500 paths. Returns are modeled as log-normal. Past performance does not guarantee future results.
                </p>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Previous runs list */}
      {!activeRun && !loading && runs.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-700 mb-3">Previous Runs</h3>
          <div className="space-y-2">
            {runs.map(r => (
              <Card key={r.id} onClick={() => loadRun(r.id)} className="cursor-pointer hover:bg-neutral-50 transition-colors">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-neutral-700">{new Date(r.created_at).toLocaleString()}</p>
                  <Badge color={r.status === "completed" ? "green" : "gray"}>{r.status}</Badge>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {!activeRun && !loading && runs.length === 0 && !generating && (
        <EmptyState message="No recommendations yet. Generate your first recommendation above." />
      )}

      {loading && <Spinner />}
    </AppShell>
  );
}
