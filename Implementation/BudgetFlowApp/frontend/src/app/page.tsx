import Link from "next/link";

const features = ["Accounts", "CSV Import", "Rule-based Categorization", "Budgets & Alerts", "Analytics"];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="max-w-lg text-center">
        <h1 className="mb-3 text-4xl font-bold tracking-tight text-neutral-900">BudgetFlow</h1>
        <p className="mb-8 text-lg text-neutral-500">
          Intelligent personal finance management. Track spending, categorize transactions, and stay on budget.
        </p>
        <div className="mb-8 flex flex-wrap justify-center gap-2">
          {features.map((f) => (
            <span key={f} className="inline-flex items-center rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
              {f}
            </span>
          ))}
        </div>
        <div className="flex justify-center gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-neutral-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-neutral-800 transition-colors"
          >
            Login
          </Link>
          <Link
            href="/signup"
            className="rounded-lg border border-neutral-300 px-6 py-2.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50 transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
